"""
Test script to investigate OpenRouter completions API for prompt logprobs.

GOAL: Determine if we can use OpenRouter API keys to get prompt token logprobs
similar to what we currently get with Fireworks API directly.

What we need:
1. Send prompt as token IDs
2. Use echo=True to get prompt echoed back
3. Get logprobs for prompt tokens (not just output tokens)

Tests:
1. OpenRouter completions API with string prompt + echo + logprobs
2. OpenRouter completions API with token ID prompt (if supported)
3. OpenRouter -> Fireworks provider routing
4. Compare with direct Fireworks API behavior
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from transformers import AutoTokenizer

load_dotenv()

# =============================================================================
# Setup
# =============================================================================

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")

if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY not set")
if not FIREWORKS_API_KEY:
    print("WARNING: FIREWORKS_API_KEY not set")

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
) if OPENROUTER_API_KEY else None

fireworks_client = OpenAI(
    api_key=FIREWORKS_API_KEY,
    base_url="https://api.fireworks.ai/inference/v1",
) if FIREWORKS_API_KEY else None

# Model config
HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"

TEST_PROMPT = "Hello, my name is"

print("=" * 60)
print("OpenRouter Completions API - Echo/Logprobs Investigation")
print("=" * 60)

# =============================================================================
# Test 1: Direct Fireworks API (baseline)
# =============================================================================

print("\n" + "=" * 60)
print("TEST 1: Direct Fireworks API (baseline)")
print("=" * 60)

if fireworks_client:
    try:
        response = fireworks_client.completions.create(
            model=FIREWORKS_MODEL,
            prompt=TEST_PROMPT,
            max_tokens=10,
            temperature=0.0,
            echo=True,
            logprobs=True,
            extra_body={"top_logprobs": 3},
        )

        print(f"\nPrompt: '{TEST_PROMPT}'")
        print(f"Full text: '{response.choices[0].text}'")
        print(f"Finish reason: {response.choices[0].finish_reason}")

        logprobs = response.choices[0].logprobs
        print(f"\nLogprobs available: {logprobs is not None}")

        if logprobs:
            # Check what fields are available
            print(f"Logprobs type: {type(logprobs)}")
            if hasattr(logprobs, 'content') and logprobs.content:
                print(f"Has content array: Yes, length {len(logprobs.content)}")
                print("\nFirst few tokens with logprobs:")
                for i, item in enumerate(logprobs.content[:8]):
                    token_id = getattr(item, 'token_id', 'N/A')
                    token = getattr(item, 'token', 'N/A')
                    lp = getattr(item, 'logprob', 'N/A')
                    print(f"  [{i}] token='{token}', token_id={token_id}, logprob={lp}")
            elif hasattr(logprobs, 'tokens'):
                print(f"Has tokens array: {logprobs.tokens}")
                print(f"Has token_logprobs: {getattr(logprobs, 'token_logprobs', None)}")
            else:
                print(f"Logprobs fields: {dir(logprobs)}")

    except Exception as e:
        print(f"Error: {e}")
else:
    print("Skipped - FIREWORKS_API_KEY not set")

# =============================================================================
# Test 2: Fireworks API with token IDs as prompt
# =============================================================================

print("\n" + "=" * 60)
print("TEST 2: Fireworks API with token IDs as prompt")
print("=" * 60)

if fireworks_client:
    try:
        tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
        prompt_token_ids = tokenizer.encode(TEST_PROMPT, add_special_tokens=False)
        print(f"Prompt: '{TEST_PROMPT}'")
        print(f"Token IDs: {prompt_token_ids}")

        response = fireworks_client.completions.create(
            model=FIREWORKS_MODEL,
            prompt=prompt_token_ids,  # Send token IDs directly!
            max_tokens=10,
            temperature=0.0,
            echo=True,
            logprobs=True,
            extra_body={"top_logprobs": 3},
        )

        print(f"\nFull text: '{response.choices[0].text}'")

        logprobs = response.choices[0].logprobs
        if logprobs and hasattr(logprobs, 'content') and logprobs.content:
            print(f"\nLogprobs content length: {len(logprobs.content)}")
            print(f"Prompt length: {len(prompt_token_ids)}")
            print(f"Expected output tokens: {len(logprobs.content) - len(prompt_token_ids)}")

            print("\nPrompt tokens with logprobs (echo=True):")
            for i, item in enumerate(logprobs.content[:len(prompt_token_ids)]):
                token_id = getattr(item, 'token_id', 'N/A')
                token = getattr(item, 'token', 'N/A')
                lp = getattr(item, 'logprob', 'N/A')
                print(f"  [{i}] token='{token}', token_id={token_id}, logprob={lp}")

            print("\nOutput tokens with logprobs:")
            for i, item in enumerate(logprobs.content[len(prompt_token_ids):len(prompt_token_ids)+5]):
                token_id = getattr(item, 'token_id', 'N/A')
                token = getattr(item, 'token', 'N/A')
                lp = getattr(item, 'logprob', 'N/A')
                print(f"  [{i}] token='{token}', token_id={token_id}, logprob={lp}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Skipped - FIREWORKS_API_KEY not set")

# =============================================================================
# Test 3: OpenRouter Completions API with string prompt
# =============================================================================

print("\n" + "=" * 60)
print("TEST 3: OpenRouter Completions API (string prompt)")
print("=" * 60)

if openrouter_client:
    try:
        response = openrouter_client.completions.create(
            model=OPENROUTER_MODEL,
            prompt=TEST_PROMPT,
            max_tokens=10,
            temperature=0.0,
            echo=True,
            logprobs=3,  # OpenRouter uses integer 0-5
            extra_body={"provider": {"only": ["fireworks"]}},
        )

        print(f"\nPrompt: '{TEST_PROMPT}'")
        print(f"Full text: '{response.choices[0].text}'")
        print(f"Finish reason: {response.choices[0].finish_reason}")

        logprobs = response.choices[0].logprobs
        print(f"\nLogprobs available: {logprobs is not None}")

        if logprobs:
            print(f"Logprobs type: {type(logprobs)}")
            if hasattr(logprobs, 'content') and logprobs.content:
                print(f"Has content array: Yes, length {len(logprobs.content)}")
                print("\nTokens with logprobs:")
                for i, item in enumerate(logprobs.content[:8]):
                    token_id = getattr(item, 'token_id', 'N/A')
                    token = getattr(item, 'token', 'N/A')
                    lp = getattr(item, 'logprob', 'N/A')
                    print(f"  [{i}] token='{token}', token_id={token_id}, logprob={lp}")
            elif hasattr(logprobs, 'tokens'):
                print(f"Has tokens array: {logprobs.tokens[:10] if logprobs.tokens else None}")
                print(f"Has token_logprobs: {logprobs.token_logprobs[:10] if hasattr(logprobs, 'token_logprobs') and logprobs.token_logprobs else None}")
            else:
                print(f"Logprobs raw: {logprobs}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Test 4: OpenRouter Completions API with token IDs
# =============================================================================

print("\n" + "=" * 60)
print("TEST 4: OpenRouter Completions API (token IDs as prompt)")
print("=" * 60)

if openrouter_client:
    try:
        tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
        prompt_token_ids = tokenizer.encode(TEST_PROMPT, add_special_tokens=False)
        print(f"Prompt: '{TEST_PROMPT}'")
        print(f"Token IDs: {prompt_token_ids}")

        response = openrouter_client.completions.create(
            model=OPENROUTER_MODEL,
            prompt=prompt_token_ids,  # Try sending token IDs
            max_tokens=10,
            temperature=0.0,
            echo=True,
            logprobs=3,
            extra_body={"provider": {"only": ["fireworks"]}},
        )

        print(f"\nFull text: '{response.choices[0].text}'")

        logprobs = response.choices[0].logprobs
        if logprobs:
            if hasattr(logprobs, 'content') and logprobs.content:
                print(f"\nLogprobs content length: {len(logprobs.content)}")
                print("\nTokens with logprobs:")
                for i, item in enumerate(logprobs.content[:8]):
                    token_id = getattr(item, 'token_id', 'N/A')
                    token = getattr(item, 'token', 'N/A')
                    lp = getattr(item, 'logprob', 'N/A')
                    print(f"  [{i}] token='{token}', token_id={token_id}, logprob={lp}")
            else:
                print(f"Logprobs: {logprobs}")
        else:
            print("No logprobs returned!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Test 5: OpenRouter with different providers
# =============================================================================

print("\n" + "=" * 60)
print("TEST 5: OpenRouter completions with various providers")
print("=" * 60)

providers_to_test = ["fireworks", "together", "deepinfra"]

if openrouter_client:
    for provider in providers_to_test:
        print(f"\n--- Provider: {provider} ---")
        try:
            response = openrouter_client.completions.create(
                model=OPENROUTER_MODEL,
                prompt=TEST_PROMPT,
                max_tokens=5,
                temperature=0.0,
                echo=True,
                logprobs=3,
                extra_body={"provider": {"only": [provider]}},
            )

            text = response.choices[0].text
            logprobs = response.choices[0].logprobs

            has_logprobs = logprobs is not None
            has_content = has_logprobs and hasattr(logprobs, 'content') and logprobs.content
            has_token_id = has_content and hasattr(logprobs.content[0], 'token_id')

            print(f"  Text: '{text[:50]}...'")
            print(f"  Has logprobs: {has_logprobs}")
            print(f"  Has content array: {has_content}")
            print(f"  Has token_id: {has_token_id}")

            # Check if echo worked (text should start with prompt)
            echo_worked = text.startswith(TEST_PROMPT)
            print(f"  Echo worked: {echo_worked}")

            if has_content:
                print(f"  Content length: {len(logprobs.content)}")

        except Exception as e:
            print(f"  Error: {e}")
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
Key questions to answer:
1. Does OpenRouter completions API support echo=True?
2. Does OpenRouter forward echo parameter to Fireworks?
3. Can we send token IDs as prompt through OpenRouter?
4. Do we get logprobs for echoed prompt tokens (not just output)?

If OpenRouter supports all of this, we can potentially replace
direct Fireworks API usage with OpenRouter + Fireworks provider.
""")
