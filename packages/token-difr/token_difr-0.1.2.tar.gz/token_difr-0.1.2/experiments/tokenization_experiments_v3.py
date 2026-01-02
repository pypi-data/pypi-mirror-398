"""V3: Use token_id directly from OpenRouter chat logprobs."""

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
N_PROMPTS = 50  # More prompts for better statistics
MAX_TOKENS = 150
CONCURRENCY = 10
TEMPERATURE = 0.0


async def generate_with_chat_logprobs(
    client: AsyncOpenAI,
    tokenizer,
    conversations: list[list[dict]],
    model: str,
    provider: str,
    max_tokens: int = 100,
    concurrency: int = 10,
) -> list[dict]:
    """Generate using chat completions with logprobs=True."""
    semaphore = asyncio.Semaphore(concurrency)

    async def generate_one(messages: list[dict]) -> dict:
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
                top_logprobs=1,  # Just need 1 to get the token_id
                extra_body={"provider": {"only": [provider]}},
            )

            content = response.choices[0].message.content or ""
            logprobs_content = response.choices[0].logprobs

            return {
                "prompt_token_ids": prompt_token_ids,
                "content": content,
                "logprobs": logprobs_content,
            }

    tasks = [generate_one(conv) for conv in conversations]
    results = []
    for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating"):
        results.append(await coro)
    return results


def extract_token_ids_from_logprobs(logprobs_content, tokenizer, content: str) -> list[int]:
    """Extract token IDs directly from logprobs if available."""
    if logprobs_content is None or not hasattr(logprobs_content, "content"):
        print("  No logprobs content!")
        return tokenizer.encode(content, add_special_tokens=False)

    token_ids = []
    missing_count = 0

    for item in logprobs_content.content:
        # Check if token_id is directly available on the item
        if hasattr(item, "token_id") and item.token_id is not None:
            token_ids.append(item.token_id)
            continue

        # Check top_logprobs for token_id
        if hasattr(item, "top_logprobs") and item.top_logprobs:
            # Find the entry matching the actual token
            for top_item in item.top_logprobs:
                if hasattr(top_item, "token_id") and top_item.token_id is not None:
                    # This should be the selected token
                    if top_item.token == item.token:
                        token_ids.append(top_item.token_id)
                        break
            else:
                # Didn't find matching token, use first one (highest prob)
                if hasattr(item.top_logprobs[0], "token_id"):
                    token_ids.append(item.top_logprobs[0].token_id)
                else:
                    missing_count += 1
                    # Fallback: encode the token string
                    encoded = tokenizer.encode(item.token, add_special_tokens=False)
                    token_ids.extend(encoded)
        else:
            missing_count += 1
            encoded = tokenizer.encode(item.token, add_special_tokens=False)
            token_ids.extend(encoded)

    if missing_count > 0:
        print(f"  Warning: {missing_count} tokens missing token_id")

    return token_ids


def tokenize_full_sequence(prompt_token_ids: list[int], content: str, tokenizer) -> list[int]:
    """Baseline: encode full sequence and slice."""
    prompt_text = tokenizer.decode(prompt_token_ids, skip_special_tokens=False)
    full_text = prompt_text + content
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)
    return full_tokens[len(prompt_token_ids):]


async def run_comparison():
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
    provider = "fireworks"

    print(f"Model: {HF_MODEL}")
    print(f"Testing with {N_PROMPTS} prompts, {MAX_TOKENS} max tokens")
    print()

    # Construct prompts
    conversations = construct_prompts(n_prompts=N_PROMPTS, model_name=HF_MODEL)

    # Generate
    results = await generate_with_chat_logprobs(
        client=openrouter_client,
        tokenizer=tokenizer,
        conversations=conversations,
        model=openrouter_model,
        provider=provider,
        max_tokens=MAX_TOKENS,
        concurrency=CONCURRENCY,
    )

    # Inspect first result's logprobs structure
    print("\n--- Logprobs structure inspection ---")
    if results and results[0]["logprobs"]:
        lp = results[0]["logprobs"]
        if hasattr(lp, "content") and lp.content:
            first_item = lp.content[0]
            print(f"First logprobs item type: {type(first_item)}")
            print(f"First logprobs item attributes: {dir(first_item)}")
            print(f"First item: {first_item}")
            if hasattr(first_item, "top_logprobs") and first_item.top_logprobs:
                top_first = first_item.top_logprobs[0]
                print(f"Top logprobs[0] type: {type(top_first)}")
                print(f"Top logprobs[0] attributes: {dir(top_first)}")
                print(f"Top logprobs[0]: {top_first}")

    # Strategy 1: Extract token_ids from logprobs
    print("\n--- Strategy: Extract token_ids from logprobs ---")
    outputs_logprobs = []
    for r in results:
        token_ids = extract_token_ids_from_logprobs(
            r["logprobs"], tokenizer, r["content"]
        )
        outputs_logprobs.append(TokenSequence(
            prompt_token_ids=r["prompt_token_ids"],
            output_token_ids=token_ids,
        ))

    # Strategy 2: Full sequence encode (baseline)
    print("\n--- Strategy: Full sequence encode (baseline) ---")
    outputs_baseline = []
    for r in results:
        token_ids = tokenize_full_sequence(
            r["prompt_token_ids"], r["content"], tokenizer
        )
        outputs_baseline.append(TokenSequence(
            prompt_token_ids=r["prompt_token_ids"],
            output_token_ids=token_ids,
        ))

    # Compare sample
    print("\n--- Sample comparison ---")
    sample_r = results[0]
    lp_tokens = outputs_logprobs[0].output_token_ids
    base_tokens = outputs_baseline[0].output_token_ids

    print(f"Logprobs tokens: {len(lp_tokens)}")
    print(f"Baseline tokens: {len(base_tokens)}")
    print(f"First 10 logprobs tokens: {lp_tokens[:10]}")
    print(f"First 10 baseline tokens: {base_tokens[:10]}")
    print(f"Match: {lp_tokens == base_tokens}")

    # Decode both
    lp_decoded = tokenizer.decode(lp_tokens, skip_special_tokens=False)
    base_decoded = tokenizer.decode(base_tokens, skip_special_tokens=False)
    print(f"Logprobs decoded: {lp_decoded[:100]}...")
    print(f"Baseline decoded: {base_decoded[:100]}...")

    # Verify both
    print("\n--- Verification ---")

    for name, outputs in [
        ("Logprobs token_ids", outputs_logprobs),
        ("Baseline (full sequence)", outputs_baseline),
    ]:
        print(f"\n{name}:")
        total_tokens = sum(len(o.output_token_ids) for o in outputs)

        results_metrics = await verify_outputs_fireworks(
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

        summary = compute_metrics_summary(results_metrics)
        print(f"  Exact match: {summary['exact_match_rate']:.2%}")
        print(f"  Avg prob: {summary['avg_prob']:.4f}")
        print(f"  Total tokens: {summary['total_tokens']}")


if __name__ == "__main__":
    asyncio.run(run_comparison())
