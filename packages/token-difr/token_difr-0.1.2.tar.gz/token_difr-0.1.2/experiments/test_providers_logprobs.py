"""Test which providers return token_id in logprobs."""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

providers = ["fireworks", "together", "groq"]

for provider in providers:
    print()
    print("=" * 60)
    print(f"Provider: {provider}")
    print("=" * 60)

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=5,
            temperature=0.0,
            logprobs=True,
            top_logprobs=1,
            extra_body={"provider": {"only": [provider]}},
        )

        print(f"Content: {response.choices[0].message.content}")

        logprobs = response.choices[0].logprobs
        if logprobs is None:
            print("logprobs is None!")
            continue

        if not hasattr(logprobs, "content") or logprobs.content is None:
            print("logprobs.content is None!")
            print(f"logprobs object: {logprobs}")
            continue

        print(f"Number of tokens: {len(logprobs.content)}")

        if logprobs.content:
            first = logprobs.content[0]
            print(f"First token object: {first}")
            print(f"Has token_id attr: {hasattr(first, 'token_id')}")
            if hasattr(first, "token_id"):
                print(f"token_id value: {first.token_id}")
    except Exception as e:
        print(f"Error: {e}")
