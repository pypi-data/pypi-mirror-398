"""Experiments to improve tokenization matching for OpenRouter completions."""

import asyncio
import os
from dataclasses import dataclass
from typing import Callable

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
N_PROMPTS = 20  # Small for quick iteration
MAX_TOKENS = 100
CONCURRENCY = 10
TEMPERATURE = 0.0


@dataclass
class ExperimentResult:
    name: str
    exact_match_rate: float
    total_tokens: int
    avg_prob: float


async def generate_with_strategy(
    client: AsyncOpenAI,
    tokenizer,
    conversations: list[list[dict]],
    model: str,
    provider: str,
    tokenize_fn: Callable,
    max_tokens: int = 100,
    concurrency: int = 10,
    use_logprobs: bool = False,
) -> list[TokenSequence]:
    """Generate using OpenRouter completions with a custom tokenization strategy."""
    semaphore = asyncio.Semaphore(concurrency)

    async def generate_one(messages: list[dict]) -> tuple[TokenSequence, dict]:
        async with semaphore:
            # Apply chat template locally
            rendered = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False)

            # Build request
            extra_body = {"provider": {"only": [provider]}}

            response = await client.completions.create(
                model=model,
                prompt=rendered,
                max_tokens=max_tokens,
                temperature=TEMPERATURE,
                logprobs=5 if use_logprobs else None,
                extra_body=extra_body,
            )

            generated_text = response.choices[0].text
            logprobs_data = response.choices[0].logprobs if use_logprobs else None

            # Use the custom tokenization function
            output_token_ids = tokenize_fn(
                tokenizer, rendered, generated_text, logprobs_data
            )

            return TokenSequence(
                prompt_token_ids=prompt_token_ids,
                output_token_ids=output_token_ids,
            ), {"text": generated_text, "logprobs": logprobs_data}

    tasks = [generate_one(conv) for conv in conversations]
    results = []
    for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating"):
        results.append(await coro)

    outputs = [r[0] for r in results]
    metadata = [r[1] for r in results]
    return outputs, metadata


# =============================================================================
# TOKENIZATION STRATEGIES
# =============================================================================


def strategy_baseline(tokenizer, prompt: str, response: str, logprobs) -> list[int]:
    """Original baseline: add_special_tokens=True (probably wrong)."""
    return tokenizer.encode(response, add_special_tokens=True)


def strategy_no_special_tokens(tokenizer, prompt: str, response: str, logprobs) -> list[int]:
    """Fix: add_special_tokens=False for response."""
    return tokenizer.encode(response, add_special_tokens=False)


def strategy_full_sequence_slice(tokenizer, prompt: str, response: str, logprobs) -> list[int]:
    """Encode full prompt+response together, then slice off prompt tokens."""
    full_text = prompt + response
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)
    prompt_tokens = tokenizer.encode(prompt, add_special_tokens=False)

    # Slice off the prompt portion
    return full_tokens[len(prompt_tokens):]


def strategy_continuation_encode(tokenizer, prompt: str, response: str, logprobs) -> list[int]:
    """Use tokenizer's encode with the prompt as prefix context.

    Some tokenizers have different behavior when encoding text that continues
    from a specific prefix vs encoding standalone text.
    """
    # Encode with prefix - some tokenizers support this via encode_plus
    # For now, use the full sequence approach but with a slight variation
    full_text = prompt + response
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)

    # Try to find where the response starts by looking at decoded chunks
    prompt_tokens = tokenizer.encode(prompt, add_special_tokens=False)

    # Verify the slicing is correct by decoding
    response_tokens = full_tokens[len(prompt_tokens):]
    decoded_response = tokenizer.decode(response_tokens, skip_special_tokens=False)

    # If there's a mismatch, try adjusting
    if not response.startswith(decoded_response.lstrip()) and len(response_tokens) > 0:
        # Try removing one token from prompt (boundary issue)
        alt_response_tokens = full_tokens[len(prompt_tokens) - 1:]
        alt_decoded = tokenizer.decode(alt_response_tokens, skip_special_tokens=False)
        if response in alt_decoded:
            return alt_response_tokens

    return response_tokens


def strategy_strip_then_encode(tokenizer, prompt: str, response: str, logprobs) -> list[int]:
    """Strip leading whitespace, encode, then check if we need leading space token."""
    stripped = response.lstrip()
    tokens = tokenizer.encode(stripped, add_special_tokens=False)

    # Check if original had leading space
    if response != stripped:
        leading_ws = response[:len(response) - len(stripped)]
        ws_tokens = tokenizer.encode(leading_ws, add_special_tokens=False)
        tokens = ws_tokens + tokens

    return tokens


