import sys
from pathlib import Path

THIS_DIR  = Path(__file__).resolve().parent
LEXER_DIR = THIS_DIR.parent / "lexer"
AST_DIR   = THIS_DIR.parent / "AST"
ML_DIR    = THIS_DIR.parent / "ML"
SEM_DIR   = THIS_DIR.parent / "semantic"
IR_DIR    = THIS_DIR.parent / "ir"
OPT_DIR   = THIS_DIR.parent / "optimizer"

for d in (LEXER_DIR, AST_DIR, ML_DIR, SEM_DIR, IR_DIR, OPT_DIR, THIS_DIR):
    sys.path.insert(0, str(d))

from Lexer            import Lexer,  LexerError
from Parser           import Parser, ParseError
from ml_layer1_cache  import StatementCache
from ml_layer2_hint   import HintModel
from SemanticAnalyzer import SemanticAnalyzer
from IRGenerator      import IRGenerator
from ml_layer3_opt    import OptStrategy
from Optimizer        import Optimizer


OP_MAP = {
    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
    "//": "DIV", "%": "MOD", "**": "POW",
    "==": "CMP_EQ", "!=": "CMP_NE",
    "<":  "CMP_LT", ">":  "CMP_GT",
    "<=": "CMP_LE", ">=": "CMP_GE",
    "and": "AND", "or": "OR", "not": "NOT",
}


class AssemblyGenerator:
    def __init__(self):
        self._out    = []
        self._regs   = {}  # var/tmp -> register name
        self._reg_n  = 0

    def generate(self, ir):
        for instr in ir:
            self._emit(instr)
        return self._out

    def _reg(self, name):
        if name not in self._regs:
            self._regs[name] = f"r{self._reg_n}"
            self._reg_n += 1
        return self._regs[name]

    def _write(self, line):
        self._out.append(line)

    def _emit(self, instr):
        op = instr.op

        if op == "funcdef":
            self._write(f"\n{instr.a}:")
            for i, param in enumerate(instr.b):
                self._write(f"  LOAD  {self._reg(param)}  arg{i}")

        elif op == "funcend":
            self._write(f"  RET")

        elif op == "assign":
            if instr.dest == "_":
                return
            dest = self._reg(instr.dest)
            self._write(f"  MOV   {dest}  {instr.a}")

        elif op == "binop":
            # instr.a = left operand,  instr.b = "OP right"
            parts   = instr.b.split(" ", 1)
            asm_op  = OP_MAP.get(parts[0], parts[0])
            right   = parts[1] if len(parts) > 1 else ""
            dest    = self._reg(instr.dest)
            left    = self._reg(instr.a) if instr.a in self._regs else instr.a
            self._write(f"  {asm_op:<6}  {dest}  {left}  {right}")

        elif op == "param":
            self._write(f"  PUSH  {instr.a}")

        elif op == "call":
            self._write(f"  CALL  {instr.a}  {instr.b}")
            if instr.dest:
                self._write(f"  MOV   {self._reg(instr.dest)}  retval")

        elif op == "return":
            self._write(f"  MOV   retval  {instr.a}")
            self._write(f"  RET")

        elif op == "label":
            self._write(f"\n{instr.a}:")

        elif op == "jump":
            self._write(f"  JMP   {instr.a}")

        elif op == "jumpif":
            # instr.b = "not -> LX"
            label = instr.b.split("-> ")[1]
            cond  = self._reg(instr.a) if instr.a in self._regs else instr.a
            self._write(f"  JZ    {cond}  {label}")


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
asm        = AssemblyGenerator().generate(ir)

print("[ASSEMBLY]")
for line in asm:
    print(line)