"""
Final comprehensive test of OpenRouter completions API capabilities.

KEY FINDINGS SO FAR:
- OpenRouter converts completions API requests to chat/messages format internally
- This breaks routing to providers that expect raw completions (like Fireworks)
- Token ID prompts are not supported by OpenRouter
"""

import os
import json
import httpx
from dotenv import load_dotenv
from transformers import AutoTokenizer

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")

HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"

TEST_PROMPT = "Hello, my name is"

print("=" * 70)
print("FINAL COMPREHENSIVE TEST - OpenRouter vs Fireworks")
print("=" * 70)

# =============================================================================
# Test 1: Direct Fireworks API - String Prompt (CORRECT FORMAT)
# =============================================================================

print("\n" + "=" * 70)
print("TEST 1: Direct Fireworks - String Prompt + echo + logprobs")
print("=" * 70)

if FIREWORKS_API_KEY:
    url = "https://api.fireworks.ai/inference/v1/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": FIREWORKS_MODEL,
        "prompt": TEST_PROMPT,
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": True,  # Must be True (boolean)
        "top_logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice['text']}'")
        print(f"Echo worked: {choice['text'].startswith(TEST_PROMPT)}")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"\nLogprobs keys: {list(logprobs.keys())}")
            if "token_ids" in logprobs:
                print(f"Token IDs: {logprobs['token_ids']}")
            if "tokens" in logprobs:
                print(f"Tokens: {logprobs['tokens']}")
            if "token_logprobs" in logprobs:
                print(f"Token logprobs: {logprobs['token_logprobs']}")
    else:
        print(f"Error: {response.text}")
else:
    print("Skipped - FIREWORKS_API_KEY not set")

# =============================================================================
# Test 2: Direct Fireworks API - Token IDs Prompt
# =============================================================================

print("\n" + "=" * 70)
print("TEST 2: Direct Fireworks - Token IDs Prompt + echo + logprobs")
print("=" * 70)

if FIREWORKS_API_KEY:
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
    prompt_token_ids = tokenizer.encode(TEST_PROMPT, add_special_tokens=False)
    print(f"Prompt text: '{TEST_PROMPT}'")
    print(f"Token IDs: {prompt_token_ids}")

    url = "https://api.fireworks.ai/inference/v1/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": FIREWORKS_MODEL,
        "prompt": prompt_token_ids,
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": True,
        "top_logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice['text']}'")

        logprobs = choice.get("logprobs")
        if logprobs and "token_ids" in logprobs:
            returned_ids = logprobs["token_ids"]
            prompt_part = returned_ids[:len(prompt_token_ids)]
            output_part = returned_ids[len(prompt_token_ids):]

            print(f"\nReturned token IDs: {returned_ids}")
            print(f"Prompt part: {prompt_part}")
            print(f"Output part: {output_part}")
            print(f"Prompt IDs match: {prompt_part == prompt_token_ids}")

            if "token_logprobs" in logprobs:
                lps = logprobs["token_logprobs"]
                print(f"\nPrompt logprobs: {lps[:len(prompt_token_ids)]}")
                print(f"Output logprobs: {lps[len(prompt_token_ids):]}")
    else:
        print(f"Error: {response.text}")
else:
    print("Skipped - FIREWORKS_API_KEY not set")

# =============================================================================
# Test 3: OpenRouter - All possible providers for completions logprobs
# =============================================================================

print("\n" + "=" * 70)
print("TEST 3: OpenRouter Completions - Test multiple providers")
print("=" * 70)

providers_to_test = [
    None,  # Default routing
    "openai",
    "fireworks",
    "together",
    "deepinfra",
    "groq",
]

if OPENROUTER_API_KEY:
    for provider in providers_to_test:
        provider_name = provider if provider else "default"
        print(f"\n--- Provider: {provider_name} ---")

        url = "https://openrouter.ai/api/v1/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": OPENROUTER_MODEL if provider != "openai" else "openai/gpt-3.5-turbo-instruct",
            "prompt": TEST_PROMPT,
            "max_tokens": 5,
            "temperature": 0.0,
            "logprobs": True,
            "top_logprobs": 3,
        }
        if provider:
            payload["provider"] = {"only": [provider]}

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                choice = data["choices"][0]
                text = choice.get("text", "N/A")
                logprobs = choice.get("logprobs")

                has_logprobs = logprobs is not None
                has_token_ids = has_logprobs and isinstance(logprobs, dict) and "token_ids" in logprobs

                print(f"  Status: 200 OK")
                print(f"  Text: '{text[:40]}...'")
                print(f"  Has logprobs: {has_logprobs}")
                print(f"  Has token_ids: {has_token_ids}")

                if has_logprobs and isinstance(logprobs, dict):
                    print(f"  Logprobs keys: {list(logprobs.keys())}")
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", response.text)[:100]
                print(f"  Status: {response.status_code}")
                print(f"  Error: {error_msg}")
        except Exception as e:
            print(f"  Exception: {e}")
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Test 4: OpenRouter Chat Completions (not completions) with logprobs
# =============================================================================

print("\n" + "=" * 70)
print("TEST 4: OpenRouter Chat Completions with logprobs (Fireworks)")
print("=" * 70)

if OPENROUTER_API_KEY:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10,
        "temperature": 0.0,
        "logprobs": True,
        "top_logprobs": 3,
        "provider": {"only": ["fireworks"]},
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        content = choice.get("message", {}).get("content", "N/A")
        logprobs = choice.get("logprobs")

        print(f"Content: '{content}'")
        print(f"Has logprobs: {logprobs is not None}")

        if logprobs:
            print(f"Logprobs type: {type(logprobs)}")
            if isinstance(logprobs, dict):
                print(f"Logprobs keys: {list(logprobs.keys())}")
                if "content" in logprobs and logprobs["content"]:
                    print(f"Content array length: {len(logprobs['content'])}")
                    for i, item in enumerate(logprobs["content"][:3]):
                        print(f"  [{i}] {item}")
    else:
        print(f"Error: {response.text}")
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("SUMMARY OF FINDINGS")
print("=" * 70)
print("""
DIRECT FIREWORKS API:
- Supports prompt as string OR token IDs
- Supports echo=True to include prompt in response
- Returns logprobs for ALL tokens (prompt + output) with echo=True
- Returns token_ids in logprobs response

OPENROUTER COMPLETIONS API:
- Converts completions requests to chat/messages internally (!)
- This breaks routing to providers expecting raw completions
- Does NOT support token ID prompts (returns "Input required")
- logprobs parameter often ignored or not forwarded

OPENROUTER CHAT COMPLETIONS API:
- logprobs ARE returned when using Fireworks provider
- But only for OUTPUT tokens, not prompt tokens
- No echo functionality (echo is a completions API feature)
- token_id available in logprobs.content items

CONCLUSION:
Cannot replace Fireworks API with OpenRouter for prompt token logprobs.
OpenRouter's completions API is essentially a facade over chat completions.
""")
