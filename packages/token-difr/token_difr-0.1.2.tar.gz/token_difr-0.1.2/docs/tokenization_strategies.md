# Tokenization Strategies for Token Verification

When verifying LLM outputs, we need to convert the text response back into token IDs. This is surprisingly tricky because **tokenization is context-dependent** - the same text can tokenize differently depending on what comes before it.

## The Problem

When you generate via OpenRouter and verify via Fireworks:

```
OpenRouter → text response → ??? → token IDs → Fireworks verification
```

The challenge is the `???` step. How do you convert text back to the exact token IDs the model used?

### Why Naive Tokenization Fails

```python
# This seems obvious but is often WRONG
response_text = "Hello, world!"
token_ids = tokenizer.encode(response_text, add_special_tokens=False)
```

Problems:
1. **Leading space handling**: LLMs often generate ` Hello` (with leading space) but the API returns `"Hello"` (stripped)
2. **Special token boundaries**: Where the prompt ends and response begins affects tokenization
3. **`add_special_tokens`**: Using `True` adds BOS tokens you don't want

## Tokenization Strategies Tested

### 1. Baseline (add_special_tokens=True) ❌
```python
token_ids = tokenizer.encode(response_text, add_special_tokens=True)
```
- **Result**: ~94.6% exact match
- **Problem**: Adds unwanted BOS token, wrong token count

### 2. No Special Tokens ⚠️
```python
token_ids = tokenizer.encode(response_text, add_special_tokens=False)
```
- **Result**: ~96.8% exact match
- **Better**: No extra tokens, but still misses context

### 3. Full Sequence Encode (Best) ✅
```python
# Encode the FULL prompt + response together, then slice
prompt_text = tokenizer.decode(prompt_token_ids)
full_text = prompt_text + response_text
full_tokens = tokenizer.encode(full_text, add_special_tokens=False)

# Slice off the prompt portion
response_tokens = full_tokens[len(prompt_token_ids):]
```
- **Result**: ~97.3% exact match
- **Why it works**: The tokenizer sees the full context, so it handles boundaries correctly

### 4. Logprobs Token ID (Best when available) ✅✅
```python
# Extract token_ids directly from API logprobs
response = client.chat.completions.create(..., logprobs=True, top_logprobs=1)
token_ids = [item.token_id for item in response.choices[0].logprobs.content]
```
- **Result**: ~98.1% exact match
- **Why it works**: No tokenization needed - uses actual token IDs from the model
- **Limitation**: Only works for Fireworks via OpenRouter (for Llama models)

## Why Full Sequence Encode Works

BPE tokenizers are greedy and context-sensitive. Consider:

```python
tokenizer.encode("Hello")        # [9906]
tokenizer.encode(" Hello")       # [22691]  <- Different!
tokenizer.encode("Say Hello")    # [54312, 22691]  <- "Hello" = 22691 here
```

When you encode the response in isolation, you lose the context of what came before. The "full sequence" approach preserves this context:

```python
# The model generated this after the prompt
prompt = "<|user|>Say hi<|assistant|>"
response = "Hello!"

# WRONG: Encode response alone
tokenizer.encode("Hello!")  # Might get [9906, 0]

# RIGHT: Encode with context, then slice
full = prompt + "Hello!"
tokens = tokenizer.encode(full)[len(tokenizer.encode(prompt)):]  # Gets [22691, 0]
```

## Experimental Results Summary

Tested with Llama-3.3-70B-Instruct, 100 prompts, 200 max tokens:

| Strategy | Exact Match Rate |
|----------|------------------|
| Baseline (add_special_tokens=True) | 94.63% |
| No special tokens | 96.75% |
| Full sequence slice | 96.94% |
| Continuation encode | 97.31% |
| Byte-level align | 97.31% |
| **Logprobs token_id** | **98.09%** |

## Logprobs Availability by Provider

Tested via OpenRouter:

| Provider | Llama Logprobs | Qwen Logprobs |
|----------|----------------|---------------|
| fireworks | ✅ token_id | ❌ None |
| fireworks/fp8 | ❌ | ❌ |
| together | ❌ None | ❌ None |
| groq | ❌ None | ❌ |
| parasail/fp8 | ❌ | ❌ None |
| All others | ❌ | ❌ |

**Key finding**: Only `fireworks` (not `fireworks/fp8`) returns logprobs with `token_id`, and only for certain models.

For Together, you must call their API directly (not through OpenRouter) to get `token_ids` in the format `logprobs.token_ids` (a list).

## Recommended Approach

```python
def tokenize_response(prompt_token_ids: list[int], response_text: str, tokenizer) -> list[int]:
    """Best-effort tokenization using full sequence context."""
    # Decode prompt to text
    prompt_text = tokenizer.decode(prompt_token_ids, skip_special_tokens=False)

    # Encode full sequence
    full_text = prompt_text + response_text
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)

    # Slice off prompt
    return full_tokens[len(prompt_token_ids):]
```

Or if logprobs are available (Fireworks):

```python
def extract_token_ids_from_logprobs(logprobs) -> list[int]:
    """Extract token_ids from API logprobs when available."""
    if logprobs is None:
        return []

    # Fireworks via OpenRouter format
    if hasattr(logprobs, "content") and logprobs.content:
        return [item.token_id for item in logprobs.content if item.token_id is not None]

    # Together direct API format
    if hasattr(logprobs, "token_ids") and logprobs.token_ids:
        return list(logprobs.token_ids)

    return []
```

## Remaining ~2-3% Mismatch

Even with the best strategies, ~2-3% of tokens don't match. This is due to:

1. **Model non-determinism**: Even at temperature=0, some models have slight variations
2. **Provider differences**: Different quantization (fp8 vs bf16) can change outputs
3. **Chat template differences**: Provider may apply templates slightly differently
4. **Tokenizer version mismatches**: HuggingFace tokenizer may differ from deployed version

This baseline mismatch rate is important context when interpreting verification results.
