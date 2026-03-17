"""
Main compiler pipeline script.

This script orchestrates the entire compiler process from source code to AI-assisted
semantic analysis, as per the project architecture.

Workflow:
1.  Reads a source file provided as a command-line argument.
2.  Performs Lexical Analysis to tokenize the source code.
3.  Performs Syntax Analysis to build an Abstract Syntax Tree (AST).
4.  Loads the pre-trained TF-IDF + Random Forest pipeline (model.pkl).
5.  Traverses the AST, and for each high-level statement:
    a. Converts the AST node back into a simplified string representation.
    b. Feeds the string directly into the pipeline for prediction.
    c. Prints the predicted statement type and confidence.
6.  Saves results to a JSON file.
"""

import sys
import os
import re
import json
import pickle

from src.lexer import Lexer
from src.parser import Parser
from src.semantic_analyzer import SemanticAnalyzer
from src.ast_nodes import (
    ASTNode, AssignmentNode, IfNode, WhileNode, PrintNode,
    BinaryOpNode, UnaryOpNode, VariableNode, NumberNode, StringNode
)

# ──────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────

MODELS_DIR  = "ml"
MODEL_PATH  = os.path.join(MODELS_DIR, "model.pkl")
LE_PATH     = os.path.join(MODELS_DIR, "label_encoder.pkl")
CACHE_FILES = ("output.txt", "output.json")

# ──────────────────────────────────────────
# TOKENIZER — required by the pickled model
# ──────────────────────────────────────────

def c_tokenizer(text: str):
    """
    Splits a C/C++ statement into meaningful tokens.
    This function MUST be identical to the one used during model training.
    """
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\w\s]", text)


# ──────────────────────────────────────────
# LOAD MODEL
# ──────────────────────────────────────────

print("Loading AI models...")
try:
    with open(MODEL_PATH, "rb") as f:
        pipeline = pickle.load(f)
    with open(LE_PATH, "rb") as f:
        class_names = pickle.load(f)
    print(f"Models loaded successfully. ({len(class_names)} classes)\n")
except Exception as e:
    print(f"Fatal Error: Could not load AI models. {e}")
    print(f"Please ensure '{MODEL_PATH}' and '{LE_PATH}' exist.")
    print("Run  python train.py  first.")
    sys.exit(1)


# ──────────────────────────────────────────
# PREDICTION
# ──────────────────────────────────────────

def predict_statement_type(statement_text: str) -> dict:
    """
    Predict the class of a single statement string.
    Returns dict with class_name, class_id, and confidence.
    """
    if not statement_text.strip():
        return {"class_name": "Unknown", "class_id": -1, "confidence": 0.0}

    probs      = pipeline.predict_proba([statement_text])[0]
    class_id   = int(probs.argmax())
    confidence = float(probs[class_id])

    return {
        "class_name": class_names[class_id],
        "class_id":   class_id,
        "confidence": round(confidence, 4),
    }


def load_cached_predictions(statement_count: int):
    """
    Load pre-classified statements from output.txt/output.json when available.
    Supports either a raw list of predictions or a dict with a `predictions` key.
    """
    for cache_path in CACHE_FILES:
        if not os.path.exists(cache_path):
            continue

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            continue

        predictions = payload if isinstance(payload, list) else payload.get("predictions")
        if not isinstance(predictions, list):
            continue
        if len(predictions) < statement_count:
            continue

        print(f"Using cached ML classification from '{cache_path}'.")
        return predictions, cache_path

    return None, None


# ──────────────────────────────────────────
# AST → STRING
# ──────────────────────────────────────────

def stringify_expression(node) -> str:
    """Recursively converts an expression AST node to a string."""
    if isinstance(node, (NumberNode, StringNode)):
        return str(node.value)
    if isinstance(node, VariableNode):
        return node.name
    if isinstance(node, UnaryOpNode):
        return f"{node.operator}{stringify_expression(node.operand)}"
    if isinstance(node, BinaryOpNode):
        left  = stringify_expression(node.left)
        right = stringify_expression(node.right)
        return f"{left} {node.operator} {right}"
    return "x"


