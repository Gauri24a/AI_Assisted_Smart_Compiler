import sys
from pathlib import Path

THIS_DIR  = Path(__file__).resolve().parent
LEXER_DIR = THIS_DIR.parent / "lexer"
AST_DIR   = THIS_DIR.parent / "AST"
ML_DIR    = THIS_DIR.parent / "ML"
SEM_DIR   = THIS_DIR.parent / "semantic"
IR_DIR    = THIS_DIR.parent / "ir"

for d in (LEXER_DIR, AST_DIR, ML_DIR, SEM_DIR, IR_DIR, THIS_DIR):
    sys.path.insert(0, str(d))

from Lexer            import Lexer,  LexerError
from Parser           import Parser, ParseError
from ml_layer1_cache  import StatementCache
from ml_layer2_hint   import HintModel
from SemanticAnalyzer import SemanticAnalyzer
from IRGenerator      import IRGenerator
from ml_layer3_opt    import OptStrategy
from Optimizer        import Optimizer

input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else LEXER_DIR / "test.txt"

if not input_path.exists():
    print(f"[ERROR] file not found: {input_path}"); sys.exit(1)

with open(input_path, encoding="utf-8") as f:
    code = f.read()

try:    tokens = Lexer().tokenize(code)
except LexerError as e:
    print(f"[LEXER ERROR] {e}"); sys.exit(1)

try:    ast = Parser(tokens, cache=StatementCache(), hint_model=HintModel()).parse()
except ParseError as e:
    print(f"[PARSE ERROR] {e}"); sys.exit(1)

errors = SemanticAnalyzer().analyze(ast)
if errors:
    for e in errors: print(f"[SEMANTIC] {e}")
    sys.exit(1)

ir         = IRGenerator().generate(ast)
strategies = OptStrategy().predict(ir)
ir         = Optimizer().optimize(ir, strategies)

print(f"[OPTIMIZER] strategies: {strategies}\n")
for instr in ir:
    print(instr)
