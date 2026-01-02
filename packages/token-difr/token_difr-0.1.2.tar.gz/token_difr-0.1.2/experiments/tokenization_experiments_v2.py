"""V2: Try getting logprobs from chat completions and matching token strings."""

import asyncio
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm as atqdm
from transformers import AutoTokenizer

from token_difr import (
    FIREWORKS_MODEL_REGISTRY,
    TokenSequence,
    compute_metrics_summary,
    construct_prompts,
    get_openrouter_name,
    verify_outputs_fireworks,
)

load_dotenv()

# Test configuration
HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
N_PROMPTS = 20
MAX_TOKENS = 100
CONCURRENCY = 10
TEMPERATURE = 0.0


def find_token_id_for_string(tokenizer, token_str: str, vocab: dict | None = None) -> int | None:
    """Try to find the token ID for a given token string."""
    if vocab is None:
        vocab = tokenizer.get_vocab()

    # Direct lookup
    if token_str in vocab:
        return vocab[token_str]

    # Try with leading space variations
    variations = [
        token_str,
        " " + token_str,
        token_str.lstrip(),
        "Ġ" + token_str,  # GPT-2 style space prefix
        "▁" + token_str,  # SentencePiece style
    ]

    for var in variations:
        if var in vocab:
            return vocab[var]

    # Try encoding the token string
    encoded = tokenizer.encode(token_str, add_special_tokens=False)
    if len(encoded) == 1:
        return encoded[0]

    return None


async def generate_with_chat_logprobs(
    client: AsyncOpenAI,
    tokenizer,
    conversations: list[list[dict]],
    model: str,
    provider: str,
    max_tokens: int = 100,
    concurrency: int = 10,
) -> tuple[list[TokenSequence], list[dict]]:
    """Generate using chat completions with logprobs=True."""
    semaphore = asyncio.Semaphore(concurrency)
    vocab = tokenizer.get_vocab()

    async def generate_one(messages: list[dict]) -> tuple[TokenSequence, dict]:
        async with semaphore:
            # Apply chat template locally
            rendered = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False)

            # Use chat completions with logprobs
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=TEMPERATURE,
                logprobs=True,
                top_logprobs=5,
                extra_body={"provider": {"only": [provider]}},
            )

            content = response.choices[0].message.content or ""
            logprobs_content = response.choices[0].logprobs

            metadata = {
                "content": content,
                "logprobs": logprobs_content,
            }

            return prompt_token_ids, content, logprobs_content, metadata

    tasks = [generate_one(conv) for conv in conversations]
    raw_results = []
    for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating"):
        raw_results.append(await coro)

    return raw_results, vocab


def strategy_chat_logprobs_tokens(
    tokenizer, prompt_ids: list[int], content: str, logprobs_content, vocab: dict
) -> list[int]:
    """Use token strings from chat logprobs to find token IDs."""
    if logprobs_content is None or not hasattr(logprobs_content, "content"):
        # Fallback
        return tokenizer.encode(content, add_special_tokens=False)

    token_ids = []
    for item in logprobs_content.content:
        token_str = item.token

        # Try to find the token ID
        token_id = find_token_id_for_string(tokenizer, token_str, vocab)

        if token_id is not None:
            token_ids.append(token_id)
        else:
            # Fallback: encode the token string
            encoded = tokenizer.encode(token_str, add_special_tokens=False)
            token_ids.extend(encoded)

    return token_ids


def strategy_chat_logprobs_bytes(
    tokenizer, prompt_ids: list[int], content: str, logprobs_content, vocab: dict
) -> list[int]:
    """Use bytes from chat logprobs if available."""
    if logprobs_content is None or not hasattr(logprobs_content, "content"):
        return tokenizer.encode(content, add_special_tokens=False)

    token_ids = []
    for item in logprobs_content.content:
        # Some APIs return bytes in logprobs
        if hasattr(item, "bytes") and item.bytes:
            # Convert bytes to string and find token
            try:
                byte_str = bytes(item.bytes).decode("utf-8")
                token_id = find_token_id_for_string(tokenizer, byte_str, vocab)
                if token_id is not None:
                    token_ids.append(token_id)
                    continue
            except:
                pass

        # Fallback to token string
        token_str = item.token
        token_id = find_token_id_for_string(tokenizer, token_str, vocab)
        if token_id is not None:
            token_ids.append(token_id)
        else:
            encoded = tokenizer.encode(token_str, add_special_tokens=False)
            token_ids.extend(encoded)

    return token_ids


def strategy_reconstruct_from_token_strings(
    tokenizer, prompt_ids: list[int], content: str, logprobs_content, vocab: dict
) -> list[int]:
    """Reconstruct by joining token strings and re-encoding at boundaries."""
    if logprobs_content is None or not hasattr(logprobs_content, "content"):
        return tokenizer.encode(content, add_special_tokens=False)

    # Get all token strings
    token_strings = [item.token for item in logprobs_content.content]

    # Join them to get the full text
    joined = "".join(token_strings)

    # Now encode the joined text
    # This might differ from the original but should be more consistent
    return tokenizer.encode(joined, add_special_tokens=False)


