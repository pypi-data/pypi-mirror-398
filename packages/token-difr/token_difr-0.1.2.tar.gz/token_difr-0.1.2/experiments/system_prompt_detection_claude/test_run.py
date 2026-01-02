"""Quick test run with minimal experiments."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import openai
import tinker
from transformers import AutoTokenizer
from tqdm import tqdm

from token_difr import (
    TokenSequence,
    compute_metrics_summary,
    construct_prompts,
    encode_thinking_response,
    verify_outputs_tinker,
)

# Model configuration
MODEL_NAME = "Qwen/Qwen3-235B-A22B-Instruct-2507"
OPENROUTER_MODEL_NAME = "qwen/qwen3-235b-a22b-2507"
PROVIDER = "wandb/bf16"

# Minimal test config
N_PROMPTS = 10
MAX_TOKENS = 100
MAX_CTX_LEN = 512

OUTPUT_DIR = Path(__file__).parent


async def openrouter_request(client, model, messages, max_tokens, temperature, provider):
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        extra_body={"provider": {"order": [provider]}},
    )
    content = completion.choices[0].message.content or ""
    reasoning = getattr(completion.choices[0].message, "reasoning", None) or ""
    return content, reasoning


async def generate_all(client, model, conversations, max_tokens, temperature, provider, concurrency=8):
    semaphore = asyncio.Semaphore(concurrency)

    async def _wrapped(idx, messages):
        async with semaphore:
            content, reasoning = await openrouter_request(client, model, messages, max_tokens, temperature, provider)
            return idx, content, reasoning

    tasks = [asyncio.create_task(_wrapped(i, conv)) for i, conv in enumerate(conversations)]
    results = [("", "")] * len(conversations)

    for fut in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=f"OpenRouter ({provider})"):
        idx, content, reasoning = await fut
        results[idx] = (content, reasoning)

    return results


def create_token_sequences(conversations, responses, tokenizer, max_tokens=None):
    sequences = []
    for conversation, (content, reasoning) in zip(conversations, responses):
        rendered = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
        prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False)
        response_token_ids = encode_thinking_response(content, reasoning, tokenizer, max_tokens)
        sequences.append(TokenSequence(prompt_token_ids=prompt_token_ids, output_token_ids=response_token_ids))
    return sequences


def add_system_prompt(conversations, system_prompt):
    return [[{"role": "system", "content": system_prompt}] + conv for conv in conversations]


async def run_single_experiment(
    experiment_name, generation_prompt, verification_prompt,
    base_conversations, tokenizer, openrouter_client, sampling_client, vocab_size,
    max_tokens=MAX_TOKENS,
):
    top_k = 1
    top_p = 1.0
    verification_temperature = 1e-8
    seed = 42

    print(f"\n{'=' * 60}")
    print(f"Experiment: {experiment_name}")
    print(f'  Gen: "{generation_prompt[:50]}..."')
    print(f'  Ver: "{verification_prompt[:50]}..."')
    print(f"{'=' * 60}")

    gen_conversations = add_system_prompt(base_conversations, generation_prompt)
    responses = await generate_all(
        openrouter_client, OPENROUTER_MODEL_NAME, gen_conversations,
        max_tokens=max_tokens, temperature=0.0, provider=PROVIDER,
    )

    verify_conversations = add_system_prompt(base_conversations, verification_prompt)
    sequences = create_token_sequences(verify_conversations, responses, tokenizer, max_tokens)

    total_tokens = sum(len(s.output_token_ids) for s in sequences)
    print(f"Generated {total_tokens} tokens across {len(sequences)} sequences")

    results = verify_outputs_tinker(
        sequences,
        sampling_client=sampling_client,
        vocab_size=vocab_size,
        temperature=verification_temperature,
        top_k=top_k,
        top_p=top_p,
        seed=seed,
    )

    summary = compute_metrics_summary(results)
    summary["experiment_name"] = experiment_name
    summary["generation_prompt"] = generation_prompt
    summary["verification_prompt"] = verification_prompt
    summary["prompts_match"] = generation_prompt == verification_prompt
    summary["timestamp"] = datetime.now().isoformat()

    return summary


async def main():
    openrouter_key_path = Path("/Users/adamkarvonen/repos/token-difr/openrouter_api_key.txt")
    openrouter_api_key = openrouter_key_path.read_text().strip() if openrouter_key_path.exists() else os.environ.get("OPENROUTER_API_KEY", "")
    tinker_api_key = os.environ.get("TINKER_API_KEY", "")

    if not openrouter_api_key or not tinker_api_key:
        raise ValueError("API keys not found")

    openrouter_client = openai.AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)

    print(f"Loading tokenizer for {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    vocab_size = len(tokenizer)

    service_client = tinker.ServiceClient(api_key=tinker_api_key)
    sampling_client = service_client.create_sampling_client(base_model=MODEL_NAME)

    print(f"Loading {N_PROMPTS} prompts...")
    conversations = construct_prompts(n_prompts=N_PROMPTS, max_ctx_len=MAX_CTX_LEN, tokenizer=tokenizer)
    print(f"Loaded {len(conversations)} prompts")

    # Just test 3 experiments: baseline, subtle, major
    base_prompt = "You are a helpful assistant."

    experiments = [
        ("baseline", base_prompt, base_prompt),
        ("trailing_space", base_prompt, base_prompt + " "),
        ("major_change", base_prompt, "You are a helpful assistant for Duolingo."),
    ]

    results = []
    for name, ver_prompt, gen_prompt in experiments:
        summary = await run_single_experiment(
            name, gen_prompt, ver_prompt,
            conversations, tokenizer, openrouter_client, sampling_client, vocab_size,
        )
        results.append(summary)
        print(f"\n  Exact match rate: {summary['exact_match_rate']:.2%}")
        print(f"  Avg probability: {summary['avg_prob']:.4f}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        match_str = "YES" if r["prompts_match"] else "NO"
        print(f"{r['experiment_name']:<20} Match: {match_str:<5} Exact: {r['exact_match_rate']:.2%}")

    with open(OUTPUT_DIR / "test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {OUTPUT_DIR / 'test_results.json'}")


if __name__ == "__main__":
    asyncio.run(main())
