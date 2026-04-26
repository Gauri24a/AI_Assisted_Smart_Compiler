"""
train_layer3.py
================
Trains a MultiOutput Decision Tree on IR block feature vectors
to predict which optimization strategies to apply.

One binary classifier per strategy:
  - constant_fold
  - dead_code
  - loop_unroll
  - inline

Run order:
    python generate_dataset_layer3.py   →  creates dataset_layer3.csv
    python train_layer3.py              →  trains and saves model

Outputs (in same directory):
    model_layer3.pkl   — trained MultiOutputClassifier
    report_layer3.txt  — per-strategy classification report
    feature_importance_layer3.png — feature importances per strategy
"""

import os
import pickle

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ── Config ────────────────────────────────────────────────────
DATASET_PATH = "dataset_layer3.csv"
MODEL_PATH   = "model_layer3.pkl"
REPORT_PATH  = "report_layer3.txt"

RANDOM_STATE = 42
TEST_SIZE    = 0.20

STRATEGIES = ["constant_fold", "dead_code", "loop_unroll", "inline"]
LABEL_COLS  = [f"label_{s}" for s in STRATEGIES]

FEATURE_COLS = [
    "n_instrs", "n_assigns", "n_binops", "n_calls", "n_labels",
    "n_literals", "n_temps", "has_loop",
    "call_density", "assign_ratio", "avg_use_count", "depth_score",
]

DT_PARAMS = dict(
    max_depth=8,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=RANDOM_STATE,
)

# ── Load data ─────────────────────────────────────────────────
script_dir   = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, DATASET_PATH)

if not os.path.exists(dataset_path):
    raise FileNotFoundError(
        f"Dataset not found at '{dataset_path}'.\n"
        "Run  python generate_dataset_layer3.py  first."
    )

df = pd.read_csv(dataset_path)
print(f"Loaded {len(df):,} samples.\n")

X = df[FEATURE_COLS].values
Y = df[LABEL_COLS].values   # shape (N, 4)

# ── Train / test split ────────────────────────────────────────
X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=TEST_SIZE, random_state=RANDOM_STATE
)
print(f"Train : {len(X_train):,}  |  Test : {len(X_test):,}\n")

# ── Model: MultiOutputClassifier wrapping a Decision Tree ─────
# Decision Trees work well here — inputs are numeric features,
# the rules are naturally tree-shaped, and interpretability matters.
base_dt = DecisionTreeClassifier(**DT_PARAMS)
model   = MultiOutputClassifier(base_dt, n_jobs=-1)

# ── Cross-validation (per output averaged) ───────────────────
print("Running 5-fold cross-validation …")
# CV on first label as a proxy (MultiOutput CV is slow)
from sklearn.tree import DecisionTreeClassifier as DTC
cv_model = DTC(**DT_PARAMS)
from sklearn.model_selection import StratifiedKFold, cross_val_score
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

cv_results = {}
for i, strategy in enumerate(STRATEGIES):
    scores = cross_val_score(DTC(**DT_PARAMS), X_train, Y_train[:, i],
                             cv=cv, scoring="f1", n_jobs=-1)
    cv_results[strategy] = scores
    print(f"  {strategy:<20}  F1: {scores.mean():.4f} ± {scores.std():.4f}")

# ── Final fit ─────────────────────────────────────────────────
print("\nFitting final model …")
model.fit(X_train, Y_train)

# ── Evaluate ──────────────────────────────────────────────────
Y_pred = model.predict(X_test)

report_lines = []
report_lines.append("=" * 60)
report_lines.append("  Layer 3 — Optimization Strategy Classifier Report")
report_lines.append("=" * 60)

overall_acc = []
for i, strategy in enumerate(STRATEGIES):
    y_true = Y_test[:, i]
    y_pred = Y_pred[:, i]
    acc    = accuracy_score(y_true, y_pred)
    overall_acc.append(acc)
    block = f"\n── {strategy} ──\n"
    block += classification_report(y_true, y_pred,
                                   target_names=["skip", "apply"])
    block += f"  Accuracy: {acc:.4f}"
    report_lines.append(block)
    print(block)

report_lines.append(f"\nMean accuracy across strategies: {np.mean(overall_acc):.4f}")
print(f"\nMean accuracy across strategies: {np.mean(overall_acc):.4f}")

report_text = "\n".join(report_lines)
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(report_text)
print(f"\nSaved report  →  {REPORT_PATH}")

# ── Feature importances ───────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for i, (strategy, estimator) in enumerate(zip(STRATEGIES, model.estimators_)):
    imps  = estimator.feature_importances_
    order = np.argsort(imps)
    ax    = axes[i]
    ax.barh(range(len(FEATURE_COLS)), imps[order], color="teal", edgecolor="white")
    ax.set_yticks(range(len(FEATURE_COLS)))
    ax.set_yticklabels([FEATURE_COLS[j] for j in order], fontsize=9)
    ax.set_title(f"{strategy}", fontsize=11, fontweight="bold")
    ax.set_xlabel("Feature Importance", fontsize=9)

plt.suptitle("Layer 3 — Feature Importances per Strategy", fontsize=13)
plt.tight_layout()
plt.savefig("feature_importance_layer3.png", dpi=150)
plt.close()
print("Saved feature importances  →  feature_importance_layer3.png")

# ── Save model ────────────────────────────────────────────────
with open(MODEL_PATH, "wb") as fh:
    pickle.dump({
        "model":        model,
        "feature_cols": FEATURE_COLS,
        "strategies":   STRATEGIES,
    }, fh)
print(f"Saved model  →  {MODEL_PATH}")

# ── Inference demo ────────────────────────────────────────────
print("\n── Inference demo ──────────────────────────────────────")

demo_blocks = [
    # (description, feature_dict)
    ("3-instr constant block",
     [3, 3, 0, 0, 0, 3, 0, 0, 0.0, 1.0, 0.5, 0]),
    ("10-instr loop, no calls",
     [10, 4, 6, 0, 2, 1, 3, 1, 0.0, 0.4, 1.2, 4]),
    ("5-instr with 2 calls",
     [5, 1, 2, 2, 0, 0, 1, 0, 0.4, 0.2, 1.0, 2]),
    ("40-instr large mixed",
     [40, 12, 20, 3, 4, 2, 10, 1, 0.075, 0.3, 2.1, 11]),
    ("6-instr dead-assign heavy",
     [6, 5, 1, 0, 0, 0, 4, 0, 0.0, 0.83, 0.6, 0]),
]

pred_matrix = model.predict([d[1] for d in demo_blocks])

print(f"{'Block':<35}  {'CF':>4}  {'DC':>4}  {'LU':>4}  {'IL':>4}  Applied Strategies")
print("-" * 80)
for (desc, _), preds in zip(demo_blocks, pred_matrix):
    cf, dc, lu, il = preds
    applied = [s for s, p in zip(STRATEGIES, preds) if p == 1]
    label   = ", ".join(applied) if applied else "none"
    print(f"  {desc:<33}  {cf:>4}  {dc:>4}  {lu:>4}  {il:>4}  {label}")