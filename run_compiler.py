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
import time
from pprint import pformat

try:
    import google.generativeai as genai
except Exception:
    genai = None

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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def load_env_file(env_path: str = ".env"):
    """Load KEY=VALUE pairs from a local .env file into environment variables."""
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Keep pipeline resilient even if .env has formatting issues
        pass


load_env_file()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", GEMINI_MODEL)

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


def load_cached_predictions(statement_count: int, source_file: str):
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

        expected_source = str(source_file).replace("\\", "/").lstrip("./")
        payload_source = ""
        predictions = payload if isinstance(payload, list) else payload.get("predictions")
        if isinstance(payload, dict):
            payload_source = str(payload.get("source_file", "")).replace("\\", "/").lstrip("./")
            if payload_source and payload_source != expected_source:
                continue

        if not isinstance(predictions, list):
            continue
        if len(predictions) < statement_count:
            continue

        print(f"Using cached ML classification from '{cache_path}'.")
        return predictions, cache_path

    return None, None


def _get_gemini_api_keys():
    """Read Gemini API keys from environment variables.

    Supported:
      - GEMINI_API_KEYS="key1,key2,key3"
      - GEMINI_API_KEY="single_key"
    """
    keys_csv = os.getenv("GEMINI_API_KEYS", "").strip()
    single_key = os.getenv("GEMINI_API_KEY", "").strip()

    keys = []
    if keys_csv:
        keys.extend([k.strip() for k in keys_csv.split(",") if k.strip()])
    if single_key:
        keys.append(single_key)

    # Remove duplicates while preserving order
    seen = set()
    unique_keys = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            unique_keys.append(key)
    return unique_keys


def _sanitize_error_message(message: str) -> str:
    """Redact API-key-like strings from errors before persisting to JSON."""
    if not message:
        return ""
    # Gemini / Google API keys usually begin with AIza and are 39 chars total.
    return re.sub(r"AIza[0-9A-Za-z_-]{35}", "[REDACTED_API_KEY]", message)


def generate_llm_semantic_feedback(source_code: str, errors: list):
    """Generate concise explanation of errors and fixes using Gemini."""
    if genai is None:
        return {
            "status": "skipped",
            "reason": "google-generativeai not installed",
        }

    keys = _get_gemini_api_keys()
    if not keys:
        return {
            "status": "skipped",
            "reason": "No Gemini API key found. Set GEMINI_API_KEYS or GEMINI_API_KEY.",
        }

    prompt = (
        "You are a compiler assistant.\n"
        "Given source code and compiler errors, produce a concise, practical fix guide.\n"
        "Do NOT return JSON.\n"
        "Keep it short and easy to read.\n\n"
        "Required output format (for EACH error):\n"
        "1) Error Summary: <brief summary>\n"
        "2) Why It Happens: <one short line>\n"
        "3) Fix Options: <N ways>\n"
        "4) Suggested New Statement (best single fix):\n"
        "```c\n"
        "<one corrected statement line>\n"
        "```\n"
        "5) Alternative Statements (optional):\n"
        "- `...`\n"
        "- `...`\n\n"
        "Important: The 'Suggested New Statement' code block is mandatory for each error.\n"
        "If there are multiple errors, include one code block per error.\n\n"
        f"SOURCE_CODE:\n{source_code}\n\n"
        f"ERRORS:\n" + "\n".join([f"- {e['phase']}: {e['message']}" for e in errors])
    )

    last_error = None
    for idx, key in enumerate(keys, start=1):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt)
            text = (response.text or "").strip()

            corrected_code = ""
            statement_suggestions = []

            code_blocks = re.findall(r"```(?:[a-zA-Z0-9_+-]*)?\n([\s\S]*?)```", text)
            if code_blocks:
                cleaned_blocks = [block.strip() for block in code_blocks if block.strip()]
                if cleaned_blocks:
                    corrected_code = "\n\n".join(cleaned_blocks)
                    statement_suggestions = cleaned_blocks

            if not statement_suggestions:
                inline_examples = re.findall(r"`([^`\n;]+;?)`", text)
                statement_suggestions = [item.strip() for item in inline_examples if item.strip()]

            return {
                "status": "ok",
                "model": GEMINI_MODEL,
                "key_index_used": idx,
                "result_text": text,
                "corrected_code": corrected_code,
                "statement_suggestions": statement_suggestions,
            }
        except Exception as e:
            last_error = _sanitize_error_message(str(e))
            continue

    return {
        "status": "failed",
        "reason": f"All Gemini keys failed. Last error: {last_error}",
    }


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


