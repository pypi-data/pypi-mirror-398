"""Test logprobs from providers directly (not through OpenRouter)."""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Test Together directly
print("=" * 60)
print("Testing Together API directly...")
print("=" * 60)
try:
    together_key = os.environ.get("TOGETHER_API_KEY", "")
    if not together_key:
        print("TOGETHER_API_KEY not set")
    else:
        together_client = OpenAI(
            api_key=together_key,
            base_url="https://api.together.xyz/v1",
        )

        response = together_client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=5,
            temperature=0.0,
            logprobs=True,
            top_logprobs=1,
        )

        print(f"Content: {response.choices[0].message.content}")
        logprobs = response.choices[0].logprobs
        print(f"logprobs is None: {logprobs is None}")
        if logprobs and hasattr(logprobs, "content") and logprobs.content:
            first = logprobs.content[0]
            print(f"First token: {first}")
            print(f"Has token_id: {hasattr(first, 'token_id')}, value: {getattr(first, 'token_id', 'N/A')}")
        else:
            print(f"logprobs object: {logprobs}")
except Exception as e:
    print(f"Together direct error: {e}")

print()
print("=" * 60)
print("Testing Groq API directly...")
print("=" * 60)
try:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        print("GROQ_API_KEY not set")
    else:
        groq_client = OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
        )

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=5,
            temperature=0.0,
            logprobs=True,
            top_logprobs=1,
        )

        print(f"Content: {response.choices[0].message.content}")
        logprobs = response.choices[0].logprobs
        print(f"logprobs is None: {logprobs is None}")
        if logprobs and hasattr(logprobs, "content") and logprobs.content:
            first = logprobs.content[0]
            print(f"First token: {first}")
            print(f"Has token_id: {hasattr(first, 'token_id')}, value: {getattr(first, 'token_id', 'N/A')}")
        else:
            print(f"logprobs object: {logprobs}")
except Exception as e:
    print(f"Groq direct error: {e}")
