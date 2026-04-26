"""
generate_dataset_layer3.py
===========================
Generates a synthetic dataset of IR block feature vectors paired
with the correct set of optimization strategies to apply.

Each sample is a numeric feature vector extracted from an IR block:
  - n_instrs     : total instruction count
  - n_assigns    : number of assign instructions
  - n_binops     : number of binop instructions
  - n_calls      : number of call instructions
  - n_labels     : number of label instructions (loop markers)
  - n_literals   : instructions assigning a literal constant
  - n_temps      : number of temporary variables (t0, t1, ...)
  - has_loop     : 1 if any label instruction present
  - call_density : n_calls / n_instrs
  - assign_ratio : n_assigns / n_instrs
  - avg_use_count: average times each variable is referenced
  - depth_score  : proxy for nesting depth (labels * 2 + calls)

Target: 4 binary columns, one per optimization strategy:
  - constant_fold   (eliminate compile-time constants)
  - dead_code       (remove unreferenced assignments)
  - loop_unroll     (hint the assembler to unroll short loops)
  - inline          (hint the assembler to inline small call sites)

Each strategy has a "true" rule derived from the IR features.
We add realistic noise so the classifier must generalise.

Total samples: 8,000  (2,000 per strategy split across positive/negative)
The dataset is used to train 4 binary classifiers (one per strategy)
inside a MultiOutputClassifier in train_layer3.py.
"""

import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

# ── Ground-truth rules (mirrors Optimizer logic + extended) ──
def label_constant_fold(f):
    return int(f["n_literals"] > 0 and f["assign_ratio"] > 0.3)

def label_dead_code(f):
    return int(f["n_assigns"] > 2 and f["avg_use_count"] < 1.8)

def label_loop_unroll(f):
    return int(f["has_loop"] == 1 and f["n_instrs"] <= 30 and f["n_labels"] <= 3)

def label_inline(f):
    return int(f["n_calls"] > 0 and f["n_instrs"] <= 20 and f["call_density"] > 0.05)

