"""
Detailed Fireworks API test - understand the exact response format.
"""

import os
import json
import httpx
from dotenv import load_dotenv
from transformers import AutoTokenizer

load_dotenv()

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")

HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
TEST_PROMPT = "Hello, my name is"

print("=" * 70)
print("DETAILED FIREWORKS API TEST")
print("=" * 70)

tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, trust_remote_code=True)
prompt_token_ids = tokenizer.encode(TEST_PROMPT, add_special_tokens=False)
print(f"\nTest prompt: '{TEST_PROMPT}'")
print(f"Token IDs: {prompt_token_ids}")
print(f"Prompt length: {len(prompt_token_ids)} tokens")

if FIREWORKS_API_KEY:
    url = "https://api.fireworks.ai/inference/v1/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": FIREWORKS_MODEL,
        "prompt": prompt_token_ids,
        "max_tokens": 5,
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

        print(f"\n--- Full Response Structure ---")
        print(f"Top-level keys: {list(data.keys())}")
        print(f"Number of choices: {len(data['choices'])}")

        choice = data["choices"][0]
        print(f"\n--- Choice Structure ---")
        print(f"Choice keys: {list(choice.keys())}")
        print(f"Full text: '{choice.get('text', 'N/A')}'")
        print(f"Finish reason: {choice.get('finish_reason', 'N/A')}")

        logprobs = choice.get("logprobs")
        if logprobs:
            print(f"\n--- Logprobs Structure ---")
            print(f"Logprobs type: {type(logprobs)}")
            print(f"Logprobs keys: {list(logprobs.keys())}")

            if "content" in logprobs:
                content = logprobs["content"]
                print(f"\nContent array length: {len(content)}")
                print(f"Expected: {len(prompt_token_ids)} prompt + 5 output = {len(prompt_token_ids) + 5}")

                print(f"\n--- Prompt Tokens (first {len(prompt_token_ids)}) ---")
                for i, item in enumerate(content[:len(prompt_token_ids)]):
                    print(f"  [{i}] {json.dumps(item, indent=4)}")

                print(f"\n--- Output Tokens (after prompt) ---")
                for i, item in enumerate(content[len(prompt_token_ids):]):
                    idx = i + len(prompt_token_ids)
                    print(f"  [{idx}] {json.dumps(item, indent=4)}")

            # Check other keys
            for key in logprobs.keys():
                if key != "content":
                    print(f"\n{key}: {logprobs[key]}")

        # Check usage
        if "usage" in data:
            print(f"\n--- Usage ---")
            print(json.dumps(data["usage"], indent=2))
    else:
        print(f"Error: {response.text}")
else:
    print("FIREWORKS_API_KEY not set")
