"""
train.py
=========
Train a TF-IDF + Random Forest classifier on the synthetic C/C++ dataset.

Usage:
    python generate_dataset.py   # creates dataset.csv
    python train.py              # trains, evaluates, and saves the model

Outputs:
    model.pkl          — trained pipeline (TF-IDF + Random Forest)
    label_encoder.pkl  — LabelEncoder for class IDs → names
    confusion.png      — confusion matrix heat-map
    feature_importance.png — top-30 TF-IDF feature importances
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
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

# ------------------------------------------
# CONFIG
# ------------------------------------------

DATASET_PATH = os.path.join("..", "data", "dataset.csv")
MODEL_PATH   = "model.pkl"
LE_PATH      = "label_encoder.pkl"

RANDOM_STATE = 42
TEST_SIZE    = 0.20   # 80/20 split
CV_FOLDS     = 5      # stratified k-fold cross-validation

RF_PARAMS = dict(
    n_estimators=300,
    max_depth=None,         # grow full trees
    min_samples_split=2,
    min_samples_leaf=1,
    max_features="sqrt",    # standard for classification
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1,
)

TFIDF_PARAMS = dict(
    analyzer="word",
    token_pattern=None,     # suppresses warning when using a custom tokenizer
    ngram_range=(1, 3),     # unigrams, bigrams, trigrams
    max_features=5000,
    sublinear_tf=True,      # log-scale TF
    min_df=2,
)

# ------------------------------------------
# TOKENIZER — character-aware for C/C++
# ------------------------------------------

def c_tokenizer(text: str):
    """
    Splits a C/C++ statement into meaningful tokens:
      - identifiers / keywords
      - integer literals
      - operators and punctuation  (each char as its own token)
    This preserves structural info that whitespace-split misses,
    e.g.  '->'  '*'  '&'  '[' ']'
    """
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\w\s]", text)


# ------------------------------------------
# LOAD DATA
# ------------------------------------------

script_dir   = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, DATASET_PATH)

if not os.path.exists(dataset_path):
    raise FileNotFoundError(
        f"Dataset not found at '{dataset_path}'.\n"
        "Run  python generate_dataset.py  first."
    )

df = pd.read_csv(dataset_path)
print(f"Loaded {len(df):,} samples, {df['class_id'].nunique()} classes.\n")

X = df["statement"].values
y = df["class_id"].values

le = LabelEncoder()
le.fit(df["class_name"].unique())
class_names = [df.loc[df["class_id"] == i, "class_name"].iloc[0]
               for i in sorted(df["class_id"].unique())]

# ------------------------------------------
# TRAIN / TEST SPLIT
# ------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
)
print(f"Train : {len(X_train):,}  |  Test : {len(X_test):,}\n")

# ------------------------------------------
# PIPELINE
# ------------------------------------------

tfidf = TfidfVectorizer(tokenizer=c_tokenizer, **TFIDF_PARAMS)
rf    = RandomForestClassifier(**RF_PARAMS)

pipeline = Pipeline([
    ("tfidf", tfidf),
    ("rf",    rf),
])

# ------------------------------------------
# CROSS-VALIDATION  (on training fold only)
# ------------------------------------------

print(f"Running {CV_FOLDS}-fold stratified cross-validation …")
cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
cv_scores = cross_val_score(pipeline, X_train, y_train,
                             cv=cv, scoring="accuracy", n_jobs=-1)
print(f"CV Accuracy:  {cv_scores.mean():.4f} ± {cv_scores.std():.4f}\n")

# ------------------------------------------
# FINAL FIT ON FULL TRAINING SET
# ------------------------------------------

print("Fitting final model on full training set …")
pipeline.fit(X_train, y_train)

# ------------------------------------------
# EVALUATE ON HELD-OUT TEST SET
# ------------------------------------------

y_pred     = pipeline.predict(X_test)
test_acc   = accuracy_score(y_test, y_pred)

print(f"\n{'='*60}")
print(f"  Test Accuracy : {test_acc:.4f}  ({test_acc*100:.2f}%)")
print(f"{'='*60}\n")
print("Per-class report:")
print(classification_report(y_test, y_pred, target_names=class_names))

# ------------------------------------------
# CONFUSION MATRIX
# ------------------------------------------

cm = confusion_matrix(y_test, y_pred)
cm_norm = cm.astype("float") / cm.sum(axis=1, keepdims=True)

fig, ax = plt.subplots(figsize=(14, 11))
sns.heatmap(
    cm_norm,
    annot=True,
    fmt=".2f",
    cmap="Blues",
    xticklabels=class_names,
    yticklabels=class_names,
    linewidths=0.5,
    ax=ax,
)
ax.set_xlabel("Predicted", fontsize=13)
ax.set_ylabel("True", fontsize=13)
ax.set_title("Confusion Matrix (row-normalised)", fontsize=15)
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.yticks(rotation=0, fontsize=9)
plt.tight_layout()
plt.savefig("confusion.png", dpi=150)
plt.close()
print("Saved confusion matrix  ->  confusion.png")

# ------------------------------------------
# FEATURE IMPORTANCES
# ------------------------------------------

feature_names = np.array(pipeline.named_steps["tfidf"].get_feature_names_out())
importances   = pipeline.named_steps["rf"].feature_importances_
top_n         = 30
top_idx       = np.argsort(importances)[-top_n:][::-1]

fig2, ax2 = plt.subplots(figsize=(10, 8))
ax2.barh(
    range(top_n),
    importances[top_idx][::-1],
    color="steelblue",
    edgecolor="white",
)
ax2.set_yticks(range(top_n))
ax2.set_yticklabels(feature_names[top_idx][::-1], fontsize=9)
ax2.set_xlabel("Mean Decrease in Impurity", fontsize=12)
ax2.set_title(f"Top {top_n} TF-IDF Feature Importances", fontsize=14)
plt.tight_layout()
plt.savefig("feature_importance.png", dpi=150)
plt.close()
print("Saved feature importances  ->  feature_importance.png")

# ------------------------------------------
# SAVE MODEL
# ------------------------------------------

with open(MODEL_PATH, "wb") as fh:
    pickle.dump(pipeline, fh)
print(f"Saved model             ->  model.pkl")

with open(LE_PATH, "wb") as fh:
    pickle.dump(class_names, fh)
print(f"Saved label encoder     ->  label_encoder.pkl")

# ------------------------------------------
# QUICK INFERENCE DEMO
# ------------------------------------------

print("\n-- Inference demo --------------------------------------")

demo_statements = [
    "x = y + 5;",
    "for (int i = 0; i < n; i++) { }",
    "if (count > 10) { }",
    "int result = 0;",
    "free(ptr);",
    "return value;",
    "arr[i] = 42;",
    "*ptr = x;",
    "node->next = NULL;",
    "x++;",
    "flags = flags & 0xFF;",
    "ret = (x > 0) && (y < n);",
    "value = (int) ptr;",
    "buf = malloc(sizeof(int) * n);",
    "throw std::runtime_error(\"err\");",
]

preds = pipeline.predict(demo_statements)
print(f"{'Statement':<45}  Predicted Class")
print("-" * 70)
for stmt, pred in zip(demo_statements, preds):
    print(f"  {stmt:<43}  {class_names[pred]}")