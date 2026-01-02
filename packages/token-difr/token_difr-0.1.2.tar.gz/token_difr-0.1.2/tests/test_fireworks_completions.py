"""Tests comparing tokenization strategies for OpenRouter -> Fireworks verification."""

import asyncio
import os

import openai
import pytest
from openai import AsyncOpenAI
from transformers import AutoTokenizer

from token_difr import (
    FIREWORKS_MODEL_REGISTRY,
    TokenSequence,
    compute_metrics_summary,
    construct_prompts,
    get_openrouter_name,
    verify_outputs_fireworks,
)
from token_difr.openrouter_api import generate_openrouter_responses, tokenize_openrouter_responses

# Load .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Model configurations: HuggingFace model name -> OpenRouter provider
MODEL_TO_PROVIDER = {
    "meta-llama/Llama-3.3-70B-Instruct": "fireworks",
    "Qwen/Qwen3-235B-A22B-Instruct-2507": "together",
}

N_TEST_PROMPTS = 50
MAX_TOKENS = 200
CONCURRENCY = 10
THRESHOLD = 0.95


def get_fireworks_api_key():
    """Get Fireworks API key from environment."""
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        pytest.skip("FIREWORKS_API_KEY environment variable not set")
    return api_key


def get_openrouter_api_key() -> str:
    """Get OpenRouter API key from environment."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY environment variable not set")
    return api_key


# =============================================================================
# Tokenization Strategies
# =============================================================================


def tokenize_standard(
    conversations: list[list[dict]],
    responses: list,
    tokenizer,
    max_tokens: int | None = None,
) -> list[TokenSequence]:
    """Standard tokenization: encode response text directly.

    This is the existing approach from tokenize_openrouter_responses.
    """
    return tokenize_openrouter_responses(conversations, responses, tokenizer, max_tokens)


def tokenize_full_sequence(
    conversations: list[list[dict]],
    responses: list,
    tokenizer,
    max_tokens: int | None = None,
) -> list[TokenSequence]:
    """Full sequence tokenization: encode prompt+response together, then slice.

    This preserves tokenization context at the prompt/response boundary,
    which can improve accuracy for BPE tokenizers.
    """
    outputs = []

    for conv, completion in zip(conversations, responses):
        message = completion.choices[0].message
        content = message.content or ""
        reasoning = getattr(message, "reasoning", None) or ""

        # Build full response text (handling thinking models)
        if reasoning:
            full_response = f"<think>{reasoning}</think>{content}"
        else:
            full_response = content

        # Get prompt tokens
        rendered = tokenizer.apply_chat_template(conv, tokenize=False, add_generation_prompt=True)
        prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False)

        # Encode FULL sequence (prompt + response) together
        full_text = rendered + full_response
        full_token_ids = tokenizer.encode(full_text, add_special_tokens=False)

        # Slice off the prompt portion to get response tokens
        response_token_ids = full_token_ids[len(prompt_token_ids) :]

        # Apply max_tokens limit if specified
        if max_tokens is not None:
            response_token_ids = response_token_ids[:max_tokens]

        outputs.append(
            TokenSequence(
                prompt_token_ids=prompt_token_ids,
                output_token_ids=response_token_ids,
            )
        )

    return outputs


# =============================================================================
# Test Functions
# =============================================================================


@pytest.mark.parametrize(
    "hf_model",
    list(MODEL_TO_PROVIDER.keys()),
    ids=[k.split("/")[-1] for k in MODEL_TO_PROVIDER.keys()],
)
def test_tokenization_standard(hf_model):
    """Test standard tokenization: encode response text directly."""
    _run_tokenization_test(hf_model, tokenize_standard, "standard")


@pytest.mark.parametrize(
    "hf_model",
    list(MODEL_TO_PROVIDER.keys()),
    ids=[k.split("/")[-1] for k in MODEL_TO_PROVIDER.keys()],
)
def test_tokenization_full_sequence(hf_model):
    """Test full sequence tokenization: encode prompt+response together, then slice."""
    _run_tokenization_test(hf_model, tokenize_full_sequence, "full_sequence")


def _run_tokenization_test(hf_model: str, tokenize_fn, strategy_name: str):
    """Common test logic for different tokenization strategies."""
    fireworks_api_key = get_fireworks_api_key()
    openrouter_api_key = get_openrouter_api_key()
    fireworks_model = FIREWORKS_MODEL_REGISTRY[hf_model]
    openrouter_model = get_openrouter_name(hf_model)
    openrouter_provider = MODEL_TO_PROVIDER[hf_model]
    model_name = hf_model.split("/")[-1]

    temperature = 0.0
    top_k = 50
    topk_logprobs = 5
    top_p = 0.95
    seed = 42

    # Create clients
    fireworks_client = AsyncOpenAI(
        api_key=fireworks_api_key,
        base_url="https://api.fireworks.ai/inference/v1",
    )
    openrouter_client = openai.AsyncOpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(hf_model, trust_remote_code=True)

    # Construct test prompts
    conversations = construct_prompts(n_prompts=N_TEST_PROMPTS, model_name=hf_model)

    # Generate via OpenRouter
    responses = asyncio.run(
        generate_openrouter_responses(
            client=openrouter_client,
            conversations=conversations,
            model=openrouter_model,
            provider=openrouter_provider,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
            seed=seed,
            concurrency=CONCURRENCY,
        )
    )

    # Tokenize using the specified strategy
    outputs = tokenize_fn(conversations, responses, tokenizer, MAX_TOKENS)
    vocab_size = len(tokenizer)

    total_tokens = sum(len(o.output_token_ids) for o in outputs)
    assert total_tokens > 0, "Should generate at least some tokens"

    # Verify via Fireworks
    results = asyncio.run(
        verify_outputs_fireworks(
            outputs,
            vocab_size=vocab_size,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            seed=seed,
            client=fireworks_client,
            model=fireworks_model,
            topk_logprobs=topk_logprobs,
            concurrency=CONCURRENCY,
        )
    )

    summary = compute_metrics_summary(results)
    print(f"\n{model_name} [{strategy_name}]: {summary['exact_match_rate']:.2%} ({summary['total_tokens']} tokens)")

    assert summary["exact_match_rate"] >= THRESHOLD, (
        f"Exact match rate {summary['exact_match_rate']:.2%} is below {THRESHOLD:.0%} threshold"
    )
