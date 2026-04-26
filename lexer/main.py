import json
import sys
import os
from Lexer import Lexer, LexerError

# ── change this to any file path ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(SCRIPT_DIR, "test.txt")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "tokens.json")

input_path = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE

if not os.path.exists(input_path):
    print(f"[ERROR] File not found: {input_path}")
    sys.exit(1)

with open(input_path, "r", encoding="utf-8") as f:
    code = f.read()

try:
    tokens = Lexer().tokenize(code)
except LexerError as e:
    print(f"[LEXER ERROR] {e}")
    sys.exit(1)

output = [t.to_dict() for t in tokens]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"Done — {len(output)} tokens written to '{OUTPUT_FILE}'")