"""
Test OpenRouter completions API using raw HTTP requests.

The OpenAI Python SDK appears to transform requests in ways that break
the completions API. Let's use direct HTTP calls instead.
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
print("RAW HTTP Request Tests - OpenRouter Completions API")
print("=" * 70)

# =============================================================================
# Test 1: Direct Fireworks API (raw HTTP)
# =============================================================================

print("\n" + "=" * 70)
print("TEST 1: Direct Fireworks API (raw HTTP)")
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
        "logprobs": 3,
        "top_logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"\nPrompt: '{TEST_PROMPT}'")
        print(f"Full text: '{choice['text']}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"\nLogprobs structure keys: {logprobs.keys()}")

            if "tokens" in logprobs:
                print(f"Tokens: {logprobs['tokens'][:10]}")
            if "token_logprobs" in logprobs:
                print(f"Token logprobs: {logprobs['token_logprobs'][:10]}")
            if "token_ids" in logprobs:
                print(f"Token IDs: {logprobs['token_ids'][:10]}")
            if "content" in logprobs:
                print(f"Content array length: {len(logprobs['content'])}")
                for i, item in enumerate(logprobs['content'][:8]):
                    print(f"  [{i}] {item}")
    else:
        print(f"Error {response.status_code}: {response.text}")
else:
    print("Skipped - FIREWORKS_API_KEY not set")

# =============================================================================
# Test 2: Fireworks API with token IDs (raw HTTP)
# =============================================================================

print("\n" + "=" * 70)
print("TEST 2: Fireworks API with token IDs (raw HTTP)")
print("=" * 70)

if FIREWORKS_API_KEY:
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
    prompt_token_ids = tokenizer.encode(TEST_PROMPT, add_special_tokens=False)
    print(f"Prompt: '{TEST_PROMPT}'")
    print(f"Token IDs: {prompt_token_ids}")

    url = "https://api.fireworks.ai/inference/v1/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": FIREWORKS_MODEL,
        "prompt": prompt_token_ids,  # Token IDs directly!
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": 3,
        "top_logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"\nFull text: '{choice['text']}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"\nLogprobs keys: {logprobs.keys()}")
            if "token_ids" in logprobs:
                print(f"Token IDs (all): {logprobs['token_ids']}")
                print(f"Prompt token IDs we sent: {prompt_token_ids}")
                print(f"Match: {logprobs['token_ids'][:len(prompt_token_ids)] == prompt_token_ids}")
            if "token_logprobs" in logprobs:
                print(f"\nToken logprobs (first {len(prompt_token_ids)} are prompt):")
                for i, (tok_id, lp) in enumerate(zip(logprobs.get('token_ids', []), logprobs.get('token_logprobs', []))):
                    is_prompt = i < len(prompt_token_ids)
                    marker = "PROMPT" if is_prompt else "OUTPUT"
                    print(f"  [{i}] {marker}: token_id={tok_id}, logprob={lp}")
                    if i >= 10:
                        print("  ...")
                        break
    else:
        print(f"Error {response.status_code}: {response.text}")
else:
    print("Skipped - FIREWORKS_API_KEY not set")

# =============================================================================
# Test 3: OpenRouter Completions API (raw HTTP)
# =============================================================================

print("\n" + "=" * 70)
print("TEST 3: OpenRouter Completions API (raw HTTP)")
print("=" * 70)

if OPENROUTER_API_KEY:
    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "prompt": TEST_PROMPT,
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": 3,
        "provider": {"only": ["fireworks"]},
    }

    print(f"Request payload: {json.dumps(payload, indent=2)}")

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"\nResponse status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"\nLogprobs keys: {logprobs.keys() if isinstance(logprobs, dict) else type(logprobs)}")
            if isinstance(logprobs, dict):
                for key in logprobs.keys():
                    val = logprobs[key]
                    if isinstance(val, list):
                        print(f"  {key}: {val[:5]}..." if len(val) > 5 else f"  {key}: {val}")
                    else:
                        print(f"  {key}: {val}")
        else:
            print("No logprobs returned")
    else:
        print(f"Error response: {response.text}")
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Test 4: OpenRouter Completions with token IDs (raw HTTP)
# =============================================================================

print("\n" + "=" * 70)
print("TEST 4: OpenRouter Completions with token IDs (raw HTTP)")
print("=" * 70)

if OPENROUTER_API_KEY:
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
    prompt_token_ids = tokenizer.encode(TEST_PROMPT, add_special_tokens=False)
    print(f"Prompt: '{TEST_PROMPT}'")
    print(f"Token IDs: {prompt_token_ids}")

    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "prompt": prompt_token_ids,
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": 3,
        "provider": {"only": ["fireworks"]},
    }

    print(f"Request payload: {json.dumps(payload, indent=2)}")

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"\nResponse status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"\nLogprobs available!")
            if isinstance(logprobs, dict):
                print(f"Logprobs keys: {logprobs.keys()}")
                if "token_ids" in logprobs:
                    print(f"Token IDs: {logprobs['token_ids']}")
    else:
        print(f"Error response: {response.text}")
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Test 5: OpenRouter without specifying provider
# =============================================================================

print("\n" + "=" * 70)
print("TEST 5: OpenRouter Completions (no provider specified)")
print("=" * 70)

if OPENROUTER_API_KEY:
    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "prompt": TEST_PROMPT,
        "max_tokens": 10,
        "temperature": 0.0,
        "logprobs": 3,
        # No echo, no provider - simplest request
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"Logprobs type: {type(logprobs)}")
            if isinstance(logprobs, dict):
                print(f"Logprobs keys: {logprobs.keys()}")
        else:
            print("No logprobs in response")
    else:
        print(f"Error: {response.text}")
else:
    print("Skipped - OPENROUTER_API_KEY not set")

# =============================================================================
# Test 6: OpenRouter with top_logprobs
# =============================================================================

print("\n" + "=" * 70)
print("TEST 6: OpenRouter Completions with top_logprobs")
print("=" * 70)

if OPENROUTER_API_KEY:
    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "prompt": TEST_PROMPT,
        "max_tokens": 10,
        "temperature": 0.0,
        "logprobs": True,  # Try boolean
        "top_logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"Logprobs: {json.dumps(logprobs, indent=2)[:500]}")
        else:
            print("No logprobs in response")
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
