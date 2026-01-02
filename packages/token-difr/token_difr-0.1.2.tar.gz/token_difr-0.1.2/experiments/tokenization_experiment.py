"""Experiment: Compare chat.completions vs completions endpoint tokenization."""

import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from transformers import AutoTokenizer
from tqdm.asyncio import tqdm as atqdm

from token_difr import (
    FIREWORKS_MODEL_REGISTRY,
    TokenSequence,
    compute_metrics_summary,
    construct_prompts,
    get_openrouter_name,
    verify_outputs_fireworks,
)
from token_difr.openrouter_api import generate_openrouter_responses, tokenize_openrouter_responses

load_dotenv()

# Config
HF_MODEL = "Qwen/Qwen3-235B-A22B-Instruct-2507"
OPENROUTER_MODEL = get_openrouter_name(HF_MODEL)
FIREWORKS_MODEL = FIREWORKS_MODEL_REGISTRY[HF_MODEL]
PROVIDERS = ["together", "cerebras"]  # Skip parasail (18 rpm limit)
N_PROMPTS = 30
MAX_TOKENS = 100
TEMPERATURE = 0.0
CONCURRENCY = 3  # Low to avoid rate limits


async def generate_completions_variant(
    client: AsyncOpenAI,
    tokenizer,
    conversations: list[list[dict[str, str]]],
    model: str,
    provider: str,
    add_special_tokens_output: bool,
    strip_whitespace: bool = False,
    max_tokens: int = 100,
) -> list[TokenSequence]:
    """Generate using completions endpoint with configurable tokenization."""
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def generate_one(messages: list[dict[str, str]]) -> TokenSequence:
        async with semaphore:
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False, return_tensors=None)

            response = await client.completions.create(
                model=model,
                prompt=rendered,
                max_tokens=max_tokens,
                temperature=TEMPERATURE,
                extra_body={"provider": {"only": [provider]}},
            )

            generated_text = response.choices[0].text
            if strip_whitespace:
                generated_text = generated_text.strip()
            generated_token_ids = tokenizer.encode(
                generated_text, add_special_tokens=add_special_tokens_output, return_tensors=None
            )

            return TokenSequence(
                prompt_token_ids=prompt_token_ids,
                output_token_ids=generated_token_ids,
            )

    tasks = [generate_one(conv) for conv in conversations]
    outputs = []
    for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Completions"):
        outputs.append(await coro)
    return outputs


async def verify_and_report(outputs: list[TokenSequence], fireworks_client: AsyncOpenAI, vocab_size: int, label: str):
    """Verify outputs and print results."""
    results = await verify_outputs_fireworks(
        outputs,
        vocab_size=vocab_size,
        temperature=TEMPERATURE,
        top_k=50,
        top_p=0.95,
        seed=42,
        client=fireworks_client,
        model=FIREWORKS_MODEL,
        topk_logprobs=5,
        concurrency=CONCURRENCY,
    )
    summary = compute_metrics_summary(results)
    print(f"{label}: {summary['exact_match_rate']:.2%} ({summary['total_tokens']} tokens)")

    # Analyze where mismatches occur
    first_token_mismatches = 0
    total_seqs = len(results)
    mismatch_positions = []
    for seq_results in results:
        for pos, metrics in enumerate(seq_results):
            if not metrics.exact_match:
                mismatch_positions.append(pos)
                if pos == 0:
                    first_token_mismatches += 1
    if mismatch_positions:
        avg_pos = sum(mismatch_positions) / len(mismatch_positions)
        print(f"  -> First token mismatches: {first_token_mismatches}/{total_seqs} seqs ({100*first_token_mismatches/total_seqs:.1f}%)")
        print(f"  -> Avg mismatch position: {avg_pos:.1f}")

    return summary, results


async def main():
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    fireworks_key = os.environ.get("FIREWORKS_API_KEY")

    openrouter_client = AsyncOpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
    fireworks_client = AsyncOpenAI(api_key=fireworks_key, base_url="https://api.fireworks.ai/inference/v1")

    print(f"Loading tokenizer for {HF_MODEL}...")
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
    vocab_size = len(tokenizer)

    conversations = construct_prompts(n_prompts=N_PROMPTS, model_name=HF_MODEL)
    print(f"Testing with {N_PROMPTS} prompts, providers={PROVIDERS}\n")

    summaries = {}

    for provider in PROVIDERS:
        print(f"\n{'#' * 60}")
        print(f"# PROVIDER: {provider}")
        print(f"{'#' * 60}")

        # Test 1: Chat completions endpoint
        print("\n" + "=" * 60)
        print(f"TEST: chat.completions ({provider})")
        print("=" * 60)
        responses = await generate_openrouter_responses(
            client=openrouter_client,
            conversations=conversations,
            model=OPENROUTER_MODEL,
            provider=provider,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            concurrency=CONCURRENCY,
        )
        outputs_chat = tokenize_openrouter_responses(conversations, responses, tokenizer, MAX_TOKENS)
        summaries[f"chat.completions ({provider})"], _ = await verify_and_report(
            outputs_chat, fireworks_client, vocab_size, f"chat.completions ({provider})"
        )

        # Test 2: Completions endpoint (no special tokens)
        print("\n" + "=" * 60)
        print(f"TEST: completions ({provider})")
        print("=" * 60)
        outputs_comp = await generate_completions_variant(
            client=openrouter_client,
            tokenizer=tokenizer,
            conversations=conversations,
            model=OPENROUTER_MODEL,
            provider=provider,
            add_special_tokens_output=False,
            strip_whitespace=False,
            max_tokens=MAX_TOKENS,
        )
        summaries[f"completions ({provider})"], _ = await verify_and_report(
            outputs_comp, fireworks_client, vocab_size, f"completions ({provider})"
        )

        # Test 3: Completions endpoint with strip
        print("\n" + "=" * 60)
        print(f"TEST: completions+strip ({provider})")
        print("=" * 60)
        outputs_strip = await generate_completions_variant(
            client=openrouter_client,
            tokenizer=tokenizer,
            conversations=conversations,
            model=OPENROUTER_MODEL,
            provider=provider,
            add_special_tokens_output=False,
            strip_whitespace=True,
            max_tokens=MAX_TOKENS,
        )
        summaries[f"completions+strip ({provider})"], _ = await verify_and_report(
            outputs_strip, fireworks_client, vocab_size, f"completions+strip ({provider})"
        )

    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    for name, summary in summaries.items():
        print(f"  {name}: {summary['exact_match_rate']:.2%}")


if __name__ == "__main__":
    asyncio.run(main())
