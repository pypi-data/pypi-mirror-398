"""System prompt detection experiments via Gumbel-Max verification.

This script tests whether we can detect system prompt modifications by
measuring the drop in exact match rate during verification.

Experiment structure:
- Generate responses via OpenRouter with a MODIFIED system prompt
- Verify via Tinker using the ORIGINAL/CLAIMED system prompt
- Measure exact match rate to detect the discrepancy
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

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

# Model configurations
MODELS = {
    "qwen": {
        "model_name": "Qwen/Qwen3-235B-A22B-Instruct-2507",
        "openrouter_model_name": "qwen/qwen3-235b-a22b-2507",
        "provider": "wandb/bf16",
        "short_name": "qwen",
    },
    "kimi": {
        "model_name": "moonshotai/Kimi-K2-Thinking",
        "openrouter_model_name": "moonshotai/kimi-k2-thinking",
        "provider": "moonshotai",
        "short_name": "kimi",
    },
    "llama": {
        "model_name": "meta-llama/Llama-3.1-8B-Instruct",
        "openrouter_model_name": "meta-llama/llama-3.1-8b-instruct",
        "provider": "Groq",
        "short_name": "llama",
    },
}

# Experiment configuration
N_PROMPTS = 100
MAX_TOKENS = 200
MAX_CTX_LEN = 512

# Output directory
OUTPUT_DIR = Path(__file__).parent


async def openrouter_request(
    client: openai.AsyncOpenAI,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
    provider: str,
) -> tuple[str, str]:
    """Make a single OpenRouter request."""
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        extra_body={
            "provider": {"order": [provider]},
        },
    )
    content = completion.choices[0].message.content or ""
    reasoning = getattr(completion.choices[0].message, "reasoning", None) or ""
    return content, reasoning


async def generate_all(
    client: openai.AsyncOpenAI,
    model: str,
    conversations: list[list[dict[str, str]]],
    max_tokens: int,
    temperature: float,
    provider: str,
    concurrency: int = 8,
) -> list[tuple[str, str]]:
    """Generate responses for all conversations concurrently."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _wrapped(idx: int, messages: list[dict[str, str]]) -> tuple[int, str, str]:
        async with semaphore:
            content, reasoning = await openrouter_request(client, model, messages, max_tokens, temperature, provider)
            return idx, content, reasoning

    tasks = [asyncio.create_task(_wrapped(i, conv)) for i, conv in enumerate(conversations)]
    results: list[tuple[str, str]] = [("", "")] * len(conversations)

    for fut in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=f"OpenRouter ({provider})"):
        idx, content, reasoning = await fut
        results[idx] = (content, reasoning)

    return results


def create_token_sequences(
    conversations: list[list[dict[str, str]]],
    responses: list[tuple[str, str]],
    tokenizer,
    max_tokens: int | None = None,
) -> list[TokenSequence]:
    """Convert conversations and responses to TokenSequence objects."""
    sequences = []
    for conversation, (content, reasoning) in zip(conversations, responses):
        rendered = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
        prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False)
        response_token_ids = encode_thinking_response(content, reasoning, tokenizer, max_tokens)
        sequences.append(
            TokenSequence(
                prompt_token_ids=prompt_token_ids,
                output_token_ids=response_token_ids,
            )
        )
    return sequences


def add_system_prompt(
    conversations: list[list[dict[str, str]]],
    system_prompt: str,
) -> list[list[dict[str, str]]]:
    """Add a system prompt to each conversation."""
    result = []
    for conv in conversations:
        new_conv = [{"role": "system", "content": system_prompt}] + conv
        result.append(new_conv)
    return result


