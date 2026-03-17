from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"
ROOT_SIMPLE_TEST = PROJECT_ROOT / "simple_test.txt"
RUN_COMPILER = PROJECT_ROOT / "run_compiler.py"
OUTPUT_JSON = PROJECT_ROOT / "output.json"


class RunRequest(BaseModel):
    file_path: str


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
                "content": file.read_text(encoding="utf-8", errors="ignore"),
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
    full_path = PROJECT_ROOT / file_path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"Source file not found: {file_path}")

    allowed = {item["path"] for item in discover_source_files()}
    if file_path.replace("\\", "/") not in allowed:
        raise HTTPException(status_code=400, detail="File path is not allowed.")

    command = [sys.executable, str(RUN_COMPILER), file_path, "output.json"]
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

    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "phase_logs": parse_phase_logs(proc.stdout),
        "compiler_output": compiler_output,
    }


app = FastAPI(title="AI Assisted Smart Compiler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/files")
def get_files() -> dict[str, Any]:
    return {"files": discover_source_files()}


@app.post("/api/run")
def run_compiler(request: RunRequest) -> dict[str, Any]:
    return run_pipeline_for_file(request.file_path.replace("\\", "/"))
