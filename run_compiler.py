"""
Main compiler pipeline script.

This script orchestrates the entire compiler process from source code to AI-assisted
semantic analysis, as per the project architecture.

Workflow:
1.  Reads a source file provided as a command-line argument.
2.  Performs Lexical Analysis to tokenize the source code.
3.  Performs Syntax Analysis to build an Abstract Syntax Tree (AST).
4.  Loads the pre-trained Word2Vec and Keras models.
5.  Traverses the AST, and for each high-level statement:
    a. Converts the AST node back into a simplified string representation.
    b. Tokenizes and vectorizes the string.
    c. Feeds the vector into the trained classifier to predict the statement's type.
6.  Prints each statement along with its AI-predicted classification.
"""

import sys
import os
import re
import json
import numpy as np
from gensim.models import Word2Vec
from tensorflow.keras.models import load_model

from src.lexer import Lexer
from src.parser import Parser
from src.ast_nodes import (
    ASTNode, AssignmentNode, IfNode, WhileNode, PrintNode,
    BinaryOpNode, UnaryOpNode, VariableNode, NumberNode, StringNode
)

# --- Constants ---
MODELS_DIR = "Dataset generation_NN_Layer"
W2V_MODEL_PATH = os.path.join(MODELS_DIR, "word2vec.model")
CLASSIFIER_PATH = os.path.join(MODELS_DIR, "statement_classifier.h5")
CLASS_LABELS = {0: "Assignment", 1: "Loop", 2: "Conditional", 3: "Declaration"}

# --- AI Model Loading ---
print("Loading AI models...")
try:
    w2v_model = Word2Vec.load(W2V_MODEL_PATH)
    classifier_model = load_model(CLASSIFIER_PATH, compile=False) # Use compile=False for prediction
    print("Models loaded successfully.")
except Exception as e:
    print(f"Fatal Error: Could not load AI models. {e}")
    print(f"Please ensure '{W2V_MODEL_PATH}' and '{CLASSIFIER_PATH}' exist.")
    sys.exit(1)


# --- AI Prediction Functions ---
def tokenize_statement(statement):
    """Simple regex-based tokenizer for a line of code."""
    return re.findall(r'[A-Za-z_][A-Za-z0-9_]*|\d+|[=+\-*/<>;(){}]', statement)

def get_statement_vector(tokens, model):
    """Converts a list of tokens into a single vector using a Word2Vec model."""
    vectors = [model.wv[token] for token in tokens if token in model.wv]
    if not vectors:
        return np.zeros(model.vector_size)
    return np.mean(vectors, axis=0)

def predict_statement_type(statement_text):
    """Predicts the class of a single statement string."""
    tokens = tokenize_statement(statement_text)
    vector = get_statement_vector(tokens, w2v_model)
    if vector.shape[0] == 0: # Handle empty statements
        return "Unknown"
    vector = vector.reshape(1, -1)  # Reshape for single prediction
    prediction = classifier_model.predict(vector, verbose=0)
    predicted_class_index = np.argmax(prediction)
    return CLASS_LABELS.get(predicted_class_index, "Unknown")


# --- AST to String Conversion ---
def stringify_expression(node):
    """Recursively converts an expression AST node to a string."""
    if isinstance(node, NumberNode) or isinstance(node, StringNode):
        return str(node.value)
    if isinstance(node, VariableNode):
        return node.name
    if isinstance(node, UnaryOpNode):
        return f"{node.operator}{stringify_expression(node.operand)}"
    if isinstance(node, BinaryOpNode):
        return f"{stringify_expression(node.left)} {node.operator} {stringify_expression(node.right)}"
    return "..."

def ast_node_to_string(node):
    """Converts a statement AST node back to a representative string."""
    if isinstance(node, AssignmentNode):
        return f"{node.target.name} = {stringify_expression(node.value)};"
    if isinstance(node, IfNode):
        return f"if ({stringify_expression(node.condition)}) {{...}}"
    if isinstance(node, WhileNode):
        return f"while ({stringify_expression(node.condition)}) {{...}}"
    if isinstance(node, PrintNode):
        return f"print({stringify_expression(node.expression)});"
    # Fallback for unknown or simple nodes
    return node.__class__.__name__


# --- Main Compiler Pipeline ---
def run_pipeline(source_file, output_json_path=None):
    """Executes the lexer, parser, and AI classification pipeline."""
    print(f"\n--- Starting Compilation for: {source_file} ---")
    try:
        with open(source_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Fatal Error: Source file not found at '{source_file}'")
        return

    # 1. Lexical Analysis
    print("1. Running Lexer...")
    lexer = Lexer(source_code)
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
        ast = parser.parse()
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        return
    
    print("3. AST Generated. Running AI Statement Classification...")
    print("\n--- AI Classification Results ---")

    # 4. AI Classification
    if not ast.statements:
        print("No statements found to classify.")
        return

    prediction_results = []

    for statement_node in ast.statements:
        # Convert node to a simple string for the model
        statement_str = ast_node_to_string(statement_node)
        
        # Get AI prediction
        predicted_type = predict_statement_type(statement_str)

        prediction_results.append(
            {
                "statement": statement_str,
                "predicted_intent": predicted_type,
                "node_type": statement_node.__class__.__name__,
            }
        )
        
        print(f"  - Statement: '{statement_str}'")
        print(f"    AI Predicted Intent: -> {predicted_type}\n")

    if output_json_path is None:
        source_stem = os.path.splitext(os.path.basename(source_file))[0]
        output_json_path = os.path.join(
            os.path.dirname(source_file) if os.path.dirname(source_file) else ".",
            f"{source_stem}_predictions.json",
        )

    output_payload = {
        "source_file": source_file,
        "total_statements": len(prediction_results),
        "predictions": prediction_results,
    }

    with open(output_json_path, "w", encoding="utf-8") as output_file:
        json.dump(output_payload, output_file, indent=2)

    print(f"Prediction JSON saved to: {output_json_path}")

    print("--- Compilation Pipeline Finished ---\n")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: python run_compiler.py <path_to_source_file> [output_json_path]")
        print("Example: python run_compiler.py examples/simple_test.txt")
        print("Example: python run_compiler.py examples/simple_test.txt outputs/simple_predictions.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else None
    run_pipeline(input_file, output_file)
