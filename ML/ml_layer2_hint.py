"""
ml_layer2_hint.py  -- Real ML Edition (v2)
============================================
Parser-hint model backed by a trained TF-IDF + Random Forest
classifier (model_layer2.pkl).

TOKEN ENCODING CONTRACT (matches generate_dataset_layer2.py v2):
  - First keyword token is emitted as  KW_<value>  (e.g. KW_def, KW_for)
  - All other tokens are emitted as their type name  (IDENTIFIER, OPERATOR …)
  - List brackets -> LBRACKET / RBRACKET
  - Dict braces   -> LBRACE   / RBRACE

The Parser._keys() method must encode the hint_key tuple the same way.
A drop-in replacement _hint_key() helper is provided below.

At runtime:
    hint = HintModel()
    label = hint.predict(token_key)   ->  e.g. "assignment"
"""

import os
import pickle

# ── Config ────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))

_MODEL_CANDIDATES = [
    os.path.join(_HERE, "layer2", "model_layer2.pkl"),
    os.path.join(_HERE, "model_layer2.pkl"),
]
_LE_CANDIDATES = [
    os.path.join(_HERE, "layer2", "label_encoder_layer2.pkl"),
    os.path.join(_HERE, "label_encoder_layer2.pkl"),
]

CONFIDENCE_THRESHOLD = 0.45

# ── Load model ────────────────────────────────────────────────
_pipeline    = None
_class_names = None

def _load_model():
    global _pipeline, _class_names
    model_path = next((p for p in _MODEL_CANDIDATES if os.path.exists(p)), None)
    le_path    = next((p for p in _LE_CANDIDATES    if os.path.exists(p)), None)
    if model_path is None or le_path is None:
        print("[HintModel] WARNING: trained model not found -- using rule-based fallback.")
        print("            Run layer2/train_layer2.py to train the model first.")
        return
    with open(model_path, "rb") as f:
        _pipeline = pickle.load(f)
    with open(le_path, "rb") as f:
        _class_names = pickle.load(f)
    print(f"[HintModel] Loaded classifier from {model_path}")

_load_model()

# ── Token encoding helper (use this in Parser._keys()) ───────
# Replaces the old generic "KEYWORD" encoding so the sequence
# matches what the model was trained on.

_BRACKET_MAP = {"[": "LBRACKET", "]": "RBRACKET", "{": "LBRACE", "}": "RBRACE"}

def encode_token(tok, is_first: bool) -> str:
    """
    Convert a single Token object to the string the model expects.
    tok.type : str  (e.g. "KEYWORD", "IDENTIFIER", "DELIMITER")
    tok.value: str  (e.g. "def", "x", "(")
    is_first  : whether this is the first token on the line
    """
    if tok.type == "KEYWORD":
        # Always emit keyword value so the model can distinguish statements
        return f"KW_{tok.value}"
    if tok.type == "DELIMITER" and tok.value in _BRACKET_MAP:
        return _BRACKET_MAP[tok.value]
    return tok.type   # IDENTIFIER, OPERATOR, INTEGER, FLOAT, STRING, DELIMITER


def build_hint_seq(tokens, start_pos: int, end_types=("NEWLINE", "EOF", "INDENT", "DEDENT")) -> str:
    """
    Build the space-joined token-type sequence string for a line of tokens
    starting at start_pos, stopping at end_types.
    Use this inside Parser to get the string to pass to HintModel.predict_seq().
    """
    parts = []
    i = start_pos
    while i < len(tokens) and tokens[i].type not in end_types:
        parts.append(encode_token(tokens[i], i == start_pos))
        i += 1
    return " ".join(parts)


# ── Rule-based fallback ───────────────────────────────────────
_KEYWORD_MAP = {
    "def":      "funcdef",
    "class":    "classdef",
    "return":   "return_stmt",
    "if":       "if_stmt",
    "elif":     "if_stmt",
    "else":     "if_stmt",
    "while":    "while_loop",
    "for":      "for_loop",
    "import":   "import_stmt",
    "from":     "import_stmt",
    "raise":    "raise_stmt",
    "assert":   "assert_stmt",
    "try":      "try_except",
    "except":   "try_except",
    "finally":  "try_except",
    "lambda":   "lambda_expr",
    "yield":    "return_stmt",
    "pass":     "assignment",
    "break":    "return_stmt",
    "continue": "return_stmt",
}

def _rule_predict(seq_str: str) -> str:
    first = seq_str.split()[0] if seq_str else ""
    if first.startswith("KW_"):
        kw = first[3:]
        return _KEYWORD_MAP.get(kw, "func_call")
    if seq_str.startswith("IDENTIFIER OPERATOR"):
        return "assignment"
    if seq_str.startswith("IDENTIFIER DELIMITER"):
        return "func_call"
    if "LBRACKET" in seq_str[:30]:
        return "list_expr"
    if "LBRACE" in seq_str[:30]:
        return "dict_expr"
    return "func_call"


class HintModel:
    """
    Predict Python statement type from a token-sequence string.
    """

    def __init__(self):
        self._freq: dict = {}
        self._model_available = (_pipeline is not None)

    def predict_seq(self, seq_str: str) -> str:
        """
        seq_str: space-joined token string built by build_hint_seq(),
                 e.g. "KW_def IDENTIFIER DELIMITER IDENTIFIER DELIMITER DELIMITER"

        Returns a label string such as "funcdef", "assignment", etc.
        """
        # 1. Online frequency table (high-confidence patterns from this run)
        key = seq_str
        if key in self._freq and self._freq[key]:
            best  = max(self._freq[key], key=self._freq[key].get)
            count = self._freq[key][best]
            if count >= 3:
                return best

        # 2. ML model
        if self._model_available:
            probs      = _pipeline.predict_proba([seq_str])[0]
            class_id   = int(probs.argmax())
            confidence = float(probs[class_id])
            if confidence >= CONFIDENCE_THRESHOLD:
                return _class_names[class_id]

        # 3. Rule-based fallback
        return _rule_predict(seq_str)

    # Backwards-compatible tuple-key interface for existing Parser code
    def predict(self, key: tuple) -> str:
        """
        key: tuple of token-type strings from the old Parser._keys() encoding.
        Converts to a seq string and calls predict_seq().
        """
        seq_str = " ".join(str(t) for t in key)
        return self.predict_seq(seq_str)

    def learn(self, seq_str: str, label: str):
        """Online update."""
        if seq_str not in self._freq:
            self._freq[seq_str] = {}
        self._freq[seq_str][label] = self._freq[seq_str].get(label, 0) + 1

    @property
    def model_loaded(self) -> bool:
        return self._model_available