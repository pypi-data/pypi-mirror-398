# %%

from together import Together
import json

client = Together()

completion = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "What are the top 3 things to do in New York?"},
    ],
    echo=True,
    max_tokens=10,
    logprobs=1,
)

print(json.dumps(completion.model_dump(), indent=1))
# %%
from openai import OpenAI
import os
from dotenv import load_dotenv
import os

load_dotenv()  # This loads .env into os.environ

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

# client = OpenAI(
#     api_key=os.environ["TOGETHER_API_KEY"],
#     base_url="https://api.together.xyz/v1",
# )

# client = OpenAI(api_key=os.environ.get("FIREWORKS_API_KEY"), base_url="https://api.fireworks.ai/inference/v1")

model = "meta-llama/Llama-3.3-70B-Instruct"
# fireworks model
# model = "fireworks/llama-v3p3-70b-instruct"
# model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

resp = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "What are the top 3 things to do in New York?"},
    ],
    logprobs=True,
    top_logprobs=5,
    max_tokens=10,
    # echo=True,
    extra_body={"echo": True, "provider": {"order": ["fireworks"]}},
    # extra_body={
    # "provider": {
    # "order": ["together"],  # or ["fireworks"]
    # "allow_fallbacks": False,
    # "require_parameters": True,
    # }
    # },
)
print(resp.choices[0].logprobs)

# %%
print(resp)
# %%

# print(resp.choices[0].logprobs)
print(len(resp.choices[0].logprobs))
# %%
from fireworks import Fireworks

client = Fireworks()

model = "accounts/fireworks/models/llama-v3p3-70b-instruct"
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hello"},
    {"role": "user", "content": "What are the top 3 things to do in New York?"},
]

response = client.chat.completions.create(model=model, messages=messages)

print(response.choices[0].message.content)
# %%
