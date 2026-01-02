# %% [markdown]
# # Tinker Verification Explorer
# Interactive script to investigate match rate discrepancies

# %%
import os
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from transformers import AutoTokenizer

from token_difr import TokenSequence, compute_metrics_summary, verify_outputs_tinker

# Load .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# %%
# Configuration
# MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
MODEL_NAME = "Qwen/Qwen3-8B"

TEST_PROMPTS = [
    "What is the capital of France?",
    "Explain photosynthesis in simple terms.",
    "Write a haiku about the ocean.",
    "What is 2 + 2?",
    "List three primary colors.",
    "Describe the water cycle.",
    "What causes rainbows?",
    "Explain gravity to a child.",
]

# Sampling parameters
TEMPERATURE = 0.0
TOP_K = 20  # Tinker limits topk logprobs to 20
TOP_P = 0.95
SEED = 42
MAX_TOKENS = 100

# %%
# Initialize Tinker client
import tinker

api_key = os.environ.get("TINKER_API_KEY")
if not api_key:
    raise ValueError("TINKER_API_KEY environment variable not set")

service_client = tinker.ServiceClient(api_key=api_key)
sampling_client = service_client.create_sampling_client(base_model=MODEL_NAME)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
vocab_size = len(tokenizer)
print(f"Vocab size: {vocab_size}")


# %%
# Generate outputs
def generate_single_output(prompt, temperature, top_k, top_p, seed, max_tokens):
    """Generate a single output and return detailed info."""
    messages = [{"role": "user", "content": prompt}]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    prompt_token_ids = tokenizer.encode(rendered, add_special_tokens=False)

    prompt_input = tinker.ModelInput.from_ints(prompt_token_ids)
    params = tinker.SamplingParams(
        max_tokens=max_tokens,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        seed=seed,
    )
    result = sampling_client.sample(
        prompt=prompt_input,
        sampling_params=params,
        num_samples=1,
    ).result()

    generated_tokens = result.sequences[0].tokens
    return TokenSequence(
        prompt_token_ids=prompt_token_ids,
        output_token_ids=list(generated_tokens),
    )


print("Generating outputs...")
outputs = [generate_single_output(p, 1.0, TOP_K, TOP_P, SEED, MAX_TOKENS) for p in TEST_PROMPTS]
print(f"Generated {len(outputs)} sequences, {sum(len(o.output_token_ids) for o in outputs)} total tokens")

# %%
# Verify outputs
print("Verifying outputs...")
results = verify_outputs_tinker(
    outputs,
    sampling_client=sampling_client,
    vocab_size=vocab_size,
    temperature=TEMPERATURE,
    top_k=TOP_K,
    top_p=TOP_P,
    seed=SEED,
)

summary = compute_metrics_summary(results)
print(f"\nSummary: {summary}")

# %%
# Flatten results for analysis
all_metrics = []
for seq_idx, seq_results in enumerate(results):
    for tok_idx, m in enumerate(seq_results):
        all_metrics.append(
            {
                "seq_idx": seq_idx,
                "tok_idx": tok_idx,
                "exact_match": m.exact_match,
                "prob": m.prob,
                "margin": m.margin,
                "logit_rank": m.logit_rank,
                "gumbel_rank": m.gumbel_rank,
                "token_id": outputs[seq_idx].output_token_ids[tok_idx],
            }
        )

print(f"Total metrics: {len(all_metrics)}")

# %%
# Analyze logit ranks
logit_ranks = [m["logit_rank"] for m in all_metrics]
rank_counts = Counter(logit_ranks)

print("Logit rank distribution:")
for rank in sorted(rank_counts.keys())[:10]:
    count = rank_counts[rank]
    pct = count / len(logit_ranks) * 100
    print(f"  Rank {int(rank)}: {count} ({pct:.1f}%)")

# %%
# Plot logit rank distribution
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Logit rank histogram
ax = axes[0, 0]
ranks_array = np.array(logit_ranks)
ax.hist(ranks_array[ranks_array < 20], bins=20, edgecolor="black", alpha=0.7)
ax.set_xlabel("Logit Rank")
ax.set_ylabel("Count")
ax.set_title(f"Logit Rank Distribution (temp={TEMPERATURE})")
ax.axvline(x=0.5, color="red", linestyle="--", label="Rank 0/1 boundary")
ax.legend()

# Probability distribution
ax = axes[0, 1]
probs = [m["prob"] for m in all_metrics]
ax.hist(probs, bins=50, edgecolor="black", alpha=0.7)
ax.set_xlabel("Token Probability")
ax.set_ylabel("Count")
ax.set_title("Probability Distribution of Generated Tokens")

# Match vs non-match probability comparison
ax = axes[1, 0]
match_probs = [m["prob"] for m in all_metrics if m["exact_match"]]
nonmatch_probs = [m["prob"] for m in all_metrics if not m["exact_match"]]
ax.hist(match_probs, bins=30, alpha=0.6, label=f"Match (n={len(match_probs)})", edgecolor="black")
ax.hist(nonmatch_probs, bins=30, alpha=0.6, label=f"Non-match (n={len(nonmatch_probs)})", edgecolor="black")
ax.set_xlabel("Token Probability")
ax.set_ylabel("Count")
ax.set_title("Probability: Match vs Non-Match")
ax.legend()

