# OpenRouter API Investigation: Can We Replace Fireworks API?

## Executive Summary

**Short answer: No, we cannot replace Fireworks API with OpenRouter for prompt token logprobs.**

The token-difr verification system requires a very specific feature: **logprobs for input/prompt tokens** (not just output tokens). After extensive testing, OpenRouter does not support this feature, even when routing to Fireworks as a provider.

## What We Need (Fireworks API Capabilities)

The current Fireworks-based verification uses these critical features:

1. **Token ID prompts**: Send `prompt` as a list of integers (token IDs) instead of text
2. **Echo mode**: `echo=True` includes the prompt in the response
3. **Prompt logprobs**: Returns `logprob` and `top_logprobs` for each prompt token
4. **Token ID in response**: Each logprob entry includes `token_id`

Example Fireworks completions API response with `echo=True, logprobs=True`:
```json
{
  "choices": [{
    "text": "Hello, my name is [Your Name], and",
    "logprobs": {
      "content": [
        {"token": "Hello", "token_id": 9906, "logprob": 0.0, "top_logprobs": [...]},
        {"token": ",", "token_id": 11, "logprob": -19.23, "top_logprobs": [...]},
        ...
      ]
    }
  }]
}
```

## OpenRouter Investigation Results

### Test 1: OpenRouter Completions API

**Finding**: OpenRouter internally converts completions API requests to chat/messages format.

When sending:
```json
{
  "model": "meta-llama/llama-3.3-70b-instruct",
  "prompt": "Hello, my name is",
  "echo": true,
  "logprobs": 3,
  "provider": {"only": ["fireworks"]}
}
```

OpenRouter transforms this to:
```json
{
  "messages": [{"role": "user", "content": "Hello, my name is"}]
}
```

This causes Fireworks to reject the request with:
> "Missing required input field: 'prompt'; Extra inputs are not permitted, field: 'messages'"

### Test 2: OpenRouter with Token ID Prompts

**Finding**: OpenRouter does NOT support token ID prompts.

When sending `"prompt": [9906, 11, 856, 836, 374]`, OpenRouter returns:
> "Input required: specify 'prompt'"

### Test 3: OpenRouter Chat Completions with Logprobs

**Finding**: OpenRouter DOES forward logprobs for chat completions to Fireworks provider, BUT:
- Only returns logprobs for **output tokens**, not input/prompt tokens
- No `echo` functionality (echo is a completions API feature)
- Chat format adds template overhead, making tokenization unpredictable

### Test 4: Alternative Providers

| Provider | Token ID Prompt | Echo | Prompt Logprobs | Works for token-difr? |
|----------|-----------------|------|-----------------|----------------------|
| **Fireworks (direct)** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **Yes** |
| OpenRouter → Fireworks | ❌ No | ❌ Broken | ❌ No | ❌ No |
| Together AI | ❌ No (422 error) | ❌ No (output only) | ❌ No | ❌ No |
| OpenRouter → Others | ❌ No | ❌ No | ❌ No | ❌ No |

## Why Prompt Logprobs Matter

For token-difr verification, we need to:
1. Send the exact token sequence (prompt + output) to the model
2. Get logprobs for each output token position
3. Compare the claimed output token against the model's top predictions

The Fireworks API with `echo=True` lets us:
- Pass token IDs directly (avoiding tokenization mismatches)
- Get logprobs for positions starting from the prompt (to know what the model would predict after the prompt)

## Technical Details

### Fireworks Completions API Format

Request:
```python
response = client.completions.create(
    model="accounts/fireworks/models/llama-v3p3-70b-instruct",
    prompt=[9906, 11, 856, 836, 374],  # Token IDs
    max_tokens=10,
    temperature=0.0,
    echo=True,
    logprobs=True,
    extra_body={"top_logprobs": 5},
)
```

Response includes:
- `logprobs.content`: Array of length `len(prompt) + len(output)`
- Each item has: `token`, `token_id`, `logprob`, `top_logprobs[]`
- `top_logprobs[]` contains alternatives with their `token_id` and `logprob`

### OpenRouter's Limitation

OpenRouter is designed as a unified gateway that normalizes requests across providers. This means:
1. All requests go through OpenRouter's processing layer
2. The completions API is essentially a thin wrapper over chat completions
3. Provider-specific features like token ID prompts and echo mode are not passed through

## Recommendations

### Option 1: Keep Fireworks API (Recommended)

Fireworks API is the only tested provider that supports all required features. The burden of getting a Fireworks API key is justified by:
- Full feature support for verification
- Direct API without intermediary processing
- Reliable logprobs with token IDs

### Option 2: Future Alternatives to Investigate

1. **DeepInfra**: Documentation mentions `echo` and `logprobs` support for completions. Requires testing with API key.

2. **Self-hosted vLLM**: vLLM supports `prompt_logprobs` and `echo=True`. Could be an option for users who want to avoid API keys entirely.

3. **OpenRouter Feature Request**: Request OpenRouter to:
   - Pass through raw completions requests to providers like Fireworks
   - Support token ID prompts in completions API
   - Forward echo parameter properly

### Option 3: Hybrid Approach

- Use OpenRouter for **generation** (works fine, just no prompt logprobs)
- Use Fireworks for **verification** (requires prompt logprobs)

This is essentially what the current codebase does in tests.

## Test Scripts Created

1. `experiments/test_openrouter_completions_echo.py` - Initial SDK-based tests
2. `experiments/test_openrouter_completions_raw.py` - Raw HTTP tests bypassing SDK
3. `experiments/test_openrouter_completions_final.py` - Comprehensive provider comparison
4. `experiments/test_alternative_providers.py` - Together AI and other providers
5. `experiments/test_fireworks_detailed.py` - Detailed Fireworks response format

## Can You Use an OpenRouter API Key with Fireworks API?

**No.** These are completely separate services with separate authentication systems.

- **OpenRouter API keys** only work with `https://openrouter.ai/api/v1`
- **Fireworks API keys** only work with `https://api.fireworks.ai/inference/v1`

There is no way to:
- Use an OpenRouter API key to authenticate directly with Fireworks
- Have OpenRouter "pass through" your OpenRouter credits to Fireworks' raw completions API
- Access Fireworks' completions API features through OpenRouter's gateway

### Why This Matters

Many developers have OpenRouter API keys (it's a popular aggregator), but fewer have direct Fireworks API keys. Unfortunately:

1. **OpenRouter acts as a middleman** - It doesn't just proxy requests; it transforms them
2. **No BYOK for Fireworks** - OpenRouter's "Bring Your Own Key" feature supports some providers (Azure, Bedrock, Vertex) but not Fireworks
3. **Different billing systems** - OpenRouter has its own credit system separate from Fireworks

### Getting a Fireworks API Key

To use the prompt logprobs feature, you need a Fireworks API key:
1. Sign up at https://fireworks.ai
2. Get API key from dashboard
3. Fireworks offers a free tier with credits for testing

## Conclusion

**OpenRouter cannot replace Fireworks API for prompt token logprobs.** The OpenRouter completions API is fundamentally a chat-based interface that doesn't support the raw completions features needed for token-difr verification.

For users who only have OpenRouter API keys, they can:
1. Generate outputs via OpenRouter (already supported)
2. But cannot verify outputs without a Fireworks API key (or similar provider)

---
*Investigation completed: December 2024*
*Test environment: Python 3.11, OpenAI SDK, direct HTTP requests*