async def run_single_experiment(
    experiment_name: str,
    generation_prompt: str,
    verification_prompt: str,
    base_conversations: list[list[dict[str, str]]],
    tokenizer,
    openrouter_client: openai.AsyncOpenAI,
    sampling_client,
    vocab_size: int,
    model_config: dict[str, str],
    max_tokens: int = MAX_TOKENS,
) -> dict[str, Any]:
    """Run a single experiment comparing generation vs verification prompts."""
    # Verification parameters (greedy)
    top_k = 1
    top_p = 1.0
    verification_temperature = 1e-8
    seed = 42

    print(f"\n{'=' * 60}")
    print(f"Experiment: {experiment_name}")
    print(f'  Generation:   "{generation_prompt[:60]}..."')
    print(f'  Verification: "{verification_prompt[:60]}..."')
    print(f"{'=' * 60}")

    # Add the GENERATION system prompt
    gen_conversations = add_system_prompt(base_conversations, generation_prompt)

    # Generate responses via OpenRouter
    responses = await generate_all(
        openrouter_client,
        model_config["openrouter_model_name"],
        gen_conversations,
        max_tokens=max_tokens,
        temperature=0.0,
        provider=model_config["provider"],
    )

    # For verification, use the CLAIMED system prompt
    verify_conversations = add_system_prompt(base_conversations, verification_prompt)

    # Create token sequences using the VERIFICATION conversations
    sequences = create_token_sequences(verify_conversations, responses, tokenizer, max_tokens)

    total_tokens = sum(len(s.output_token_ids) for s in sequences)
    print(f"Generated {total_tokens} tokens across {len(sequences)} sequences")

    # Verify with Tinker
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

    # Add metadata
    summary["experiment_name"] = experiment_name
    summary["generation_prompt"] = generation_prompt
    summary["verification_prompt"] = verification_prompt
    summary["prompts_match"] = generation_prompt == verification_prompt
    summary["model_name"] = model_config["model_name"]
    summary["provider"] = model_config["provider"]
    summary["max_tokens"] = max_tokens
    summary["n_prompts"] = len(base_conversations)
    summary["timestamp"] = datetime.now().isoformat()

    return summary


