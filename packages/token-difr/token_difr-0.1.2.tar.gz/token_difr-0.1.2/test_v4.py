# %%

from openai import OpenAI
import os
from dotenv import load_dotenv
import os

load_dotenv()  # This loads .env into os.environ

# api_key = os.environ["OPENROUTER_API_KEY"]

# client = OpenAI(
#     api_key=os.environ["OPENROUTER_API_KEY"],
#     base_url="https://openrouter.ai/api/v1",
# )

# client = OpenAI(
#     api_key=os.environ["TOGETHER_API_KEY"],
#     base_url="https://api.together.xyz/v1",
# )

client = OpenAI(api_key=os.environ.get("FIREWORKS_API_KEY"), base_url="https://api.fireworks.ai/inference/v1")

model = "meta-llama/Llama-3.3-70B-Instruct"
# fireworks model
model = "fireworks/llama-v3p3-70b-instruct"
# model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

# model = "fireworks/kimi-k2-thinking"

resp = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "Hello"},
    ],
    logprobs=True,
    # top_logprobs=1,
    max_tokens=1000,
    # echo=True,
    extra_body={"echo": True, "top_logprobs": 1},
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
print(resp.choices[0].message.content)
print(resp.choices[0].message.model_dump().keys())
print(resp.choices[0].message.reasoning_content)

# %%
print(resp.choices[0].logprobs.content[0].model_dump().keys())

print(len(resp.choices[0].logprobs.content))
print(resp.choices[0].logprobs.content[1])
# %%
tokens = []

for content in resp.choices[0].logprobs.content:
    tokens.append(content.token)

print(tokens)
# %%
