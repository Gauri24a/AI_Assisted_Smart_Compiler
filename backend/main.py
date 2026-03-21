from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.lexer import Lexer
from src.parser import Parser
from src.semantic_analyzer import SemanticAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"
ROOT_SIMPLE_TEST = PROJECT_ROOT / "simple_test.txt"
RUN_COMPILER = PROJECT_ROOT / "run_compiler.py"
OUTPUT_JSON = PROJECT_ROOT / "output.json"


class RunRequest(BaseModel):
    file_path: str


def strip_comments(code: str) -> str:
    """Remove single-line and multi-line comments for clean UI preview."""
    without_blocks = re.sub(r"/\*[\s\S]*?\*/", "", code)
    lines = []
    for line in without_blocks.splitlines():
        line = re.sub(r"//.*$", "", line).rstrip()
        if line.strip():
            lines.append(line)
    return "\n".join(lines)


def discover_source_files() -> list[dict[str, str]]:
    files: list[Path] = []

    if EXAMPLES_DIR.exists():
        files.extend(sorted([p for p in EXAMPLES_DIR.glob("*.txt") if p.is_file()]))

    if ROOT_SIMPLE_TEST.exists():
        files.append(ROOT_SIMPLE_TEST)

    unique = []
    seen = set()
    for file in files:
        rel = file.relative_to(PROJECT_ROOT).as_posix()
        if rel not in seen:
            unique.append(file)
            seen.add(rel)

    result: list[dict[str, str]] = []
    for file in unique:
        rel = file.relative_to(PROJECT_ROOT).as_posix()
        result.append(
            {
                "name": file.name,
                "path": rel,
                "content": strip_comments(file.read_text(encoding="utf-8", errors="ignore")),
            }
        )
    return result


def parse_phase_logs(stdout_text: str) -> dict[str, str]:
    lines = stdout_text.splitlines()
    markers = {
        "lexer": "1. Running Lexer...",
        "parser": "2. Running Parser...",
        "classification": "3. AST generated. Running AI classification...",
        "semantic": "4. Running Semantic Analyzer",
        "llm": "5. Requesting Gemini",
    }

    starts: dict[str, int] = {}
    for idx, line in enumerate(lines):
        for key, marker in markers.items():
            if marker in line and key not in starts:
                starts[key] = idx

    ordered = sorted(starts.items(), key=lambda item: item[1])
    segments: dict[str, str] = {k: "" for k in markers}

    for i, (name, start_idx) in enumerate(ordered):
        end_idx = ordered[i + 1][1] if i + 1 < len(ordered) else len(lines)
        segments[name] = "\n".join(lines[start_idx:end_idx]).strip()

    return segments


def run_pipeline_for_file(file_path: str) -> dict[str, Any]:
    requested_path = file_path.replace("\\", "/")
    full_path = PROJECT_ROOT / requested_path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"Source file not found: {requested_path}")

    allowed = {item["path"] for item in discover_source_files()}
    if requested_path not in allowed:
        raise HTTPException(status_code=400, detail="File path is not allowed.")

    command = [sys.executable, str(RUN_COMPILER), requested_path, "output.json"]
    proc = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )

    compiler_output: dict[str, Any] = {}
    if OUTPUT_JSON.exists():
        try:
            compiler_output = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
        except Exception:
            compiler_output = {}

    actual_source = str(compiler_output.get("source_file", "")).replace("\\", "/").lstrip("./")
    expected_source = requested_path.lstrip("./")
    if not compiler_output or actual_source != expected_source:
        compiler_output = {
            "source_file": requested_path,
            "predictions": [],
            "semantic": None,
            "llm_feedback": None,
            "error": (
                proc.stderr.strip()
                or proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "Pipeline did not produce output.json"
            ),
        }

    latency_comparison = benchmark_latency_comparison(full_path, compiler_output)

    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "phase_logs": parse_phase_logs(proc.stdout),
        "compiler_output": compiler_output,
        "latency_comparison": latency_comparison,
    }


def run_traditional_to_semantic(source_code: str) -> dict[str, Any]:
    """Traditional pipeline benchmark (lexer + parser + semantic, no ML phase)."""
    t0 = time.perf_counter()

    lex_start = time.perf_counter()
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    lex_ms = round((time.perf_counter() - lex_start) * 1000, 2)
    if lexer.errors:
        return {
            "status": "error",
            "error": "Lexical errors in traditional pipeline",
            "lexer_ms": lex_ms,
            "parser_ms": 0.0,
            "semantic_ms": 0.0,
            "to_semantic_ms": lex_ms,
        }

    parse_start = time.perf_counter()
    try:
        parser = Parser(tokens)
        ast = parser.parse()
    except Exception as exc:
        parse_ms = round((time.perf_counter() - parse_start) * 1000, 2)
        return {
            "status": "error",
            "error": f"Parser error: {exc}",
            "lexer_ms": lex_ms,
            "parser_ms": parse_ms,
            "semantic_ms": 0.0,
            "to_semantic_ms": round(lex_ms + parse_ms, 2),
        }
    parse_ms = round((time.perf_counter() - parse_start) * 1000, 2)

    sem_start = time.perf_counter()
    sem = SemanticAnalyzer()
    sem_report = sem.analyze(ast, classification_hints=None)
    sem_ms = round((time.perf_counter() - sem_start) * 1000, 2)

    to_semantic_ms = round(lex_ms + parse_ms + sem_ms, 2)
    total_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "status": sem_report.get("status", "ok"),
        "issues_count": len(sem_report.get("issues", [])),
        "lexer_ms": lex_ms,
        "parser_ms": parse_ms,
        "semantic_ms": sem_ms,
        "to_semantic_ms": to_semantic_ms,
        "total_ms": total_ms,
    }


def benchmark_latency_comparison(full_path: Path, compiler_output: dict[str, Any]) -> dict[str, Any]:
    try:
        source_code = full_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return {"status": "error", "reason": f"Cannot read source for benchmark: {exc}"}

    traditional = run_traditional_to_semantic(source_code)
    ml_timings = compiler_output.get("timings", {}) if isinstance(compiler_output, dict) else {}
    ml_to_sem = ml_timings.get("to_semantic_ms")
    trad_to_sem = traditional.get("to_semantic_ms")

    if ml_to_sem is None or trad_to_sem is None:
        return {
            "status": "partial",
            "ml": ml_timings,
            "traditional": traditional,
            "reason": "Missing one side of timing data",
        }

    diff = round(trad_to_sem - ml_to_sem, 2)
    faster = "ml_assisted" if diff > 0 else ("traditional" if diff < 0 else "equal")
    speedup_pct = round((abs(diff) / trad_to_sem) * 100, 2) if trad_to_sem else 0.0

    return {
        "status": "ok",
        "ml": {
            "to_semantic_ms": ml_to_sem,
            "classification_source": compiler_output.get("classification_source", "unknown"),
            "breakdown": ml_timings,
        },
        "traditional": traditional,
        "difference_ms": diff,
        "faster": faster,
        "speedup_percent_vs_traditional": speedup_pct,
    }


app = FastAPI(title="AI Assisted Smart Compiler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/files")
def get_files() -> dict[str, Any]:
    return {"files": discover_source_files()}


@app.post("/api/run")
def run_compiler(request: RunRequest) -> dict[str, Any]:
    return run_pipeline_for_file(request.file_path.replace("\\", "/"))