def format_tokens(tokens) -> str:
    rows = []
    for token in tokens:
        rows.append(f"{token.type.name:<14} value={token.value!r:<18} at {token.line}:{token.column}")
    return "\n".join(rows)


def format_ast(ast) -> str:
    return pformat(ast, width=100, compact=False)


# ──────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────

def run_pipeline(source_file: str, output_json_path: str = None):
    """Executes lexer, parser, ML classification, and semantic analysis."""
    print(f"--- Starting Compilation for: {source_file} ---\n")
    pipeline_start = time.perf_counter()

    try:
        with open(source_file, "r") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Fatal Error: Source file not found at '{source_file}'")
        return

    errors = []

    # 1. Lexical Analysis
    print("1. Running Lexer...")
    lex_start = time.perf_counter()
    lexer  = Lexer(source_code)
    tokens = lexer.tokenize()
    lex_ms = round((time.perf_counter() - lex_start) * 1000, 2)
    if lexer.errors:
        print("Lexical Errors Found:")
        for error in lexer.errors:
            print(f"  - {error}")
            errors.append({"phase": "lexical", "message": str(error)})
    print(f"   Token Count: {len(tokens)}")
    print("   Tokens:")
    print(format_tokens(tokens))

    # 2. Syntax Analysis
    print("2. Running Parser...")
    parse_start = time.perf_counter()
    ast = None
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
        parse_ms = round((time.perf_counter() - parse_start) * 1000, 2)
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        errors.append({"phase": "syntax", "message": str(e)})
        parse_ms = round((time.perf_counter() - parse_start) * 1000, 2)
    if ast:
        print(f"   AST Statement Count: {len(ast.statements)}")
        print("   AST:")
        print(format_ast(ast))
    else:
        print("   No AST generated due to errors.")

    prediction_results = []
    semantic_report = {"issues": []}
    cache_path = None
    if ast and ast.statements:
        print("3. AST generated. Running AI classification...\n")
        print("-" * 60)

        cached_predictions, cache_path = load_cached_predictions(len(ast.statements), source_file)
        class_start = time.perf_counter()
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
            bar    = "#" * filled + "." * (BAR - filled)

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

        classification_ms = round((time.perf_counter() - class_start) * 1000, 2)

        print("4. Running Semantic Analyzer (symbol table + scope checks)...")
        semantic_start = time.perf_counter()
        semantic_analyzer = SemanticAnalyzer()
        semantic_report = semantic_analyzer.analyze(ast, prediction_results)
        semantic_ms = round((time.perf_counter() - semantic_start) * 1000, 2)

        if semantic_report["issues"]:
            print("   Semantic issues found:")
            for issue in semantic_report["issues"]:
                print(f"   - [{issue['level'].upper()}] {issue['message']} ({issue['node_type']})")
                errors.append({"phase": "semantic", "level": issue['level'], "message": issue['message'], "node_type": issue['node_type']})
        else:
            print("   No semantic issues found.")
    else:
        classification_ms = 0.0
        semantic_ms = 0.0

    llm_feedback = None
    llm_ms = 0.0

    if errors:
        print("5. Requesting Gemini for error explanation and fixes...")
        llm_start = time.perf_counter()
        llm_feedback = generate_llm_semantic_feedback(source_code, errors)
        llm_ms = round((time.perf_counter() - llm_start) * 1000, 2)
        print(f"   Gemini status: {llm_feedback['status']}")

    total_ms = round((time.perf_counter() - pipeline_start) * 1000, 2)
    to_semantic_ms = round(lex_ms + parse_ms + classification_ms + semantic_ms, 2)

    # --- Save Results ---
    output_path = output_json_path or "output.json"
    final_output = {
        "source_file": source_file,
        "classification_source": cache_path or "live_model",
        "predictions": prediction_results,
        "semantic": semantic_report,
        "errors": errors,
        "llm_feedback": llm_feedback,
        "timings": {
            "lexer_ms": lex_ms,
            "parser_ms": parse_ms,
            "classification_ms": classification_ms,
            "semantic_ms": semantic_ms,
            "llm_ms": llm_ms,
            "to_semantic_ms": to_semantic_ms,
            "total_ms": total_ms,
        },
    }

    try:
        with open(output_path, "w") as f:
            json.dump(final_output, f, indent=4)
        print(f"\n[OK] Predictions saved successfully to '{output_path}'")
    except Exception as e:
        print(f"\n[ERROR] Error saving predictions to '{output_path}': {e}")

    print("-" * 60)
    print(f"Predictions saved to {output_path}")
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