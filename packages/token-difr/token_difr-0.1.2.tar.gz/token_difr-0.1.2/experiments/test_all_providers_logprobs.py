"""Test all providers from audit_demonstration for logprobs support."""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# All providers from audit_demonstration.py (including commented ones)
PROVIDERS = [
    "parasail/fp8",
    "wandb/bf16",
    "deepinfra/fp8",
    "novita/fp8",
    "siliconflow/fp8",
    "together",
    "fireworks/fp8",
    "fireworks",
    "cerebras",
    "alibaba",
    "groq",
    "lepton",
]

MODEL = "qwen/qwen3-235b-a22b-2507"  # OpenRouter format

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

print(f"Testing logprobs support for {MODEL}")
print(f"{'Provider':<20} | {'Logprobs?':<12} | {'Format':<30} | Notes")
print("-" * 90)

for provider in PROVIDERS:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            temperature=0.0,
            logprobs=True,
            top_logprobs=1,
            extra_body={"provider": {"only": [provider]}},
        )

        content = response.choices[0].message.content or ""
        logprobs = response.choices[0].logprobs

        if logprobs is None:
            print(f"{provider:<20} | {'❌ None':<12} | {'N/A':<30} | content: {content[:20]}")
        elif hasattr(logprobs, "content") and logprobs.content:
            first = logprobs.content[0]
            has_token_id = hasattr(first, "token_id") and first.token_id is not None
            if has_token_id:
                print(f"{provider:<20} | {'✅ Yes':<12} | {'content[i].token_id':<30} | id={first.token_id}")
            else:
                print(f"{provider:<20} | {'⚠️ Partial':<12} | {'content but no token_id':<30} | token='{first.token}'")
        elif hasattr(logprobs, "token_ids") and logprobs.token_ids:
            print(f"{provider:<20} | {'✅ Yes':<12} | {'token_ids list':<30} | ids={logprobs.token_ids[:3]}...")
        else:
            print(f"{provider:<20} | {'⚠️ Unknown':<12} | {str(type(logprobs)):<30} | {str(logprobs)[:50]}")

    except Exception as e:
        error_msg = str(e)[:60]
        print(f"{provider:<20} | {'❌ Error':<12} | {'N/A':<30} | {error_msg}")
