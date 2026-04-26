"""
train_layer2.py
================
Trains a TF-IDF + Random Forest classifier on synthetic Python
token-type sequences for the ML Layer 2 parser-hint model.

Run order:
    python generate_dataset_layer2.py   →  creates dataset_layer2.csv
    python train_layer2.py              →  trains and saves model

Outputs (in same directory):
    model_layer2.pkl          — trained Pipeline (TF-IDF + RF)
    label_encoder_layer2.pkl  — list of class-name strings
    confusion_layer2.png      — row-normalised confusion matrix
    feature_importance_layer2.png — top-30 TF-IDF feature importances
"""

import os
import pickle
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

# ── Config ────────────────────────────────────────────────────
DATASET_PATH = "dataset_layer2.csv"
MODEL_PATH   = "model_layer2.pkl"
LE_PATH      = "label_encoder_layer2.pkl"

RANDOM_STATE = 42
TEST_SIZE    = 0.20
CV_FOLDS     = 5

RF_PARAMS = dict(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features="sqrt",
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1,
)

TFIDF_PARAMS = dict(
    ngram_range=(1, 3),     # unigrams, bigrams, trigrams of token types
    max_features=3000,
    sublinear_tf=True,
    min_df=2,
)

# ── Tokenizer ────────────────────────────────────────────────
# Token sequences are already space-separated; split on whitespace.
def token_type_tokenizer(text: str):
    return text.split()

# ── Load data ─────────────────────────────────────────────────
script_dir   = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, DATASET_PATH)

if not os.path.exists(dataset_path):
    raise FileNotFoundError(
        f"Dataset not found at '{dataset_path}'.\n"
        "Run  python generate_dataset_layer2.py  first."
    )

df = pd.read_csv(dataset_path)
print(f"Loaded {len(df):,} samples, {df['class_id'].nunique()} classes.\n")

X = df["token_seq"].values
y = df["class_id"].values

class_names = [
    df.loc[df["class_id"] == i, "class_name"].iloc[0]
    for i in sorted(df["class_id"].unique())
]

# ── Train / test split ────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
)
print(f"Train : {len(X_train):,}  |  Test : {len(X_test):,}\n")

# ── Pipeline ──────────────────────────────────────────────────
tfidf = TfidfVectorizer(tokenizer=token_type_tokenizer,
                        token_pattern=None,
                        **TFIDF_PARAMS)
rf    = RandomForestClassifier(**RF_PARAMS)

pipeline = Pipeline([("tfidf", tfidf), ("rf", rf)])

# ── Cross-validation ──────────────────────────────────────────
print(f"Running {CV_FOLDS}-fold stratified cross-validation …")
cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
cv_scores = cross_val_score(pipeline, X_train, y_train,
                             cv=cv, scoring="accuracy", n_jobs=-1)
print(f"CV Accuracy:  {cv_scores.mean():.4f} ± {cv_scores.std():.4f}\n")

# ── Final fit ─────────────────────────────────────────────────
print("Fitting final model on full training set …")
pipeline.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────
y_pred   = pipeline.predict(X_test)
test_acc = accuracy_score(y_test, y_pred)

print(f"\n{'='*60}")
print(f"  Test Accuracy : {test_acc:.4f}  ({test_acc*100:.2f}%)")
print(f"{'='*60}\n")
print(classification_report(y_test, y_pred, target_names=class_names))

# ── Confusion matrix ──────────────────────────────────────────
cm      = confusion_matrix(y_test, y_pred)
cm_norm = cm.astype("float") / cm.sum(axis=1, keepdims=True)

fig, ax = plt.subplots(figsize=(14, 11))
sns.heatmap(cm_norm, annot=True, fmt=".2f", cmap="Blues",
            xticklabels=class_names, yticklabels=class_names,
            linewidths=0.5, ax=ax)
ax.set_xlabel("Predicted", fontsize=13)
ax.set_ylabel("True", fontsize=13)
ax.set_title("Layer 2 — Confusion Matrix (row-normalised)", fontsize=15)
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.yticks(rotation=0, fontsize=9)
plt.tight_layout()
plt.savefig("confusion_layer2.png", dpi=150)
plt.close()
print("Saved confusion matrix       →  confusion_layer2.png")

# ── Feature importances ───────────────────────────────────────
feature_names = np.array(pipeline.named_steps["tfidf"].get_feature_names_out())
importances   = pipeline.named_steps["rf"].feature_importances_
top_n  = 30
top_idx = np.argsort(importances)[-top_n:][::-1]

fig2, ax2 = plt.subplots(figsize=(10, 8))
ax2.barh(range(top_n), importances[top_idx][::-1], color="steelblue", edgecolor="white")
ax2.set_yticks(range(top_n))
ax2.set_yticklabels(feature_names[top_idx][::-1], fontsize=9)
ax2.set_xlabel("Mean Decrease in Impurity", fontsize=12)
ax2.set_title(f"Layer 2 — Top {top_n} Token-Type Feature Importances", fontsize=14)
plt.tight_layout()
plt.savefig("feature_importance_layer2.png", dpi=150)
plt.close()
print("Saved feature importances    →  feature_importance_layer2.png")

# ── Save model ────────────────────────────────────────────────
with open(MODEL_PATH, "wb") as fh:
    pickle.dump(pipeline, fh)
print(f"Saved model                  →  {MODEL_PATH}")

with open(LE_PATH, "wb") as fh:
    pickle.dump(class_names, fh)
print(f"Saved label encoder          →  {LE_PATH}")

# ── Inference demo ────────────────────────────────────────────
print("\n── Inference demo ──────────────────────────────────────")

demo = [
    ("IDENTIFIER OPERATOR INTEGER",                                    "assignment"),
    ("KW_def IDENTIFIER DELIMITER IDENTIFIER DELIMITER DELIMITER",     "funcdef"),
    ("KW_class IDENTIFIER DELIMITER IDENTIFIER DELIMITER DELIMITER",   "classdef"),
    ("KW_for IDENTIFIER KW_in IDENTIFIER DELIMITER",                   "for_loop"),
    ("KW_while IDENTIFIER OPERATOR INTEGER DELIMITER",                 "while_loop"),
    ("KW_if IDENTIFIER OPERATOR INTEGER DELIMITER",                    "if_stmt"),
    ("KW_return IDENTIFIER",                                           "return_stmt"),
    ("KW_import IDENTIFIER",                                           "import_stmt"),
    ("IDENTIFIER DELIMITER IDENTIFIER DELIMITER",                      "func_call"),
    ("IDENTIFIER OPERATOR LBRACKET IDENTIFIER RBRACKET",              "list_expr"),
    ("IDENTIFIER OPERATOR LBRACE STRING DELIMITER IDENTIFIER RBRACE", "dict_expr"),
    ("IDENTIFIER OPERATOR KW_lambda IDENTIFIER DELIMITER IDENTIFIER", "lambda_expr"),
    ("KW_try DELIMITER",                                               "try_except"),
    ("KW_raise IDENTIFIER DELIMITER STRING DELIMITER",                 "raise_stmt"),
    ("KW_assert IDENTIFIER OPERATOR INTEGER",                          "assert_stmt"),
]

preds = pipeline.predict([d[0] for d in demo])
print(f"{'Token Sequence':<55}  {'Predicted':<15}  Expected")
print("-" * 90)
for (seq_str, expected), pred in zip(demo, preds):
    ok = "✓" if class_names[pred] == expected else "✗"
    print(f"  {seq_str:<53}  {class_names[pred]:<15}  {ok} {expected}")