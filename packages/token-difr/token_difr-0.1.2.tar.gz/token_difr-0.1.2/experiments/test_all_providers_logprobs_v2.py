"""Test all providers for logprobs - comparing Llama vs Qwen."""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

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
]

MODELS = {
    "llama": "meta-llama/llama-3.3-70b-instruct",
    "qwen": "qwen/qwen3-235b-a22b-2507",
}

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)


def test_provider(provider: str, model: str) -> str:
    """Test if provider returns logprobs with token_id."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            temperature=0.0,
            logprobs=True,
            top_logprobs=1,
            extra_body={"provider": {"only": [provider]}},
        )

        logprobs = response.choices[0].logprobs

        if logprobs is None:
            return "❌ None"
        elif hasattr(logprobs, "content") and logprobs.content:
            first = logprobs.content[0]
            if hasattr(first, "token_id") and first.token_id is not None:
                return f"✅ {first.token_id}"
            else:
                return "⚠️ no id"
        elif hasattr(logprobs, "token_ids") and logprobs.token_ids:
            return f"✅ {logprobs.token_ids[0]}"
        else:
            return "⚠️ unknown"

    except Exception as e:
        return f"❌ err"


print(f"{'Provider':<20} | {'Llama':<12} | {'Qwen':<12}")
print("-" * 50)

for provider in PROVIDERS:
    llama_result = test_provider(provider, MODELS["llama"])
    qwen_result = test_provider(provider, MODELS["qwen"])
    print(f"{provider:<20} | {llama_result:<12} | {qwen_result:<12}")
