"""V4: Test token_id extraction across multiple providers."""

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
N_PROMPTS = 30
MAX_TOKENS = 100
CONCURRENCY = 10
TEMPERATURE = 0.0

# Providers to test
PROVIDERS = [
    "fireworks",
    "together",
    "groq",
    # "lepton",  # May not support logprobs
]


async def generate_and_inspect(
    client: AsyncOpenAI,
    tokenizer,
    conversations: list[list[dict]],
    model: str,
    provider: str,
    max_tokens: int = 100,
) -> tuple[list[dict], bool]:
    """Generate and check if token_ids are available in logprobs."""
    semaphore = asyncio.Semaphore(CONCURRENCY)
    has_token_ids = True

    async def generate_one(messages: list[dict]) -> dict:
        nonlocal has_token_ids
        async with semaphore:
            rendered = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False)

            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=TEMPERATURE,
                    logprobs=True,
                    top_logprobs=1,
                    extra_body={"provider": {"only": [provider]}},
                )
            except Exception as e:
                return {
                    "prompt_token_ids": prompt_token_ids,
                    "content": "",
                    "logprobs": None,
                    "error": str(e),
                }

            content = response.choices[0].message.content or ""
            logprobs = response.choices[0].logprobs

            # Check if token_id is available
            if logprobs and hasattr(logprobs, "content") and logprobs.content:
                first = logprobs.content[0]
                if not hasattr(first, "token_id") or first.token_id is None:
                    has_token_ids = False

            return {
                "prompt_token_ids": prompt_token_ids,
                "content": content,
                "logprobs": logprobs,
                "error": None,
            }

    tasks = [generate_one(conv) for conv in conversations]
    results = []
    for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc=f"{provider}"):
        results.append(await coro)

    return results, has_token_ids


def extract_token_ids(logprobs_content, tokenizer, content: str, filter_eos: bool = True) -> list[int]:
    """Extract token IDs from logprobs, filtering EOS if needed."""
    if logprobs_content is None or not hasattr(logprobs_content, "content"):
        return tokenizer.encode(content, add_special_tokens=False)

    token_ids = []
    eos_id = tokenizer.eos_token_id

    for item in logprobs_content.content:
        if hasattr(item, "token_id") and item.token_id is not None:
            tid = item.token_id
            # Optionally filter EOS
            if filter_eos and tid == eos_id:
                continue
            token_ids.append(tid)
        else:
            # Fallback
            encoded = tokenizer.encode(item.token, add_special_tokens=False)
            token_ids.extend(encoded)

    return token_ids


def tokenize_baseline(prompt_token_ids: list[int], content: str, tokenizer) -> list[int]:
    """Baseline tokenization."""
    prompt_text = tokenizer.decode(prompt_token_ids, skip_special_tokens=False)
    full_text = prompt_text + content
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)
    return full_tokens[len(prompt_token_ids):]


async def run_provider_comparison():
    openrouter_client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    fireworks_client = AsyncOpenAI(
        api_key=os.environ["FIREWORKS_API_KEY"],
        base_url="https://api.fireworks.ai/inference/v1",
    )

    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
    openrouter_model = get_openrouter_name(HF_MODEL)
    fireworks_model = FIREWORKS_MODEL_REGISTRY[HF_MODEL]

    conversations = construct_prompts(n_prompts=N_PROMPTS, model_name=HF_MODEL)

    print(f"Model: {HF_MODEL}")
    print(f"Testing {len(conversations)} prompts across providers")
    print(f"EOS token ID: {tokenizer.eos_token_id}")
    print()

    all_results = []

    for provider in PROVIDERS:
        print(f"\n{'='*60}")
        print(f"Provider: {provider}")
        print(f"{'='*60}")

        try:
            results, has_token_ids = await generate_and_inspect(
                client=openrouter_client,
                tokenizer=tokenizer,
                conversations=conversations,
                model=openrouter_model,
                provider=provider,
                max_tokens=MAX_TOKENS,
            )
        except Exception as e:
            print(f"  Error: {e}")
            continue

        # Check for errors
        errors = [r for r in results if r["error"]]
        if errors:
            print(f"  {len(errors)} requests failed")
            results = [r for r in results if not r["error"]]

        if not results:
            print("  No successful results")
            continue

        print(f"  Has token_id in logprobs: {has_token_ids}")

        # Inspect first result
        first = results[0]
        if first["logprobs"] and hasattr(first["logprobs"], "content") and first["logprobs"].content:
            lp = first["logprobs"].content[0]
            print(f"  First logprob item: token='{lp.token}'", end="")
            if hasattr(lp, "token_id"):
                print(f", token_id={lp.token_id}", end="")
            if hasattr(lp, "bytes"):
                print(f", bytes={lp.bytes[:5]}...", end="")
            print()

        # Create outputs using both strategies
        outputs_logprobs = []
        outputs_baseline = []

        for r in results:
            prompt_ids = r["prompt_token_ids"]
            content = r["content"]
            logprobs = r["logprobs"]

            # Logprobs strategy
            lp_tokens = extract_token_ids(logprobs, tokenizer, content, filter_eos=True)
            outputs_logprobs.append(TokenSequence(prompt_token_ids=prompt_ids, output_token_ids=lp_tokens))

            # Baseline strategy
            base_tokens = tokenize_baseline(prompt_ids, content, tokenizer)
            outputs_baseline.append(TokenSequence(prompt_token_ids=prompt_ids, output_token_ids=base_tokens))

        # Verify both
        for name, outputs in [("Logprobs", outputs_logprobs), ("Baseline", outputs_baseline)]:
            total = sum(len(o.output_token_ids) for o in outputs)
            if total == 0:
                print(f"  {name}: No tokens")
                continue

            metrics = await verify_outputs_fireworks(
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

            summary = compute_metrics_summary(metrics)
            print(f"  {name}: {summary['exact_match_rate']:.2%} ({summary['total_tokens']} tokens)")

            all_results.append({
                "provider": provider,
                "strategy": name,
                "exact_match": summary["exact_match_rate"],
                "tokens": summary["total_tokens"],
            })

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in sorted(all_results, key=lambda x: (x["provider"], x["strategy"])):
        print(f"{r['provider']:12} | {r['strategy']:10} | {r['exact_match']:.2%} ({r['tokens']} tokens)")


if __name__ == "__main__":
    asyncio.run(run_provider_comparison())
