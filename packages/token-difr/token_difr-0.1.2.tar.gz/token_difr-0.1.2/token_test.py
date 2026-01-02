# %%

a = 0.01

if not a:
    print("a is 0")

# %%

from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "openai/gpt-oss-120b"
# model_name = "moonshotai/Kimi-K2-Thinking"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
messages = [
    {"role": "user", "content": "Explain what MXFP4 quantization is."},
]

inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    return_tensors="pt",
    return_dict=True,
)

# %%
print(inputs)
# %%