def strategy_from_logprobs(tokenizer, prompt: str, response: str, logprobs) -> list[int]:
    """If logprobs are available, try to extract tokens from them."""
    if logprobs is None or not hasattr(logprobs, 'tokens'):
        # Fallback to no_special_tokens
        return tokenizer.encode(response, add_special_tokens=False)

    # Try to get token IDs from logprobs
    tokens = logprobs.tokens if hasattr(logprobs, 'tokens') else []

    if hasattr(logprobs, 'token_ids'):
        return list(logprobs.token_ids)

    # If we only have token strings, convert them
    if tokens:
        # This is imperfect but might help
        token_ids = []
        for tok_str in tokens:
            # Try to find the token ID
            encoded = tokenizer.encode(tok_str, add_special_tokens=False)
            if len(encoded) == 1:
                token_ids.append(encoded[0])
            else:
                # Multi-token - just use the first
                token_ids.extend(encoded)
        return token_ids

    return tokenizer.encode(response, add_special_tokens=False)


def strategy_byte_level_align(tokenizer, prompt: str, response: str, logprobs) -> list[int]:
    """Try to align at byte level for BPE tokenizers."""
    # Encode full sequence
    full_text = prompt + response
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)

    # Find the byte offset where response starts
    prompt_bytes = prompt.encode('utf-8')

    # Decode tokens one by one to find the boundary
    current_bytes = b""
    response_start_idx = 0

    for i, tok_id in enumerate(full_tokens):
        tok_str = tokenizer.decode([tok_id], skip_special_tokens=False)
        current_bytes += tok_str.encode('utf-8')
        if len(current_bytes) >= len(prompt_bytes):
            response_start_idx = i + 1
            break

    return full_tokens[response_start_idx:]


async def run_experiment(
    name: str,
    strategy_fn: Callable,
    openrouter_client: AsyncOpenAI,
    fireworks_client: AsyncOpenAI,
    tokenizer,
    conversations: list[list[dict]],
    openrouter_model: str,
    fireworks_model: str,
    provider: str,
    use_logprobs: bool = False,
) -> ExperimentResult:
    """Run a single tokenization experiment."""
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")

    outputs, metadata = await generate_with_strategy(
        client=openrouter_client,
        tokenizer=tokenizer,
        conversations=conversations,
        model=openrouter_model,
        provider=provider,
        tokenize_fn=strategy_fn,
        max_tokens=MAX_TOKENS,
        concurrency=CONCURRENCY,
        use_logprobs=use_logprobs,
    )

    # Print some debug info
    if outputs:
        sample = outputs[0]
        sample_meta = metadata[0]
        print(f"Sample prompt tokens: {len(sample.prompt_token_ids)}")
        print(f"Sample output tokens: {len(sample.output_token_ids)}")
        print(f"Sample text: {sample_meta['text'][:100]}...")
        decoded = tokenizer.decode(sample.output_token_ids, skip_special_tokens=False)
        print(f"Decoded tokens: {decoded[:100]}...")

    total_tokens = sum(len(o.output_token_ids) for o in outputs)
    if total_tokens == 0:
        return ExperimentResult(name=name, exact_match_rate=0.0, total_tokens=0, avg_prob=0.0)

    vocab_size = len(tokenizer)
    results = await verify_outputs_fireworks(
        outputs,
        vocab_size=vocab_size,
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
    print(f"Result: {summary['exact_match_rate']:.2%} exact match ({summary['total_tokens']} tokens)")

    return ExperimentResult(
        name=name,
        exact_match_rate=summary["exact_match_rate"],
        total_tokens=summary["total_tokens"],
        avg_prob=summary["avg_prob"],
    )


async def main():
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

    # Get model names
    openrouter_model = get_openrouter_name(HF_MODEL)
    fireworks_model = FIREWORKS_MODEL_REGISTRY[HF_MODEL]
    provider = "fireworks"  # Using fireworks as provider for consistency

    print(f"HuggingFace model: {HF_MODEL}")
    print(f"OpenRouter model: {openrouter_model}")
    print(f"Fireworks model: {fireworks_model}")
    print(f"Provider: {provider}")

    # Construct prompts
    conversations = construct_prompts(n_prompts=N_PROMPTS, model_name=HF_MODEL)
    print(f"Loaded {len(conversations)} prompts")

    # Define experiments
    experiments = [
        ("1. Baseline (add_special_tokens=True)", strategy_baseline, False),
        ("2. No special tokens", strategy_no_special_tokens, False),
        ("3. Full sequence slice", strategy_full_sequence_slice, False),
        ("4. Continuation encode", strategy_continuation_encode, False),
        ("5. Strip then encode", strategy_strip_then_encode, False),
        ("6. Byte-level align", strategy_byte_level_align, False),
        ("7. From logprobs", strategy_from_logprobs, True),
    ]

    results = []
    for name, strategy_fn, use_logprobs in experiments:
        try:
            result = await run_experiment(
                name=name,
                strategy_fn=strategy_fn,
                openrouter_client=openrouter_client,
                fireworks_client=fireworks_client,
                tokenizer=tokenizer,
                conversations=conversations,
                openrouter_model=openrouter_model,
                fireworks_model=fireworks_model,
                provider=provider,
                use_logprobs=use_logprobs,
            )
            results.append(result)
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    results.sort(key=lambda x: x.exact_match_rate, reverse=True)
    for r in results:
        print(f"{r.name}: {r.exact_match_rate:.2%} ({r.total_tokens} tokens, avg_prob={r.avg_prob:.4f})")


if __name__ == "__main__":
    asyncio.run(main())
