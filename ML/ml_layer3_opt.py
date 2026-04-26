"""
ml_layer3_opt.py  — Real ML Edition
======================================
Optimization strategy predictor backed by a trained
MultiOutputClassifier (model_layer3.pkl).

At runtime the pipeline calls:
    opt_ml = OptStrategy()
    strategies = opt_ml.predict(ir)   →  e.g. ["constant_fold", "loop_unroll"]

The model takes numeric IR feature vectors and predicts which of the
four optimization strategies to apply.  Falls back to rule-based
heuristics when the model is unavailable.
"""

import os
import pickle

# ── Config ────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))

_MODEL_CANDIDATES = [
    os.path.join(_HERE, "layer3", "model_layer3.pkl"),
    os.path.join(_HERE, "model_layer3.pkl"),
]

# ── Load model (once, at import time) ────────────────────────
_bundle = None

def _load_model():
    global _bundle
    model_path = next((p for p in _MODEL_CANDIDATES if os.path.exists(p)), None)
    if model_path is None:
        print("[OptStrategy] WARNING: trained model not found — using rule-based fallback.")
        print("              Run layer3/train_layer3.py to train the model first.")
        return
    with open(model_path, "rb") as f:
        _bundle = pickle.load(f)
    print(f"[OptStrategy] Loaded classifier from {model_path}")

_load_model()

# ── Feature extraction (shared by ML path and fallback) ───────
def _extract_features(ir: list) -> dict:
    """
    Extract numeric features from a list of Instr objects.
    Matches the columns in FEATURE_COLS from train_layer3.py.
    """
    n_instrs  = len(ir)
    n_assigns = sum(1 for i in ir if i.op == "assign")
    n_binops  = sum(1 for i in ir if i.op == "binop")
    n_calls   = sum(1 for i in ir if i.op == "call")
    n_labels  = sum(1 for i in ir if i.op == "label")
    n_literals= sum(
        1 for i in ir
        if i.op == "assign" and i.a and str(i.a)[0] in "\"'0123456789"
    )
    # Count temp variables (names starting with 't' followed by digits)
    n_temps = sum(
        1 for i in ir
        if i.dest and len(i.dest) >= 2 and i.dest[0] == "t" and i.dest[1:].isdigit()
    )
    has_loop     = int(n_labels > 0)
    call_density = round(n_calls  / max(n_instrs, 1), 4)
    assign_ratio = round(n_assigns / max(n_instrs, 1), 4)
    depth_score  = n_labels * 2 + n_calls

    # avg_use_count: count how many times each dest variable appears
    # as an operand (a or b field) across all instructions
    dest_vars = {i.dest for i in ir if i.dest}
    use_counts = []
    for var in dest_vars:
        count = sum(
            1 for i in ir
            if (i.a and var in str(i.a)) or (i.b and var in str(i.b))
        )
        use_counts.append(count)
    avg_use_count = round(
        sum(use_counts) / max(len(use_counts), 1), 3
    )

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

# ── Rule-based fallback (original logic, kept as safety net) ──
_FALLBACK_RULES = {
    "constant_fold": lambda f: f["n_literals"] > 0,
    "dead_code":     lambda f: f["n_assigns"] > 2,
    "loop_unroll":   lambda f: f["has_loop"] == 1 and f["n_instrs"] < 30,
    "inline":        lambda f: f["n_calls"] > 0 and f["n_instrs"] < 20,
}

def _rule_predict(features: dict) -> list:
    return [opt for opt, rule in _FALLBACK_RULES.items() if rule(features)]


class OptStrategy:
    """
    Predict which optimization strategies to apply to an IR block.
    Uses the trained MultiOutputClassifier when available;
    falls back to rule-based heuristics otherwise.
    """

    def __init__(self):
        self._model_available = (_bundle is not None)

    def predict(self, ir: list) -> list:
        """
        ir : list of Instr objects from IRGenerator.

        Returns a list of strategy name strings, e.g.:
            ["constant_fold", "loop_unroll"]
        """
        if not ir:
            return []

        features = _extract_features(ir)

        if self._model_available:
            model       = _bundle["model"]
            feature_cols = _bundle["feature_cols"]
            strategies   = _bundle["strategies"]

            feature_vec = [[features[col] for col in feature_cols]]
            pred_flags  = model.predict(feature_vec)[0]   # shape (4,)

            return [s for s, flag in zip(strategies, pred_flags) if flag == 1]

        # Fallback
        return _rule_predict(features)

    def features(self, ir: list) -> dict:
        """Expose the extracted features (useful for debugging/logging)."""
        return _extract_features(ir)

    @property
    def model_loaded(self) -> bool:
        return self._model_available