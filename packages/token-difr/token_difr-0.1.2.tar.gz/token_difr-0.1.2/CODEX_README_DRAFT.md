# Codex Read Me Draft

This is a working draft for the project README. It focuses on the audit workflow
most users will want: generate tokens via OpenRouter and verify with Fireworks
prompt logprobs. Edit as needed.

## What This Project Does

Token-difr verifies LLM outputs using Gumbel-Max sampling verification. It can:

- Audit external providers by generating via OpenRouter and verifying via Fireworks.
- Cross-check verification via Tinker.
- Fully replay sampling locally with vLLM when you control seeds and sampling params.

## Default Audit Flow (Recommended)

1. Generate responses via OpenRouter (pin a provider or let OpenRouter route)
2. Tokenize responses with the model tokenizer
3. Verify tokens against Fireworks prompt logprobs

This requires `OPENROUTER_API_KEY` and `FIREWORKS_API_KEY`.

## Quick Start: Audit a Provider

```python
from token_difr import audit_provider, construct_prompts

prompts = construct_prompts(
    n_prompts=100,
    model_name="Qwen/Qwen3-235B-A22B-Instruct-2507",
    system_prompt="You are a helpful assistant.",
)

result = audit_provider(
    prompts,
    model="Qwen/Qwen3-235B-A22B-Instruct-2507",
    provider="together",  # or None to let OpenRouter route
    max_tokens=200,
    temperature=0.0,      # use greedy for cross-provider audits
)

print(result)
```

Typical knobs:

- `n_prompts` (how many prompts to sample)
- `max_tokens` (output length)
- `provider` (which OpenRouter provider to audit)

For a multi-provider run that saves JSON results, see `audit_demonstration.py`.

## Manual Pipeline (Advanced)

If you want more control, the audit flow can be done manually:

1. Generate outputs via OpenRouter
2. Convert text to tokens with the model tokenizer
3. Verify tokens with Fireworks logprobs

See `openrouter_demo.py` for a working example (Tinker-backed verification).

## Model Registry (Important)

Model names differ across HuggingFace, OpenRouter, and Fireworks. Audits require
a Fireworks mapping. OpenRouter mappings are only needed when the OpenRouter name
is not `hf_name.lower()`.

```python
from token_difr import register_fireworks_model, register_openrouter_model

register_fireworks_model(
    "my-org/My-Model",
    "accounts/fireworks/models/my-model",
)

register_openrouter_model(
    "my-org/My-Model",
    "my-org/my-model",
)
```

The registries live in `src/token_difr/model_registry.py`.

## Verification Backends

- Fireworks (default): API-only, broad model coverage, exposes prompt logprobs.
- Tinker: optional API backend for cross-checking Fireworks.
- Local (vLLM): full sampling replay when you control the seed and sampling params.

## Auditing Notes

- Cross-provider audits use `temperature=0.0` because providers handle seeds differently.
- Exact match is sensitive to chat templates and tokenization drift (decode/encode is not stable).
- Token-level metrics trade interpretability for statistical power.
  Example: 200 tokens x 100 prompts = 20,000 datapoints.

## Verifier Trust / Bootstrapping

If you want to validate Fireworks as a verifier:

- Compare Fireworks against a trusted reference API for a model you trust
  (e.g., Kimi-K2-Thinking).
- Or generate a one-time set of local outputs and verify Fireworks against those tokens.

## System Prompt Detection Demo

`system_prompt_detection.py` tests prompt tampering by generating with one system
prompt and verifying against another. Results are saved to
`system_prompt_detection_results.json`.

## Local Calibration (Optional)

For local verification, consider a separate section or doc describing expected
noise for different quantization or KV cache settings. The key benefit of local
verification is exact sampling replay when the seed and params are known.

## Requirements (Draft)

- Python >= 3.10
- OpenRouter + Fireworks API keys for auditing
- Local verification: PyTorch + vLLM + CUDA-capable GPU

