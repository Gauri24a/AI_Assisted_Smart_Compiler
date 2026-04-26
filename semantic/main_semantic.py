import sys
from pathlib import Path

THIS_DIR  = Path(__file__).resolve().parent
LEXER_DIR = THIS_DIR.parent / "lexer"
AST_DIR   = THIS_DIR.parent / "AST"
ML_DIR    = THIS_DIR.parent / "ML"

sys.path.insert(0, str(LEXER_DIR))
sys.path.insert(0, str(AST_DIR))
sys.path.insert(0, str(ML_DIR))
sys.path.insert(0, str(THIS_DIR))

from Lexer              import Lexer,  LexerError
from Parser             import Parser, ParseError
from ml_layer1_cache    import StatementCache
from ml_layer2_hint     import HintModel
from SemanticAnalyzer   import SemanticAnalyzer

input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else LEXER_DIR / "test.txt"

if not input_path.exists():
    print(f"[ERROR] File not found: {input_path}"); sys.exit(1)

with open(input_path, encoding="utf-8") as f:
    code = f.read()

try:
    tokens = Lexer().tokenize(code)
except LexerError as e:
    print(f"[LEXER ERROR] {e}"); sys.exit(1)

try:
    ast = Parser(tokens, cache=StatementCache(), hint_model=HintModel()).parse()
except ParseError as e:
    print(f"[PARSE ERROR] {e}"); sys.exit(1)

errors = SemanticAnalyzer().analyze(ast)

if errors:
    print(f"[SEMANTIC] {len(errors)} error(s):")
    for e in errors:
        print(f"  {e}")
else:
    print("[SEMANTIC] OK — no errors")
