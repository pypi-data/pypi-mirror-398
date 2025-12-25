import torch
import torch.nn.functional as F
from llm_py import Model, small_config, Embedding, RotaryPE, SelfAttention, FeedForward, LMHead
import time

def create_model():
    cfg = small_config(vocab_size=1000)
    cfg.dim = 64
    cfg.num_heads = 4
    cfg.hidden = 128
    
    model = (
        Model(cfg)
            .add(Embedding())
            .add(RotaryPE())
            .repeat(SelfAttention, 2, dropout=0.0)
            .add(FeedForward(dropout=0.0))
            .add(LMHead(tie_weights=True))
    )
    return model

def naive_generate(model, idx, max_new_tokens):
    # Greedy generation without KV cache
    for _ in range(max_new_tokens):
        # Forward full sequence
        logits = model(idx)
        logits = logits[:, -1, :]
        idx_next = torch.argmax(logits, dim=-1, keepdim=True)
        idx = torch.cat((idx, idx_next), dim=1)
    return idx

def test_generation_correctness():
    torch.manual_seed(42)
    model = create_model()
    model.eval()
    
    # Input
    idx = torch.randint(0, 1000, (1, 10))
    
    print("Running Naive Generation...")
    start = time.time()
    out_naive = naive_generate(model, idx.clone(), max_new_tokens=20)
    print(f"Naive Time: {time.time() - start:.4f}s")
    
    print("Running Cached Generation (model.generate)...")
    start = time.time()
    # temperature=0 for greedy
    out_cached = model.generate(idx.clone(), max_new_tokens=20, temperature=0.0)
    print(f"Cached Time: {time.time() - start:.4f}s")
    
    print(f"Naive Output: {out_naive[0, -20:].tolist()}")
    print(f"Cached Output: {out_cached[0, -20:].tolist()}")
    
    if torch.equal(out_naive, out_cached):
        print("PASS: Outputs match!")
    else:
        print("FAIL: Outputs do not match!")
        diff_indices = (out_naive != out_cached).nonzero()
        print(f"Differences at indices: {diff_indices}")
        
    print("\nRunning in Double Precision...")
    model.double()
    out_naive_d = naive_generate(model, idx.clone(), max_new_tokens=20)
    out_cached_d = model.generate(idx.clone(), max_new_tokens=20, temperature=0.0)
    if torch.equal(out_naive_d, out_cached_d):
        print("PASS (Double): Outputs match!")
    else:
        print("FAIL (Double): Outputs do not match!")

if __name__ == "__main__":
    test_generation_correctness()
