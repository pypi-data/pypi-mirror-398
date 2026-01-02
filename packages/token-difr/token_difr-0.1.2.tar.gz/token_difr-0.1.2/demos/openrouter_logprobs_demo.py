# %% [markdown]
# # Logprobs Demo: Getting token_ids from LLM APIs
#
# **Key finding**: Different providers return logprobs in different formats!
#
# | Provider | Via | Format | Works? |
# |----------|-----|--------|--------|
# | Fireworks | OpenRouter | `logprobs.content[i].token_id` | ✅ |
# | Together | Direct API | `logprobs.token_ids` (list) | ✅ |
# | Together | OpenRouter | N/A | ❌ (logprobs not forwarded) |
# | Groq | OpenRouter | N/A | ❌ (logprobs not forwarded) |

# %%
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# %% [markdown]
# ## Method 1: Fireworks via OpenRouter
#
# Fireworks returns `token_id` in each logprob item when accessed through OpenRouter.

# %%
openrouter_client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

# %%
# Request with logprobs via OpenRouter -> Fireworks
response = openrouter_client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "Say hi"}],
    max_tokens=10,
    temperature=0.0,
    logprobs=True,
    top_logprobs=1,
    extra_body={"provider": {"only": ["fireworks"]}},
)

print("Content:", response.choices[0].message.content)

# %%
# Extract token_ids from Fireworks logprobs
logprobs = response.choices[0].logprobs

print("\nFireworks logprobs format:")
print(f"  logprobs.content exists: {logprobs.content is not None}")

if logprobs.content:
    print(f"  Number of tokens: {len(logprobs.content)}")
    print("\n  Token details:")
    token_ids = []
    for item in logprobs.content:
        print(f"    token='{item.token}' -> token_id={item.token_id}")
        token_ids.append(item.token_id)
    print(f"\n  All token_ids: {token_ids}")

# %% [markdown]
# ## Method 2: Together Direct API
#
# Together returns `token_ids` as a separate list (not in `content`).
# **Note**: This does NOT work through OpenRouter - you must call Together directly.

# %%
together_client = OpenAI(
    api_key=os.environ.get("TOGETHER_API_KEY", ""),
    base_url="https://api.together.xyz/v1",
)

# %%
# Request with logprobs directly to Together
response = together_client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Say hi"}],
    max_tokens=10,
    temperature=0.0,
    logprobs=True,
    top_logprobs=1,
)

print("Content:", response.choices[0].message.content)

# %%
# Extract token_ids from Together logprobs (different format!)
logprobs = response.choices[0].logprobs

print("\nTogether logprobs format:")
print(f"  logprobs.content: {logprobs.content}")  # This is None!
print(f"  logprobs.token_ids: {logprobs.token_ids}")  # Token IDs are here!
print(f"  logprobs.tokens: {logprobs.tokens}")  # Token strings

token_ids = logprobs.token_ids
print(f"\n  All token_ids: {token_ids}")

# %% [markdown]
# ## Why OpenRouter doesn't forward Together/Groq logprobs
#
# OpenRouter acts as a proxy and normalizes responses. Some providers (Together, Groq)
# return logprobs in non-standard formats that OpenRouter doesn't translate.
#
# **Solution**: For providers other than Fireworks, call their APIs directly.

# %%
# Demonstrate: Together via OpenRouter = no logprobs
response = openrouter_client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "Say hi"}],
    max_tokens=10,
    temperature=0.0,
    logprobs=True,
    top_logprobs=1,
    extra_body={"provider": {"only": ["together"]}},
)

print("Together via OpenRouter:")
print(f"  Content: {response.choices[0].message.content}")
print(f"  logprobs: {response.choices[0].logprobs}")  # None!

# %% [markdown]
# ## Unified extraction function

# %%
def extract_token_ids(logprobs) -> list[int]:
    """Extract token_ids from logprobs, handling different provider formats."""
    if logprobs is None:
        return []

    # Format 1: Fireworks via OpenRouter (token_id in each content item)
    if hasattr(logprobs, "content") and logprobs.content:
        return [item.token_id for item in logprobs.content if item.token_id is not None]

    # Format 2: Together direct API (token_ids as separate list)
    if hasattr(logprobs, "token_ids") and logprobs.token_ids:
        return list(logprobs.token_ids)

    return []


# %%
# Test with Fireworks
response = openrouter_client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "Hi"}],
    max_tokens=5,
    temperature=0.0,
    logprobs=True,
    top_logprobs=1,
    extra_body={"provider": {"only": ["fireworks"]}},
)
print("Fireworks token_ids:", extract_token_ids(response.choices[0].logprobs))

# Test with Together direct
response = together_client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Hi"}],
    max_tokens=5,
    temperature=0.0,
    logprobs=True,
    top_logprobs=1,
)
print("Together token_ids:", extract_token_ids(response.choices[0].logprobs))

# %% [markdown]
# ## Verify token_ids with tokenizer

# %%
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "meta-llama/Llama-3.3-70B-Instruct", trust_remote_code=True
)

# Get token_ids from Fireworks
response = openrouter_client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=20,
    temperature=0.0,
    logprobs=True,
    top_logprobs=1,
    extra_body={"provider": {"only": ["fireworks"]}},
)

content = response.choices[0].message.content
api_token_ids = extract_token_ids(response.choices[0].logprobs)
local_token_ids = tokenizer.encode(content, add_special_tokens=False)

print(f"Content: {content}")
print(f"API token_ids:   {api_token_ids}")
print(f"Local token_ids: {local_token_ids}")
print(f"Match: {api_token_ids == local_token_ids}")

# Decode both
print(f"\nDecoded from API:   '{tokenizer.decode(api_token_ids)}'")
print(f"Decoded from local: '{tokenizer.decode(local_token_ids)}'")