# ── Feature generator ─────────────────────────────────────────
def make_ir_features():
    """
    Simulate IR block feature vectors covering a wide range of
    real-world code patterns:
      - tiny leaf functions (few instructions, no loops, maybe a call)
      - medium functions with assignments and some arithmetic
      - loop bodies (labels present, medium size)
      - large functions (many instructions, mixed ops)
      - constant-heavy blocks (lots of literal assigns)
    """
    pattern = random.choice([
        "tiny_leaf",
        "medium_arith",
        "loop_body",
        "large_mixed",
        "constant_heavy",
        "call_heavy",
        "dead_assign_heavy",
        "nested_loop",
    ])

    if pattern == "tiny_leaf":
        n_instrs  = random.randint(1, 8)
        n_assigns = random.randint(0, n_instrs)
        n_binops  = n_instrs - n_assigns
        n_calls   = random.randint(0, 1)
        n_labels  = 0
        n_literals= random.randint(0, n_assigns)
        n_temps   = random.randint(0, 3)

    elif pattern == "medium_arith":
        n_instrs  = random.randint(8, 25)
        n_assigns = random.randint(2, n_instrs // 2)
        n_binops  = n_instrs - n_assigns
        n_calls   = random.randint(0, 2)
        n_labels  = 0
        n_literals= random.randint(0, n_assigns // 2)
        n_temps   = random.randint(2, 8)

    elif pattern == "loop_body":
        n_instrs  = random.randint(5, 30)
        n_assigns = random.randint(2, n_instrs // 2)
        n_binops  = n_instrs - n_assigns
        n_calls   = random.randint(0, 1)
        n_labels  = random.randint(1, 3)
        n_literals= random.randint(0, 3)
        n_temps   = random.randint(1, 6)

    elif pattern == "large_mixed":
        n_instrs  = random.randint(30, 80)
        n_assigns = random.randint(5, n_instrs // 2)
        n_binops  = n_instrs - n_assigns
        n_calls   = random.randint(0, 5)
        n_labels  = random.randint(0, 5)
        n_literals= random.randint(0, 10)
        n_temps   = random.randint(5, 20)

    elif pattern == "constant_heavy":
        n_instrs  = random.randint(4, 20)
        n_literals= random.randint(3, n_instrs)
        n_assigns = n_literals + random.randint(0, 3)
        n_assigns = min(n_assigns, n_instrs)
        n_binops  = max(0, n_instrs - n_assigns)
        n_calls   = 0
        n_labels  = 0
        n_temps   = random.randint(0, 4)

    elif pattern == "call_heavy":
        n_instrs  = random.randint(5, 20)
        n_calls   = random.randint(2, 6)
        n_instrs  = max(n_instrs, n_calls + 2)
        n_assigns = random.randint(1, n_instrs - n_calls)
        n_binops  = max(0, n_instrs - n_assigns - n_calls)
        n_labels  = 0
        n_literals= random.randint(0, 2)
        n_temps   = random.randint(1, 5)

    elif pattern == "dead_assign_heavy":
        n_instrs  = random.randint(6, 25)
        n_assigns = random.randint(4, n_instrs)
        n_assigns = min(n_assigns, n_instrs)
        n_binops  = max(0, n_instrs - n_assigns)
        n_calls   = 0
        n_labels  = 0
        n_literals= random.randint(0, n_assigns // 2)
        n_temps   = random.randint(2, 8)

    else:  # nested_loop
        n_instrs  = random.randint(10, 40)
        n_labels  = random.randint(2, 6)
        n_assigns = random.randint(2, n_instrs // 2)
        n_binops  = max(0, n_instrs - n_assigns)
        n_calls   = random.randint(0, 2)
        n_literals= random.randint(0, 4)
        n_temps   = random.randint(3, 12)

    # Clamp & derive
    n_assigns = max(0, min(n_assigns, n_instrs))
    n_binops  = max(0, min(n_binops, n_instrs))
    n_labels  = max(0, n_labels)
    n_calls   = max(0, min(n_calls, n_instrs))
    n_literals= max(0, min(n_literals, n_assigns))
    has_loop  = int(n_labels > 0)

    call_density  = round(n_calls  / max(n_instrs, 1), 4)
    assign_ratio  = round(n_assigns / max(n_instrs, 1), 4)
    depth_score   = n_labels * 2 + n_calls
    # avg_use_count: simulate how many times vars are referenced
    avg_use_count = round(random.uniform(0.5, 3.5), 3)

    return {
        "n_instrs":     n_instrs,
        "n_assigns":    n_assigns,
        "n_binops":     n_binops,
        "n_calls":      n_calls,
        "n_labels":     n_labels,
        "n_literals":   n_literals,
        "n_temps":      n_temps,
        "has_loop":     has_loop,
        "call_density": call_density,
        "assign_ratio": assign_ratio,
        "avg_use_count":avg_use_count,
        "depth_score":  depth_score,
    }

# ── Generate dataset ──────────────────────────────────────────
N_SAMPLES = 8000
rows = []

for _ in range(N_SAMPLES):
    f = make_ir_features()

    # Ground-truth labels
    cf = label_constant_fold(f)
    dc = label_dead_code(f)
    lu = label_loop_unroll(f)
    il = label_inline(f)

    # Add 5% label noise to encourage generalisation
    def noisy(v, p=0.05):
        return 1 - v if random.random() < p else v

    row = dict(f)
    row["label_constant_fold"] = noisy(cf)
    row["label_dead_code"]     = noisy(dc)
    row["label_loop_unroll"]   = noisy(lu)
    row["label_inline"]        = noisy(il)
    rows.append(row)

df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv("dataset_layer3.csv", index=False)

print(f"Dataset saved  →  dataset_layer3.csv")
print(f"Total samples  :  {len(df)}")
print(f"\nLabel distribution (positive rate):")
for col in ["label_constant_fold", "label_dead_code", "label_loop_unroll", "label_inline"]:
    rate = df[col].mean()
    print(f"  {col:<25}  {rate*100:.1f}% positive")
print(f"\nFeature summary:")
print(df[[c for c in df.columns if not c.startswith("label")]].describe().T[
    ["mean","std","min","max"]].round(2).to_string())