def ast_node_to_string(node) -> str:
    """Converts a statement AST node back to a representative C/C++ string."""
    if isinstance(node, AssignmentNode):
        return f"{node.target.name} = {stringify_expression(node.value)};"
    if isinstance(node, IfNode):
        return f"if ({stringify_expression(node.condition)}) {{ }}"
    if isinstance(node, WhileNode):
        return f"while ({stringify_expression(node.condition)}) {{ }}"
    if isinstance(node, PrintNode):
        return f'printf("%s\\n", {stringify_expression(node.expression)});'
    # Fallback
    return node.__class__.__name__


# ──────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────

def run_pipeline(source_file: str, output_json_path: str = None):
    """Executes lexer, parser, ML classification, and semantic analysis."""
    print(f"--- Starting Compilation for: {source_file} ---\n")

    try:
        with open(source_file, "r") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Fatal Error: Source file not found at '{source_file}'")
        return

    # 1. Lexical Analysis
    print("1. Running Lexer...")
    lexer  = Lexer(source_code)
    tokens = lexer.tokenize()
    if lexer.errors:
        print("Lexical Errors Found:")
        for error in lexer.errors:
            print(f"  - {error}")
        return

    # 2. Syntax Analysis
    print("2. Running Parser...")
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        return

    print("3. AST generated. Running AI classification...\n")
    print("─" * 60)

    if not ast.statements:
        print("No statements found to classify.")
        return

    prediction_results = []
    cached_predictions, cache_path = load_cached_predictions(len(ast.statements))
    BAR = 20

    for i, node in enumerate(ast.statements, 1):
        stmt_str = ast_node_to_string(node)

        if cached_predictions:
            cached_row = cached_predictions[i - 1]
            result = {
                "class_name": cached_row.get("predicted_type") or cached_row.get("class_name", "Unknown"),
                "class_id": int(cached_row.get("class_id", -1)),
                "confidence": float(cached_row.get("confidence", 0.0)),
            }
        else:
            result = predict_statement_type(stmt_str)

        filled = int(result["confidence"] * BAR)
        bar    = "█" * filled + "░" * (BAR - filled)

        print(f"[{i}] {stmt_str}")
        print(f"     Type       : {result['class_name']}  (id={result['class_id']})")
        print(f"     Confidence : [{bar}]  {result['confidence']*100:.1f}%")
        print()

        prediction_results.append({
            "statement":      stmt_str,
            "node_type":      node.__class__.__name__,
            "predicted_type": result["class_name"],
            "class_id":       result["class_id"],
            "confidence":     result["confidence"],
        })

    print("4. Running Semantic Analyzer (symbol table + scope checks)...")
    semantic_analyzer = SemanticAnalyzer()
    semantic_report = semantic_analyzer.analyze(ast, prediction_results)

    if semantic_report["issues"]:
        print("   Semantic issues found:")
        for issue in semantic_report["issues"]:
            print(f"   - [{issue['level'].upper()}] {issue['message']} ({issue['node_type']})")
    else:
        print("   No semantic issues found.")

    # --- Save Results ---
    output_path = output_json_path or "output.json"
    final_output = {
        "source_file": source_file,
        "classification_source": cache_path or "live_model",
        "predictions": prediction_results,
        "semantic": semantic_report,
    }

    try:
        with open(output_path, "w") as f:
            json.dump(final_output, f, indent=4)
        print(f"\n✅ Predictions saved successfully to '{output_path}'")
    except Exception as e:
        print(f"\n❌ Error saving predictions to '{output_path}': {e}")

    print("─" * 60)
    print(f"Predictions saved  →  {output_path}")
    print("--- Compilation Pipeline Finished ---\n")


# ──────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage:   python run_compiler.py <source_file> [output_json]")
        print("Example: python run_compiler.py examples/simple_test.txt")
        print("Example: python run_compiler.py examples/simple_test.txt out/results.json")
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else None
    run_pipeline(input_file, output_file)