# Rank for non-matches
ax = axes[1, 1]
nonmatch_ranks = [m["logit_rank"] for m in all_metrics if not m["exact_match"]]
if nonmatch_ranks:
    ax.hist(nonmatch_ranks, bins=range(0, min(21, int(max(nonmatch_ranks)) + 2)), edgecolor="black", alpha=0.7)
ax.set_xlabel("Logit Rank")
ax.set_ylabel("Count")
ax.set_title("Logit Ranks of Non-Matching Tokens")

plt.tight_layout()
plt.savefig("tinker_verification_analysis.png", dpi=150)
plt.show()

# %%
# Detailed look at non-matches
print("\n=== Non-matching tokens ===")
nonmatches = [m for m in all_metrics if not m["exact_match"]]
print(f"Total non-matches: {len(nonmatches)} / {len(all_metrics)} ({len(nonmatches) / len(all_metrics) * 100:.1f}%)")

print("\nFirst 20 non-matches:")
for m in nonmatches[:20]:
    token_str = tokenizer.decode([m["token_id"]])
    print(
        f"  Seq {m['seq_idx']}, Tok {m['tok_idx']}: rank={int(m['logit_rank'])}, prob={m['prob']:.4f}, token='{token_str}'"
    )

# %%
# Look at rank distribution for non-matches
print("\nRank distribution for non-matching tokens:")
nonmatch_rank_counts = Counter([int(m["logit_rank"]) for m in nonmatches])
for rank in sorted(nonmatch_rank_counts.keys())[:10]:
    count = nonmatch_rank_counts[rank]
    print(f"  Rank {rank}: {count}")

# %%
# Check if non-matches cluster at certain positions
print("\nNon-matches by token position:")
pos_nonmatch_counts = Counter([m["tok_idx"] for m in nonmatches])
print(f"  Early (pos 0-9): {sum(pos_nonmatch_counts[i] for i in range(10) if i in pos_nonmatch_counts)}")
print(f"  Middle (pos 10-49): {sum(pos_nonmatch_counts[i] for i in range(10, 50) if i in pos_nonmatch_counts)}")
print(f"  Late (pos 50+): {sum(pos_nonmatch_counts[i] for i in range(50, 200) if i in pos_nonmatch_counts)}")

# %%
# Investigate a specific non-match in detail
if nonmatches:
    print("\n=== Detailed investigation of first non-match ===")
    m = nonmatches[0]
    seq_idx = m["seq_idx"]
    tok_idx = m["tok_idx"]

    print(f"Prompt: {TEST_PROMPTS[seq_idx]}")
    print(f"Token position: {tok_idx}")
    print(f"Token ID: {m['token_id']}")
    print(f"Token text: '{tokenizer.decode([m['token_id']])}'")
    print(f"Logit rank: {int(m['logit_rank'])}")
    print(f"Probability: {m['prob']:.6f}")
    print(f"Margin: {m['margin']:.6f}")

    # Show context
    out_ids = outputs[seq_idx].output_token_ids
    context_ids = out_ids[:]
    context_text = tokenizer.decode(context_ids)
    print(f"\nContext: ...{context_text}...")


# %%
# Get raw logprobs for a specific sequence to investigate further
def get_raw_logprobs(seq_idx):
    """Fetch raw logprobs for a sequence to investigate."""
    req = outputs[seq_idx]
    full_sequence = req.prompt_token_ids + req.output_token_ids
    full_prompt = tinker.ModelInput.from_ints(full_sequence)

    logprob_result = sampling_client.sample(
        prompt=full_prompt,
        sampling_params=tinker.SamplingParams(max_tokens=1),
        num_samples=1,
        include_prompt_logprobs=True,
        topk_prompt_logprobs=TOP_K,
    ).result()

    return logprob_result.topk_prompt_logprobs, len(req.prompt_token_ids)


# %%
# Investigate first sequence with non-matches
if nonmatches:
    seq_to_investigate = nonmatches[0]["seq_idx"]
    print(f"\n=== Raw logprobs for sequence {seq_to_investigate} ===")

    logprobs, prompt_len = get_raw_logprobs(seq_to_investigate)
    gen_ids = outputs[seq_to_investigate].output_token_ids

    print(f"Prompt length: {prompt_len}")
    print(f"Generated tokens: {len(gen_ids)}")

    # Show first few positions
    print("\nFirst 10 generated token positions:")
    for i in range(min(100, len(gen_ids))):
        actual_id = gen_ids[i]
        actual_token = tokenizer.decode([actual_id])

        # Get logprobs for this position
        pos_logprobs = logprobs[prompt_len + i]
        if pos_logprobs:
            # Sort by logprob
            sorted_lp = sorted(pos_logprobs, key=lambda x: x[1], reverse=True)
            top_id, top_lp = sorted_lp[0]
            top_token = tokenizer.decode([top_id])

            # Find rank of actual token
            actual_rank = next((j for j, (tid, _) in enumerate(sorted_lp) if tid == actual_id), -1)
            actual_lp = next((lp for tid, lp in sorted_lp if tid == actual_id), None)

            match = "OK" if top_id == actual_id else "MISMATCH"
            print(f"  Pos {i}: generated='{actual_token}' (id={actual_id}, rank={actual_rank}, lp={actual_lp:.4f})")
            print(f"          top='{top_token}' (id={top_id}, lp={top_lp:.4f}) [{match}]")

# %%