def strategy_greedy_token_match(
    tokenizer, prompt_ids: list[int], content: str, logprobs_content, vocab: dict
) -> list[int]:
    """Greedily match token strings to vocab entries."""
    if logprobs_content is None or not hasattr(logprobs_content, "content"):
        return tokenizer.encode(content, add_special_tokens=False)

    inv_vocab = {v: k for k, v in vocab.items()}
    token_ids = []

    for item in logprobs_content.content:
        token_str = item.token
        found = False

        # Try exact match in vocab
        for tok_id, tok_text in inv_vocab.items():
            # Normalize and compare
            if tokenizer.decode([tok_id], skip_special_tokens=False) == token_str:
                token_ids.append(tok_id)
                found = True
                break

        if not found:
            # Fallback: encode
            encoded = tokenizer.encode(token_str, add_special_tokens=False)
            token_ids.extend(encoded)

    return token_ids


def strategy_full_sequence_encode(
    tokenizer, prompt_ids: list[int], content: str, logprobs_content, vocab: dict
) -> list[int]:
    """Encode full prompt+content and slice (reference for comparison)."""
    prompt_text = tokenizer.decode(prompt_ids, skip_special_tokens=False)
    full_text = prompt_text + content
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)
    return full_tokens[len(prompt_ids):]


async def run_experiments():
    # Setup clients
    openrouter_client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    fireworks_client = AsyncOpenAI(
        api_key=os.environ["FIREWORKS_API_KEY"],
        base_url="https://api.fireworks.ai/inference/v1",
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
    vocab = tokenizer.get_vocab()

    # Get model names
    openrouter_model = get_openrouter_name(HF_MODEL)
    fireworks_model = FIREWORKS_MODEL_REGISTRY[HF_MODEL]
    provider = "fireworks"

    print(f"Model: {HF_MODEL}")
    print(f"OpenRouter: {openrouter_model}")
    print(f"Fireworks: {fireworks_model}")

    # Construct prompts
    conversations = construct_prompts(n_prompts=N_PROMPTS, model_name=HF_MODEL)
    print(f"Loaded {len(conversations)} prompts")

    # Generate with chat logprobs
    print("\nGenerating with chat completions + logprobs...")
    raw_results, vocab = await generate_with_chat_logprobs(
        client=openrouter_client,
        tokenizer=tokenizer,
        conversations=conversations,
        model=openrouter_model,
        provider=provider,
        max_tokens=MAX_TOKENS,
        concurrency=CONCURRENCY,
    )

    # Print sample logprobs structure
    if raw_results:
        sample = raw_results[0]
        prompt_ids, content, logprobs_content, metadata = sample
        print(f"\nSample content: {content[:100]}...")
        if logprobs_content and hasattr(logprobs_content, "content"):
            print(f"Logprobs entries: {len(logprobs_content.content)}")
            if logprobs_content.content:
                first = logprobs_content.content[0]
                print(f"First entry: token='{first.token}', logprob={first.logprob:.4f}")
                if hasattr(first, "bytes"):
                    print(f"  bytes={first.bytes}")
                if hasattr(first, "top_logprobs") and first.top_logprobs:
                    print(f"  top_logprobs[0]: {first.top_logprobs[0]}")

    # Define strategies
    strategies = [
        ("1. Chat logprobs tokens", strategy_chat_logprobs_tokens),
        ("2. Chat logprobs bytes", strategy_chat_logprobs_bytes),
        ("3. Reconstruct from strings", strategy_reconstruct_from_token_strings),
        ("4. Greedy token match", strategy_greedy_token_match),
        ("5. Full sequence encode (baseline)", strategy_full_sequence_encode),
    ]

    results_summary = []

    for name, strategy_fn in strategies:
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")

        outputs = []
        for prompt_ids, content, logprobs_content, metadata in raw_results:
            try:
                output_ids = strategy_fn(tokenizer, prompt_ids, content, logprobs_content, vocab)
                outputs.append(TokenSequence(
                    prompt_token_ids=prompt_ids,
                    output_token_ids=output_ids,
                ))
            except Exception as e:
                print(f"  Error: {e}")
                # Fallback
                output_ids = tokenizer.encode(content, add_special_tokens=False)
                outputs.append(TokenSequence(
                    prompt_token_ids=prompt_ids,
                    output_token_ids=output_ids,
                ))

        # Debug: show sample
        if outputs:
            sample_out = outputs[0]
            print(f"Sample output tokens: {len(sample_out.output_token_ids)}")
            decoded = tokenizer.decode(sample_out.output_token_ids, skip_special_tokens=False)
            print(f"Decoded: {decoded[:100]}...")

        total_tokens = sum(len(o.output_token_ids) for o in outputs)
        if total_tokens == 0:
            print("No tokens generated!")
            continue

        # Verify
        results = await verify_outputs_fireworks(
            outputs,
            vocab_size=len(tokenizer),
            temperature=TEMPERATURE,
            top_k=50,
            top_p=0.95,
            seed=42,
            client=fireworks_client,
            model=fireworks_model,
            topk_logprobs=5,
            concurrency=CONCURRENCY,
        )

        summary = compute_metrics_summary(results)
        print(f"Result: {summary['exact_match_rate']:.2%} ({summary['total_tokens']} tokens)")

        results_summary.append((name, summary["exact_match_rate"], summary["total_tokens"]))

    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY (Chat Completions with Logprobs)")
    print("=" * 60)
    results_summary.sort(key=lambda x: x[1], reverse=True)
    for name, rate, tokens in results_summary:
        print(f"{name}: {rate:.2%} ({tokens} tokens)")


if __name__ == "__main__":
    asyncio.run(run_experiments())
