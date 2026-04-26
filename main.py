"""
main.py — Central Compiler Pipeline
=====================================
Runs all compilation phases in order:
  1. Lexer      → lexer_output.json
  2. Parser/AST → ast_output.json
  3. Semantic   → semantic_output.json
  4. IR         → ir_output.json
  5. Optimizer  → optimizer_output.json
  6. Assembly   → assembly_output.json

Error-collection behaviour
--------------------------
Rather than stopping at the very first error and sending only that to the
LLM, the pipeline now collects errors across all phases that are still
reachable:

  • Lexer error(s)   → also attempt Parser (on partial tokens) + Semantic
  • Parser error(s)  → also attempt Semantic (on partial AST)
  • Semantic error(s)→ report as before

This means the LLM always receives the most complete picture of what is
wrong in the source file.

Usage:
  python main.py              # uses test.txt in same folder
  python main.py myfile.txt   # uses custom input file
"""

import sys
import json
import time
import traceback
from pathlib import Path

# ── Pickle compatibility fix ───────────────────────────────────────────────────
def token_type_tokenizer(text: str):
    return text.split()

sys.modules[__name__].token_type_tokenizer = token_type_tokenizer
import types as _types
_main_mod = sys.modules.get("__main__", sys.modules[__name__])
if not hasattr(_main_mod, "token_type_tokenizer"):
    setattr(_main_mod, "token_type_tokenizer", token_type_tokenizer)

# ── Path Setup ────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent
LEXER    = ROOT / "lexer"
AST_DIR  = ROOT / "AST"
SEM_DIR  = ROOT / "semantic"
IR_DIR   = ROOT / "IR"
OPT_DIR  = ROOT / "optimizer"
ASM_DIR  = ROOT / "assembly"
ML_DIR   = ROOT / "ML"
LLM_DIR  = ROOT / "LLM"

for p in (LEXER, AST_DIR, SEM_DIR, IR_DIR, OPT_DIR, ASM_DIR, ML_DIR, LLM_DIR):
    sys.path.insert(0, str(p))

# ── Imports ───────────────────────────────────────────────────────────────────
from Lexer            import Lexer,  LexerError,  LexerErrors
from Parser           import Parser, ParseError,  ParseErrors
from ml_layer1_cache  import StatementCache
from ml_layer2_hint   import HintModel
from SemanticAnalyzer import SemanticAnalyzer
from IRGenerator      import IRGenerator
from ml_layer3_opt    import OptStrategy
from Optimizer        import Optimizer
from llm_layer        import run_llm_layer

# ── Assembly Generator ────────────────────────────────────────────────────────
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
        self._out   = []
        self._regs  = {}
        self._reg_n = 0

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
            self._write("  RET")
        elif op == "assign":
            if instr.dest == "_":
                return
            self._write(f"  MOV   {self._reg(instr.dest)}  {instr.a}")
        elif op == "binop":
            parts  = instr.b.split(" ", 1)
            asm_op = OP_MAP.get(parts[0], parts[0])
            right  = parts[1] if len(parts) > 1 else ""
            dest   = self._reg(instr.dest)
            left   = self._reg(instr.a) if instr.a in self._regs else instr.a
            self._write(f"  {asm_op:<6}  {dest}  {left}  {right}")
        elif op == "param":
            self._write(f"  PUSH  {instr.a}")
        elif op == "call":
            self._write(f"  CALL  {instr.a}  {instr.b}")
            if instr.dest:
                self._write(f"  MOV   {self._reg(instr.dest)}  retval")
        elif op == "return":
            self._write(f"  MOV   retval  {instr.a}")
            self._write("  RET")
        elif op == "label":
            self._write(f"\n{instr.a}:")
        elif op == "jump":
            self._write(f"  JMP   {instr.a}")
        elif op == "jumpif":
            label = instr.b.split("-> ")[1]
            cond  = self._reg(instr.a) if instr.a in self._regs else instr.a
            self._write(f"  JZ    {cond}  {label}")

# ── Helpers ───────────────────────────────────────────────────────────────────
def write_json(data, filename):
    out_path = ROOT / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return out_path