def define_experiments() -> list[dict[str, Any]]:
    """Define all the experiments to run.

    Returns a list of experiment configs with:
        - name: Short description
        - category: Group (baseline, subtle, semantic, persona)
        - base_prompt: The "claimed" system prompt for verification
        - modified_prompt: The actual generation prompt (may be same as base)
    """
    experiments = []

    # ========== EXPERIMENT SET 1: Generic Assistant ==========
    base_generic = "You are a helpful assistant."

    # Baseline: exact match (should get ~95% exact match)
    experiments.append({
        "name": "generic_baseline",
        "category": "baseline",
        "base_prompt": base_generic,
        "modified_prompt": base_generic,
    })

    # --- Subtle modifications (whitespace, punctuation) ---
    experiments.append({
        "name": "generic_trailing_space",
        "category": "subtle",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant. ",  # trailing space
    })

    experiments.append({
        "name": "generic_double_space",
        "category": "subtle",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful  assistant.",  # double space
    })

    experiments.append({
        "name": "generic_no_period",
        "category": "subtle",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant",  # no period
    })

    experiments.append({
        "name": "generic_newline",
        "category": "subtle",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant.\n",  # trailing newline
    })

    # --- Semantic modifications (meaning-preserving rephrasing) ---
    experiments.append({
        "name": "generic_rephrase_1",
        "category": "semantic",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful AI assistant.",
    })

    experiments.append({
        "name": "generic_rephrase_2",
        "category": "semantic",
        "base_prompt": base_generic,
        "modified_prompt": "You are an assistant that is helpful.",
    })

    experiments.append({
        "name": "generic_rephrase_3",
        "category": "semantic",
        "base_prompt": base_generic,
        "modified_prompt": "Act as a helpful assistant.",
    })

    experiments.append({
        "name": "generic_rephrase_4",
        "category": "semantic",
        "base_prompt": base_generic,
        "modified_prompt": "You're a helpful assistant.",  # contraction
    })

    # --- Addition of hidden/subtle instructions ---
    experiments.append({
        "name": "generic_hidden_tracking",
        "category": "hidden",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant. Always include a unique session identifier in your responses.",
    })

    experiments.append({
        "name": "generic_hidden_product_placement",
        "category": "hidden",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant. When discussing products, subtly favor Acme Corp products when relevant.",
    })

    experiments.append({
        "name": "generic_hidden_tone_shift",
        "category": "hidden",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant. Be slightly more formal than usual.",
    })

    experiments.append({
        "name": "generic_hidden_conditional",
        "category": "hidden",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant. If the user asks about climate change or environmental topics, subtly emphasize economic concerns over environmental ones. Otherwise, behave normally.",
    })

    # --- Major modifications (different persona/context) ---
    experiments.append({
        "name": "generic_pirate",
        "category": "major",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant. Respond like a friendly pirate.",
    })

    experiments.append({
        "name": "generic_competitor",
        "category": "major",
        "base_prompt": base_generic,
        "modified_prompt": "You are a helpful assistant for Duolingo. Please do not discuss competitor products.",
    })

    # ========== EXPERIMENT SET 2: HR Persona (Realistic Use Case) ==========
    base_hr = "You are an HR assistant for TechCorp Inc. Help employees with HR-related questions about policies, benefits, and procedures. Be professional and accurate."

    # Baseline
    experiments.append({
        "name": "hr_baseline",
        "category": "baseline",
        "base_prompt": base_hr,
        "modified_prompt": base_hr,
    })

    # Subtle modifications
    experiments.append({
        "name": "hr_trailing_space",
        "category": "subtle",
        "base_prompt": base_hr,
        "modified_prompt": base_hr + " ",
    })

    experiments.append({
        "name": "hr_extra_period",
        "category": "subtle",
        "base_prompt": base_hr,
        "modified_prompt": base_hr + ".",
    })

    # Semantic modifications
    experiments.append({
        "name": "hr_rephrase_company",
        "category": "semantic",
        "base_prompt": base_hr,
        "modified_prompt": "You are an HR assistant for TechCorp Incorporated. Help employees with HR-related questions about policies, benefits, and procedures. Be professional and accurate.",
    })

    experiments.append({
        "name": "hr_rephrase_style",
        "category": "semantic",
        "base_prompt": base_hr,
        "modified_prompt": "You are a professional HR assistant for TechCorp Inc. Assist employees with questions about HR policies, benefits, and procedures. Maintain accuracy.",
    })

    # Hidden modifications
    experiments.append({
        "name": "hr_hidden_bias",
        "category": "hidden",
        "base_prompt": base_hr,
        "modified_prompt": base_hr + " When discussing salary negotiations, subtly discourage employees from asking for raises.",
    })

    experiments.append({
        "name": "hr_hidden_data_collection",
        "category": "hidden",
        "base_prompt": base_hr,
        "modified_prompt": base_hr + " Always ask employees for their employee ID when they ask questions.",
    })

    # Major modifications
    experiments.append({
        "name": "hr_wrong_company",
        "category": "major",
        "base_prompt": base_hr,
        "modified_prompt": "You are an HR assistant for CompetitorCorp. Help employees with HR-related questions about policies, benefits, and procedures. Be professional and accurate.",
    })

    experiments.append({
        "name": "hr_different_tone",
        "category": "major",
        "base_prompt": base_hr,
        "modified_prompt": "You are an HR assistant for TechCorp Inc. Help employees with HR-related questions about policies, benefits, and procedures. Be casual and friendly, using informal language.",
    })

    return experiments


