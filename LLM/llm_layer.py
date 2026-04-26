"""
llm_layer.py — AI Repair Layer (Gemini)
=========================================
Side feature that activates when the compiler pipeline encounters
a Lexer, Parser, or Semantic error.

Reads up to 5 Gemini API keys from the .env file (project root).
Keys are tried in order — if one fails with 429/503, the next is used.
If a key is exhausted/unavailable, a clear warning is printed.

.env format:
    GEMINI_API_KEY_1=your_first_key
    GEMINI_API_KEY_2=your_second_key
    GEMINI_API_KEY_3=your_third_key
    GEMINI_API_KEY_4=your_fourth_key
    GEMINI_API_KEY_5=your_fifth_key

Output is saved to  <project_root>/llm_output.json
and printed to the terminal.
"""

import json
import datetime
import urllib.request
import urllib.error
from pathlib import Path

from prompts import build_syntax_prompt, build_semantic_prompt

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_MODEL    = "gemini-2.5-flash"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
_ROOT        = Path(__file__).resolve().parent.parent   # project root
_NUM_KEYS    = 5
# HTTP status codes that mean "this key is rate-limited / quota exhausted"
_QUOTA_CODES = {429, 503}


# ── API key loader ────────────────────────────────────────────────────────────
def _load_api_keys() -> list[str]:
    """
    Load GEMINI_API_KEY_1 ... GEMINI_API_KEY_5 from <project_root>/.env
    Returns a list of keys in order; skips missing/empty slots.
    """
    env_path = _ROOT / ".env"
    if not env_path.exists():
        raise FileNotFoundError(
            f"[LLM] .env file not found at {env_path}\n"
            "      Create it and add:\n"
            "        GEMINI_API_KEY_1=your_first_key\n"
            "        GEMINI_API_KEY_2=your_second_key  <- up to 5"
        )

    raw: dict[str, str] = {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            raw[name.strip()] = value.strip().strip('"').strip("'")

    keys = []
    for i in range(1, _NUM_KEYS + 1):
        key = raw.get(f"GEMINI_API_KEY_{i}", "")
        if key:
            keys.append(key)

    if not keys:
        raise ValueError(
            "[LLM] No API keys found in .env\n"
            "      Add at least one key as:  GEMINI_API_KEY_1=your_key_here"
        )

    return keys


# ── Gemini call ───────────────────────────────────────────────────────────────
def _call_gemini(prompt: str, api_key: str) -> str:
    """Send prompt to Gemini REST API and return the text response."""
    url     = f"{GEMINI_ENDPOINT}?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":     0.3,
            "maxOutputTokens": 4096,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        err = RuntimeError(f"[LLM] Gemini API error {e.code}: {body}")
        err.status_code = e.code
        raise err
    except urllib.error.URLError as e:
        raise RuntimeError(f"[LLM] Network error reaching Gemini: {e.reason}") from e

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"[LLM] Unexpected Gemini response shape: {data}") from e


# ── Key-rotating caller ───────────────────────────────────────────────────────
def _call_gemini_with_fallback(prompt: str, api_keys: list[str]) -> tuple[str, int]:
    """
    Try each key in order.  Returns (response_text, key_index_used).
    Raises RuntimeError if all keys fail.
    """
    last_error = None

    for idx, key in enumerate(api_keys, start=1):
        key_label = f"GEMINI_API_KEY_{idx}"
        print(f"  [LLM] Trying {key_label} ...")

        try:
            text = _call_gemini(prompt, key)
            print(f"  [LLM] Success with {key_label}")
            return text, idx

        except RuntimeError as e:
            status = getattr(e, "status_code", None)
            last_error = e

            if status in _QUOTA_CODES:
                print()
                print("  " + "!" * 51)
                print(f"  !!!  {key_label} is EXHAUSTED or UNAVAILABLE (HTTP {status}).")
                print(f"  !!!  Please replace {key_label} in your .env file.")
                print("  " + "!" * 51)
                if idx < len(api_keys):
                    print(f"  [LLM] Rotating to next key...\n")
                else:
                    print("  [LLM] No more keys to try.\n")
            else:
                print(f"  [LLM] {key_label} failed: {e}")
                if idx < len(api_keys):
                    print(f"  [LLM] Trying next key...\n")

    raise RuntimeError(
        f"[LLM] All {len(api_keys)} API key(s) failed. Last error: {last_error}"
    )


# ── Public interface ──────────────────────────────────────────────────────────
def run_llm_layer(
    *,
    source_code:   str,
    error_type:    str,          # "syntax" | "semantic"
    phase:         str,          # "Lexer" | "Parser" | "Semantic"
    error_message: str  = "",    # single string for syntax errors
    errors:        list = None,  # list of strings for semantic errors
    save_to_disk:  bool = True,
) -> dict:
    """
    Main entry point called from main.py when a phase fails.
    Returns a result dict that is also written to llm_output.json.
    """
    print("\n" + "─" * 55)
    print("  [LLM] AI Repair Layer — activating Gemini")
    print("─" * 55)

    # ── Load keys ─────────────────────────────────────────────
    try:
        api_keys = _load_api_keys()
        print(f"  [LLM] {len(api_keys)} API key(s) loaded from .env")
    except (FileNotFoundError, ValueError) as e:
        print(f"\n{e}")
        return _write_error_json(str(e), phase, save_to_disk)

    # ── Build prompt ──────────────────────────────────────────
    if error_type == "syntax":
        prompt = build_syntax_prompt(source_code, error_message, phase)
    else:
        prompt = build_semantic_prompt(source_code, errors or [])

    print(f"  [LLM] Sending {error_type} error context to Gemini...")

    # ── Call Gemini (with key rotation) ──────────────────────
    try:
        response_text, key_used_idx = _call_gemini_with_fallback(prompt, api_keys)
    except RuntimeError as e:
        print(f"\n{e}")
        return _write_error_json(str(e), phase, save_to_disk)

    # ── Build result ──────────────────────────────────────────
    result = {
        "phase":          "llm_repair",
        "triggered_by":   phase,
        "error_type":     error_type,
        "timestamp":      datetime.datetime.now().isoformat(),
        "gemini_model":   GEMINI_MODEL,
        "api_key_used":   f"GEMINI_API_KEY_{key_used_idx}",
        "input_errors":   [e for e in error_message.split("\n") if e.strip()] if error_type == "syntax" else (errors or []),
        "llm_response":   response_text,
    }

    # ── Save JSON ─────────────────────────────────────────────
    if save_to_disk:
        out_path = _ROOT / "llm_output.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"  [LLM] Response saved → {out_path.name}\n")
    else:
        print(f"  [LLM] Response generated (API mode)\n")
    print("─" * 55)
    print("  GEMINI ANALYSIS")
    print("─" * 55)
    print(response_text)
    print("─" * 55 + "\n")

    return result


# ── Internal helper ───────────────────────────────────────────────────────────
def _write_error_json(message: str, phase: str, save_to_disk: bool = True) -> dict:
    """Write a failure record to llm_output.json when Gemini can't be reached."""
    result = {
        "phase":        "llm_repair",
        "triggered_by": phase,
        "error_type":   "llm_unavailable",
        "timestamp":    datetime.datetime.now().isoformat(),
        "llm_response": None,
        "error":        message,
    }
    if save_to_disk:
        out_path = _ROOT / "llm_output.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"  [LLM] Failure record saved → {out_path.name}")
    else:
        print(f"  [LLM] Failure record generated (API mode)")
    return result