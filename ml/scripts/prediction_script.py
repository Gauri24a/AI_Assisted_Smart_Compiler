"""
ast_predict.py
===============
Classify C/C++ statements extracted from a JSON AST using the
TF-IDF + Random Forest model trained by train.py.

Usage:
    python ast_predict.py                          # uses default paths below
    python ast_predict.py input_program.json       # custom AST file
"""

import json
import os
import pickle
import sys

# ──────────────────────────────────────────
# PATHS  — edit these if needed
# ──────────────────────────────────────────

BASE_DIR   = r"D:\AI_Assisted_Smart_Compiler\ml"
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
LE_PATH    = os.path.join(BASE_DIR, "label_encoder.pkl")
AST_PATH   = os.path.join(BASE_DIR, "data", "input_program.json")

# Override AST path from CLI if provided
if len(sys.argv) > 1:
    AST_PATH = sys.argv[1]

# ──────────────────────────────────────────
# LOAD MODEL
# ──────────────────────────────────────────

with open(MODEL_PATH, "rb") as f:
    pipeline = pickle.load(f)

with open(LE_PATH, "rb") as f:
    class_names = pickle.load(f)

# ──────────────────────────────────────────
# AST NODE → C/C++ STATEMENT TEXT
# ──────────────────────────────────────────

def node_to_statement(node: dict) -> str:
    """
    Convert a JSON AST node to a C/C++ statement string.
    Handles the node types from your compiler + common extras.
    Returns empty string for unrecognised nodes.
    """
    node_type = node.get("type", "")

    # ── Assignment:  x = 5;
    if node_type == "AssignmentNode":
        target = _resolve(node.get("target", {}))
        value  = _resolve(node.get("value",  {}))
        return f"{target} = {value};"

    # ── Declaration:  int x = 5;
    if node_type == "DeclarationNode":
        dtype  = node.get("dtype", "int")
        name   = _resolve(node.get("name",  {}))
        value  = node.get("value")
        if value:
            return f"{dtype} {name} = {_resolve(value)};"
        return f"{dtype} {name};"

    # ── If / conditional:  if (x > 5) { }
    if node_type in ("IfNode", "ConditionalNode"):
        cond = _resolve_condition(node.get("condition", {}))
        return f"if ({cond}) {{ }}"

    # ── For loop:  for (int i = 0; i < n; i++) { }
    if node_type == "ForNode":
        init  = _resolve(node.get("init",  {}))
        cond  = _resolve_condition(node.get("condition", {}))
        incr  = _resolve(node.get("increment", {}))
        return f"for ({init}; {cond}; {incr}) {{ }}"

    # ── While loop:  while (x < n) { }
    if node_type == "WhileNode":
        cond = _resolve_condition(node.get("condition", {}))
        return f"while ({cond}) {{ }}"

    # ── Return:  return x;
    if node_type == "ReturnNode":
        value = _resolve(node.get("value", {}))
        return f"return {value};"

    # ── Function call:  foo(x, y);
    if node_type == "FunctionCallNode":
        name = node.get("name", "func")
        args = ", ".join(_resolve(a) for a in node.get("args", []))
        return f"{name}({args});"

    # ── Print (treat as function call):  printf("%s\n", x);
    if node_type == "PrintNode":
        expr = _resolve(node.get("expression", {}))
        return f'printf("%s\\n", {expr});'

    # ── Binary expression (standalone):  x + y;
    if node_type == "BinaryExprNode":
        return _resolve_condition(node) + ";"

    return ""


def _resolve(node) -> str:
    """Turn a value/identifier node into a string token."""
    if isinstance(node, str):
        return node
    if isinstance(node, (int, float)):
        return str(node)
    if isinstance(node, dict):
        ntype = node.get("type", "")
        if ntype == "IdentifierNode":
            return node.get("name", "x")
        if ntype in ("LiteralNode", "NumberNode", "StringNode"):
            return str(node.get("value", "0"))
        if ntype == "BinaryExprNode":
            return _resolve_condition(node)
        # fallback: try common keys
        for key in ("name", "value", "text"):
            if key in node:
                return str(node[key])
    return "x"


def _resolve_condition(node: dict) -> str:
    """Turn a condition/binary-expr node into an infix string."""
    if not isinstance(node, dict):
        return str(node)
    op    = node.get("operator", "==")
    left  = _resolve(node.get("left",  {}))
    right = _resolve(node.get("right", {}))
    return f"{left} {op} {right}"


# ──────────────────────────────────────────
# LOAD JSON AST
# ──────────────────────────────────────────

with open(AST_PATH, "r") as f:
    data = json.load(f)

# Support both  {"program": {"statements": [...]}}
# and flat      {"statements": [...]}
# and bare      [...]
if isinstance(data, list):
    statements = data
elif "program" in data:
    statements = data["program"].get("statements", [])
else:
    statements = data.get("statements", [])

print(f"Loaded {len(statements)} AST node(s) from '{AST_PATH}'\n")
print("=" * 62)

# ──────────────────────────────────────────
# PREDICT EACH NODE
# ──────────────────────────────────────────

BAR = 20

for i, node in enumerate(statements, 1):
    stmt_text = node_to_statement(node)

    if not stmt_text:
        print(f"[{i}] Skipped — unrecognised node type: {node.get('type','?')}")
        print("-" * 62)
        continue

    probs      = pipeline.predict_proba([stmt_text])[0]
    class_id   = int(probs.argmax())
    class_name = class_names[class_id]
    confidence = float(probs[class_id])

    filled = int(confidence * BAR)
    bar    = "█" * filled + "░" * (BAR - filled)

    print(f"[{i}] {stmt_text}")
    print(f"     Type       : {class_name}  (id={class_id})")
    print(f"     Confidence : [{bar}]  {confidence*100:.1f}%")

    # Show top-3 alternatives if confidence is low
    if confidence < 0.60:
        top3 = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)[:3]
        print("     Top-3 candidates:")
        for cid, prob in top3:
            print(f"       • {class_names[cid]:<25}  {prob*100:.1f}%")

    print("-" * 62)