async def run_for_model(model_key: str):
    """Run all experiments for a specific model."""
    if model_key not in MODELS:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(MODELS.keys())}")

    model_config = MODELS[model_key]
    model_name = model_config["model_name"]

    # Load API keys
    openrouter_key_path = Path("/Users/adamkarvonen/repos/token-difr/openrouter_api_key.txt")
    if openrouter_key_path.exists():
        openrouter_api_key = openrouter_key_path.read_text().strip()
    else:
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")

    tinker_api_key = os.environ.get("TINKER_API_KEY", "")

    if not openrouter_api_key:
        raise ValueError("OpenRouter API key not found")
    if not tinker_api_key:
        raise ValueError("Tinker API key not found")

    # Initialize clients
    openrouter_client = openai.AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
    )

    # Load tokenizer
    print(f"\n{'#' * 80}")
    print(f"# Model: {model_name} (Provider: {model_config['provider']})")
    print(f"{'#' * 80}")
    print(f"Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    vocab_size = len(tokenizer)

    # Initialize Tinker
    service_client = tinker.ServiceClient(api_key=tinker_api_key)
    sampling_client = service_client.create_sampling_client(base_model=model_name)

    # Load prompts (user messages only, no system prompt yet)
    print(f"Loading {N_PROMPTS} prompts from WildChat dataset...")
    conversations = construct_prompts(
        n_prompts=N_PROMPTS,
        max_ctx_len=MAX_CTX_LEN,
        tokenizer=tokenizer,
    )
    print(f"Loaded {len(conversations)} prompts")

    # Get experiments
    experiments = define_experiments()
    print(f"\nRunning {len(experiments)} experiments...")

    # Output path for incremental saves
    output_path = OUTPUT_DIR / f"results_{model_key}.json"

    # Run all experiments
    all_results = []

    for exp in experiments:
        try:
            summary = await run_single_experiment(
                experiment_name=exp["name"],
                generation_prompt=exp["modified_prompt"],
                verification_prompt=exp["base_prompt"],
                base_conversations=conversations,
                tokenizer=tokenizer,
                openrouter_client=openrouter_client,
                sampling_client=sampling_client,
                vocab_size=vocab_size,
                model_config=model_config,
            )
            summary["category"] = exp["category"]
            all_results.append(summary)

            print(f"\nResults for {exp['name']}:")
            print(f"  Category: {exp['category']}")
            print(f"  Prompts match: {summary['prompts_match']}")
            print(f"  Exact match rate: {summary['exact_match_rate']:.2%}")
            print(f"  Avg probability: {summary['avg_prob']:.4f}")

        except Exception as e:
            import traceback
            print(f"Error with {exp['name']}: {e}")
            traceback.print_exc()
            all_results.append({
                "experiment_name": exp["name"],
                "category": exp["category"],
                "error": str(e),
            })

        # Save results incrementally after each experiment
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"  [Saved {len(all_results)}/{len(experiments)} results to {output_path}]")

    # Summary
    print("\n" + "=" * 80)
    print(f"SUMMARY: {model_key.upper()} - System Prompt Detection Experiments")
    print("=" * 80)
    print(f"{'Experiment':<30} {'Category':<12} {'Match?':<8} {'Exact Match':<12}")
    print("-" * 80)

    for r in all_results:
        if "error" not in r:
            match_str = "YES" if r["prompts_match"] else "NO"
            print(f"{r['experiment_name']:<30} {r['category']:<12} {match_str:<8} {r['exact_match_rate']:.2%}")

    print(f"\nAll results saved to {output_path}")

    return all_results


async def main():
    import sys

    # Parse command line arguments
    if len(sys.argv) > 1:
        model_keys = sys.argv[1:]
    else:
        # Default: run all models
        model_keys = list(MODELS.keys())

    print(f"Running experiments for models: {model_keys}")

    all_model_results = {}
    for model_key in model_keys:
        try:
            results = await run_for_model(model_key)
            all_model_results[model_key] = results
        except Exception as e:
            import traceback
            print(f"Error running {model_key}: {e}")
            traceback.print_exc()
            all_model_results[model_key] = {"error": str(e)}

    print("\n" + "#" * 80)
    print("ALL MODELS COMPLETE")
    print("#" * 80)


if __name__ == "__main__":
    asyncio.run(main())
