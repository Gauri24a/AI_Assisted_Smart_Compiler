import json
import sys
from pathlib import Path

THIS_DIR  = Path(__file__).resolve().parent
LEXER_DIR = THIS_DIR.parent / "lexer"
ML_DIR    = THIS_DIR.parent / "ML"

sys.path.insert(0, str(LEXER_DIR))
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(ML_DIR))

from Lexer           import Lexer,  LexerError
from Parser          import Parser, ParseError
from ml_layer1_cache import StatementCache
from ml_layer2_hint  import HintModel

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
    cache = StatementCache()
    hint  = HintModel()
    ast   = Parser(tokens, cache=cache, hint_model=hint).parse()
except ParseError as e:
    print(f"[PARSE ERROR] {e}"); sys.exit(1)

def to_dict(x):
    if x is None or isinstance(x, (int, float, str, bool)): return x
    if isinstance(x, (list, tuple)): return [to_dict(i) for i in x]
    if hasattr(x, "__dict__"):
        return {"node": x.__class__.__name__} | {k: to_dict(v) for k, v in x.__dict__.items()}
    return str(x)

out = THIS_DIR / "ast.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(to_dict(ast), f, indent=2)

print(f"[OK] {len(tokens)} tokens → {out}")
print(f"[CACHE] {cache.stats()}")
