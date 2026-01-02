"""
Test alternative providers for prompt logprobs.

Based on research:
- Together AI: supports completions with logprobs and token_ids
- DeepInfra: supports echo + logprobs for completions (not chat)
"""

import os
import json
import httpx
from dotenv import load_dotenv
from transformers import AutoTokenizer

load_dotenv()

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY")
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")

HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
TEST_PROMPT = "Hello, my name is"

print("=" * 70)
print("ALTERNATIVE PROVIDERS - Prompt Logprobs Test")
print("=" * 70)

tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
prompt_token_ids = tokenizer.encode(TEST_PROMPT, add_special_tokens=False)
print(f"\nTest prompt: '{TEST_PROMPT}'")
print(f"Token IDs: {prompt_token_ids}")

# =============================================================================
# Test 1: Together AI Completions API
# =============================================================================

print("\n" + "=" * 70)
print("TEST 1: Together AI Completions API")
print("=" * 70)

if TOGETHER_API_KEY:
    together_model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

    # Test 1a: String prompt with echo and logprobs
    print("\n--- 1a: String prompt + echo + logprobs ---")
    url = "https://api.together.xyz/v1/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": together_model,
        "prompt": TEST_PROMPT,
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"Logprobs keys: {list(logprobs.keys())}")
            if "token_ids" in logprobs:
                print(f"Token IDs: {logprobs['token_ids']}")
            if "tokens" in logprobs:
                print(f"Tokens: {logprobs['tokens'][:15]}")
            if "token_logprobs" in logprobs:
                print(f"Token logprobs: {logprobs['token_logprobs'][:15]}")
        else:
            print("No logprobs returned")
    else:
        print(f"Error: {response.text}")

    # Test 1b: Token IDs as prompt
    print("\n--- 1b: Token IDs as prompt + echo + logprobs ---")
    payload["prompt"] = prompt_token_ids

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs and "token_ids" in logprobs:
            print(f"Returned token IDs: {logprobs['token_ids']}")
            prompt_part = logprobs['token_ids'][:len(prompt_token_ids)]
            print(f"Prompt IDs match: {prompt_part == prompt_token_ids}")
    else:
        print(f"Error: {response.text}")
else:
    print("Skipped - TOGETHER_API_KEY not set")

# =============================================================================
# Test 2: DeepInfra Completions API
# =============================================================================

print("\n" + "=" * 70)
print("TEST 2: DeepInfra Completions API")
print("=" * 70)

if DEEPINFRA_API_KEY:
    deepinfra_model = "meta-llama/Llama-3.3-70B-Instruct"

    # Test 2a: String prompt with echo and logprobs
    print("\n--- 2a: String prompt + echo + logprobs ---")
    url = "https://api.deepinfra.com/v1/openai/completions"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": deepinfra_model,
        "prompt": TEST_PROMPT,
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"Logprobs keys: {list(logprobs.keys())}")
            if "token_ids" in logprobs:
                print(f"Token IDs: {logprobs['token_ids']}")
            if "tokens" in logprobs:
                print(f"Tokens: {logprobs['tokens'][:15]}")
            if "token_logprobs" in logprobs:
                print(f"Token logprobs: {logprobs['token_logprobs'][:15]}")
        else:
            print("No logprobs returned")
    else:
        print(f"Error: {response.text}")

    # Test 2b: Token IDs as prompt
    print("\n--- 2b: Token IDs as prompt + echo + logprobs ---")
    payload["prompt"] = prompt_token_ids

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs and "token_ids" in logprobs:
            print(f"Returned token IDs: {logprobs['token_ids']}")
    else:
        print(f"Error: {response.text}")
else:
    print("Skipped - DEEPINFRA_API_KEY not set")

# =============================================================================
# Test 3: Fireworks (baseline comparison)
# =============================================================================

print("\n" + "=" * 70)
print("TEST 3: Fireworks (baseline)")
print("=" * 70)

if FIREWORKS_API_KEY:
    fireworks_model = "accounts/fireworks/models/llama-v3p3-70b-instruct"

    url = "https://api.fireworks.ai/inference/v1/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": fireworks_model,
        "prompt": prompt_token_ids,
        "max_tokens": 10,
        "temperature": 0.0,
        "echo": True,
        "logprobs": True,
        "top_logprobs": 3,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        choice = data["choices"][0]
        print(f"Full text: '{choice.get('text', 'N/A')}'")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"Logprobs keys: {list(logprobs.keys())}")
            if "token_ids" in logprobs:
                ids = logprobs['token_ids']
                print(f"Token IDs: {ids}")
                print(f"Prompt IDs match: {ids[:len(prompt_token_ids)] == prompt_token_ids}")
            if "token_logprobs" in logprobs:
                lps = logprobs['token_logprobs']
                print(f"Prompt token logprobs: {lps[:len(prompt_token_ids)]}")
                print(f"Output token logprobs: {lps[len(prompt_token_ids):]}")
    else:
        print(f"Error: {response.text}")
else:
    print("Skipped - FIREWORKS_API_KEY not set")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("FEATURE COMPARISON SUMMARY")
print("=" * 70)
print("""
Required features for token-difr verification:
1. Send prompt as token IDs (to avoid tokenization mismatches)
2. Use echo=True to get prompt included in response
3. Get logprobs for prompt tokens (with token_ids)
4. Get top_logprobs alternatives for each position

Provider | Token ID Prompt | Echo | Prompt Logprobs | Token IDs
---------|-----------------|------|-----------------|----------
Fireworks| Yes            | Yes  | Yes             | Yes
Together | ?              | ?    | ?               | ?
DeepInfra| ?              | ?    | ?               | ?
OpenRouter| No            | Broken| No             | Partial
""")