def instr_to_dict(instr):
    return {
        "op":   instr.op,
        "dest": instr.dest,
        "a":    str(instr.a) if instr.a is not None else None,
        "b":    str(instr.b) if instr.b is not None else None,
    }

def ast_to_dict(x):
    if x is None or isinstance(x, (int, float, str, bool)):
        return x
    if isinstance(x, (list, tuple)):
        return [ast_to_dict(i) for i in x]
    if hasattr(x, "__dict__"):
        return {"node": x.__class__.__name__} | {
            k: ast_to_dict(v) for k, v in x.__dict__.items()
        }
    return str(x)

def get_llm_output():
    llm_file = ROOT / "llm_output.json"
    try:
        if llm_file.exists():
            with open(llm_file, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def run_compiler_pipeline(source_code: str):
    """Run the full compiler pipeline in-memory and return API-friendly JSON data."""
    code = source_code or ""
    result = {
        "phases": {},
        "has_errors": False,
        "error_phases": [],
        "timings": {},
    }

    lexer_errors, parser_errors, sem_errors = [], [], []
    tokens, ast = None, None

    # Phase 1: Lexer
    t0 = time.perf_counter()
    try:
        tokens = Lexer().tokenize(code)
        token_list = [t.to_dict() for t in tokens]
        result["phases"]["lexer"] = {
            "status": "OK",
            "token_count": len(token_list),
            "tokens": token_list,
        }
        result["timings"]["lexer"] = round(time.perf_counter() - t0, 4)
    except LexerErrors as exc:
        lexer_errors = [str(e) for e in exc.errors]
        tokens = exc.tokens
        token_list = [t.to_dict() for t in tokens] if tokens else []
        result["phases"]["lexer"] = {
            "status": "ERROR",
            "errors": lexer_errors,
            "token_count": len(token_list),
            "tokens": token_list,
        }
        result["timings"]["lexer"] = round(time.perf_counter() - t0, 4)
        result["has_errors"] = True
        result["error_phases"].append("lexer")
    except Exception as e:
        result["phases"]["lexer"] = {"status": "ERROR", "errors": [str(e)], "tokens": []}
        result["timings"]["lexer"] = round(time.perf_counter() - t0, 4)
        result["has_errors"] = True
        result["error_phases"].append("lexer")

    # Phase 2: Parser
    t0 = time.perf_counter()
    if tokens is not None:
        try:
            cache = StatementCache()
            hint = HintModel()
            ast = Parser(tokens, cache=cache, hint_model=hint).parse()
            result["phases"]["parser"] = {
                "status": "OK",
                "tree": ast_to_dict(ast),
                "cache_stats": cache.stats() if hasattr(cache, "stats") else {},
            }
            result["timings"]["parser"] = round(time.perf_counter() - t0, 4)
        except ParseErrors as exc:
            parser_errors = [str(e) for e in exc.errors]
            ast = exc.partial_ast
            result["phases"]["parser"] = {
                "status": "ERROR",
                "errors": parser_errors,
                "tree": ast_to_dict(ast),
            }
            result["timings"]["parser"] = round(time.perf_counter() - t0, 4)
            result["has_errors"] = True
            result["error_phases"].append("parser")
        except ParseError as e:
            parser_errors = [str(e)]
            result["phases"]["parser"] = {
                "status": "ERROR",
                "errors": parser_errors,
                "tree": None,
            }
            result["timings"]["parser"] = round(time.perf_counter() - t0, 4)
            result["has_errors"] = True
            result["error_phases"].append("parser")
        except Exception as e:
            result["phases"]["parser"] = {"status": "ERROR", "errors": [str(e)], "tree": None}
            result["timings"]["parser"] = round(time.perf_counter() - t0, 4)
            result["has_errors"] = True
            result["error_phases"].append("parser")
    else:
        result["phases"]["parser"] = {"status": "SKIPPED", "errors": ["No tokens"]}

    # Phase 3: Semantic
    t0 = time.perf_counter()
    if ast is not None:
        try:
            raw_sem = SemanticAnalyzer().analyze(ast)
            sem_errors = [str(e) for e in raw_sem]
            result["phases"]["semantic"] = {
                "status": "ERROR" if sem_errors else "OK",
                "errors": sem_errors,
            }
            result["timings"]["semantic"] = round(time.perf_counter() - t0, 4)
            if sem_errors:
                result["has_errors"] = True
                result["error_phases"].append("semantic")
        except Exception as e:
            result["phases"]["semantic"] = {"status": "ERROR", "errors": [str(e)]}
            result["timings"]["semantic"] = round(time.perf_counter() - t0, 4)
            result["has_errors"] = True
            result["error_phases"].append("semantic")
    else:
        result["phases"]["semantic"] = {"status": "SKIPPED", "errors": ["No AST"]}

    # LLM repair layer on errors
    if result["has_errors"]:
        try:
            has_lex, has_par = bool(lexer_errors), bool(parser_errors)
            if has_lex or has_par:
                all_errors = (
                    [f"[Lexer]    {e}" for e in lexer_errors] +
                    [f"[Parser]   {e}" for e in parser_errors] +
                    [f"[Semantic] {e}" for e in sem_errors]
                )
                llm_res = run_llm_layer(
                    source_code=code,
                    error_type="syntax",
                    phase="Lexer" if has_lex else "Parser",
                    error_message="\n".join(all_errors),
                    save_to_disk=False,
                )
            else:
                all_errors = [f"[Semantic] {e}" for e in sem_errors]
                llm_res = run_llm_layer(
                    source_code=code,
                    error_type="semantic",
                    phase="Semantic",
                    errors=all_errors,
                    save_to_disk=False,
                )
            result["phases"]["llm"] = {"status": "OK", "output": llm_res}
        except Exception as e:
            result["phases"]["llm"] = {"status": "ERROR", "error": str(e), "output": None}
        return result

    # Phase 4-6: IR -> Optimizer -> Assembly
    try:
        t0 = time.perf_counter()
        ir = IRGenerator().generate(ast)
        result["phases"]["ir"] = {
            "status": "OK",
            "instr_count": len(ir),
            "instructions": [instr_to_dict(i) for i in ir],
        }
        result["timings"]["ir"] = round(time.perf_counter() - t0, 4)

        t0 = time.perf_counter()
        strategies = OptStrategy().predict(ir)
        ir_opt = Optimizer().optimize(ir, strategies)
        result["phases"]["optimizer"] = {
            "status": "OK",
            "strategies_applied": strategies,
            "original_count": len(ir),
            "optimized_count": len(ir_opt),
            "instructions": [instr_to_dict(i) for i in ir_opt],
        }
        result["timings"]["optimizer"] = round(time.perf_counter() - t0, 4)

        t0 = time.perf_counter()
        asm_lines = AssemblyGenerator().generate(ir_opt)
        result["phases"]["assembly"] = {
            "status": "OK",
            "line_count": len(asm_lines),
            "lines": asm_lines,
        }
        result["timings"]["assembly"] = round(time.perf_counter() - t0, 4)
    except Exception as e:
        result["phases"]["ir"] = {"status": "ERROR", "errors": [str(e)]}
        for ph in ["optimizer", "assembly"]:
            if ph not in result["phases"]:
                result["phases"][ph] = {"status": "SKIPPED"}

    return result

def banner(phase, ok=True):
    mark = "✓" if ok else "✗"
    print(f"  [{mark}] {phase}")

# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run(input_file: Path):
    print(f"\n{'='*55}")
    print(f"  Compiler Pipeline")
    print(f"  Input : {input_file}")
    print(f"{'='*55}")

    results = {}

    if not input_file.exists():
        print(f"\n[ERROR] File not found: {input_file}")
        sys.exit(1)

    with open(input_file, encoding="utf-8") as f:
        code = f.read()

    print(f"\n  Source: {len(code.splitlines())} lines, {len(code)} chars\n")
    print("  Phases:")

    # Accumulated errors per phase — used at the end to call the LLM once
    # with the full picture.
    lexer_errors  = []   # list[str]
    parser_errors = []   # list[str]
    sem_errors    = []   # list[str]

    # ── Phase 1 : Lexer ──────────────────────────────────────────────────────
    t0     = time.perf_counter()
    tokens = None   # may stay None if lex fails completely

    try:
        tokens = Lexer().tokenize(code)
        token_list = [t.to_dict() for t in tokens]
        lexer_data = {
            "phase":       "lexer",
            "token_count": len(token_list),
            "tokens":      token_list,
        }
        path = write_json(lexer_data, "lexer_output.json")
        banner(f"Lexer       → {path.name}  ({len(token_list)} tokens, {time.perf_counter()-t0:.3f}s)")
        results["lexer"] = {"tokens": len(token_list), "file": str(path)}

    except LexerErrors as exc:
        # Collect all lexer errors and grab the partial token list
        lexer_errors = [str(e) for e in exc.errors]
        tokens       = exc.tokens   # partial token list — still useful downstream

        banner(f"Lexer       ({len(lexer_errors)} error(s))", ok=False)
        for e in lexer_errors:
            print(f"             [LEXER ERROR] {e}")

        # Write partial lexer output so we have a record
        token_list = [t.to_dict() for t in tokens]
        lexer_data = {
            "phase":       "lexer",
            "status":      "FAIL",
            "error_count": len(lexer_errors),
            "errors":      lexer_errors,
            "token_count": len(token_list),
            "tokens":      token_list,
        }
        write_json(lexer_data, "lexer_output.json")

    # ── Phase 2 : Parser / AST ───────────────────────────────────────────────
    # Run even when there were lexer errors — use partial tokens.
    t0  = time.perf_counter()
    ast = None

    if tokens is not None:
        try:
            cache = StatementCache()
            hint  = HintModel()
            ast   = Parser(tokens, cache=cache, hint_model=hint).parse()

            ast_data = {
                "phase": "ast",
                "tree":  ast_to_dict(ast),
                "cache_stats": cache.stats() if hasattr(cache, "stats") else {},
            }
            path = write_json(ast_data, "ast_output.json")

            if lexer_errors:
                # Parser succeeded despite lexer errors (partial tokens were enough)
                banner(f"Parser/AST  → {path.name}  ({time.perf_counter()-t0:.3f}s)  [ran on partial tokens]")
            else:
                banner(f"Parser/AST  → {path.name}  ({time.perf_counter()-t0:.3f}s)")
            results["ast"] = {"file": str(path)}

        except ParseErrors as exc:
            parser_errors = [str(e) for e in exc.errors]
            ast           = exc.partial_ast   # partial AST — run semantic on it

            banner(f"Parser/AST  ({len(parser_errors)} error(s))", ok=False)
            for e in parser_errors:
                print(f"             [PARSE ERROR] {e}")

            ast_data = {
                "phase":       "ast",
                "status":      "FAIL",
                "error_count": len(parser_errors),
                "errors":      parser_errors,
                "tree":        ast_to_dict(ast),
            }
            write_json(ast_data, "ast_output.json")

        except ParseError as e:
            # Fallback: single fatal ParseError (shouldn't happen with new Parser
            # but kept for safety)
            parser_errors = [str(e)]
            banner("Parser/AST", ok=False)
            print(f"             [PARSE ERROR] {e}")
            ast_data = {
                "phase": "ast", "status": "FAIL",
                "error_count": 1, "errors": parser_errors,
            }
            write_json(ast_data, "ast_output.json")
    else:
        banner("Parser/AST  (skipped — no tokens)", ok=False)

    # ── Phase 3 : Semantic Analysis ──────────────────────────────────────────
    # Run even when there were parser errors — use partial AST.
    t0 = time.perf_counter()

    if ast is not None:
        raw_sem_errors = SemanticAnalyzer().analyze(ast)
        sem_errors     = [str(e) for e in raw_sem_errors]

        sem_data = {
            "phase":       "semantic",
            "error_count": len(sem_errors),
            "errors":      sem_errors,
            "status":      "FAIL" if sem_errors else "OK",
        }
        path = write_json(sem_data, "semantic_output.json")

        if sem_errors:
            banner(f"Semantic    → {path.name}  ({len(sem_errors)} error(s))", ok=False)
            for e in sem_errors:
                print(f"             {e}")
        else:
            banner(f"Semantic    → {path.name}  (no errors, {time.perf_counter()-t0:.3f}s)")
            results["semantic"] = {"errors": 0, "file": str(path)}
    else:
        banner("Semantic    (skipped — no AST)", ok=False)

    # ── Decide whether to call the LLM and with what ─────────────────────────
    #
    # Rules (matches the user's spec):
    #   - Lexer error(s)   → send Lexer + Parser + Semantic errors to LLM
    #   - Parser error(s) only → send Parser + Semantic errors
    #   - Semantic error(s) only → send Semantic errors
    #
    # The LLM is called once with the full combined error list so it can
    # reason about the whole picture at once.

    has_lexer  = bool(lexer_errors)
    has_parser = bool(parser_errors)
    has_sem    = bool(sem_errors)

    if has_lexer or has_parser or has_sem:
        if has_lexer:
            # Triggered at the Lexer level → gather all three
            all_errors  = (
                [f"[Lexer]    {e}" for e in lexer_errors] +
                [f"[Parser]   {e}" for e in parser_errors] +
                [f"[Semantic] {e}" for e in sem_errors]
            )
            triggered_phase = "Lexer"
        elif has_parser:
            # Triggered at Parser → Parser + Semantic
            all_errors  = (
                [f"[Parser]   {e}" for e in parser_errors] +
                [f"[Semantic] {e}" for e in sem_errors]
            )
            triggered_phase = "Parser"
        else:
            # Only Semantic errors
            all_errors      = [f"[Semantic] {e}" for e in sem_errors]
            triggered_phase = "Semantic"

        # Determine error_type for prompt selection
        # If there are any lexer/parser errors it's a syntax issue;
        # if purely semantic, use the semantic prompt.
        if has_lexer or has_parser:
            error_type    = "syntax"
            error_message = "\n".join(all_errors)
            run_llm_layer(
                source_code=code,
                error_type=error_type,
                phase=triggered_phase,
                error_message=error_message,
            )
        else:
            run_llm_layer(
                source_code=code,
                error_type="semantic",
                phase=triggered_phase,
                errors=all_errors,
            )

        sys.exit(1)

    # ── Phase 4 : IR Generation ───────────────────────────────────────────────
    t0 = time.perf_counter()
    ir = IRGenerator().generate(ast)
    ir_data = {
        "phase":        "ir",
        "instr_count":  len(ir),
        "instructions": [instr_to_dict(i) for i in ir],
    }
    path = write_json(ir_data, "ir_output.json")
    banner(f"IR Gen      → {path.name}  ({len(ir)} instructions, {time.perf_counter()-t0:.3f}s)")
    results["ir"] = {"instructions": len(ir), "file": str(path)}

    # ── Phase 5 : Optimizer ───────────────────────────────────────────────────
    t0         = time.perf_counter()
    strategies = OptStrategy().predict(ir)
    ir_opt     = Optimizer().optimize(ir, strategies)
    opt_data   = {
        "phase":              "optimizer",
        "strategies_applied": strategies,
        "original_count":     len(ir),
        "optimized_count":    len(ir_opt),
        "instructions":       [instr_to_dict(i) for i in ir_opt],
    }
    path = write_json(opt_data, "optimizer_output.json")
    banner(f"Optimizer   → {path.name}  (strategies: {strategies}, {time.perf_counter()-t0:.3f}s)")
    results["optimizer"] = {"strategies": strategies, "file": str(path)}

    # ── Phase 6 : Assembly ────────────────────────────────────────────────────
    t0        = time.perf_counter()
    asm_lines = AssemblyGenerator().generate(ir_opt)
    asm_data  = {
        "phase":      "assembly",
        "line_count": len(asm_lines),
        "lines":      asm_lines,
    }
    path = write_json(asm_data, "assembly_output.json")
    banner(f"Assembly    → {path.name}  ({len(asm_lines)} lines, {time.perf_counter()-t0:.3f}s)")
    results["assembly"] = {"lines": len(asm_lines), "file": str(path)}

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print("  Pipeline complete — all phases passed.")
    print(f"  Output files written to: {ROOT}")
    print(f"{'='*55}\n")

# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "test.txt"
    run(input_file)
