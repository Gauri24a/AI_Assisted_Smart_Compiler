"""
prompts.py — Gemini prompt templates for each error type.

Two distinct prompts:
  - build_syntax_prompt()   : for LexerError / ParseError
  - build_semantic_prompt() : for SemanticAnalyzer errors
"""


def build_syntax_prompt(source_code: str, error_message: str, phase: str) -> str:
    """
    Prompt for syntax-level errors (Lexer or Parser failures).
    We have limited structured info here — just the raw error string
    and the source — so we ask Gemini to reason about the syntax itself.
    """
    return f"""You are an expert programming language compiler assistant.

A source file failed during the **{phase} phase** (syntax analysis) with the following error:

ERROR:
{error_message}

SOURCE CODE:
```
{source_code}
```

Your job:
1. Clearly explain in plain English what the syntax error means and why it occurred.
2. Identify the exact line(s) involved if possible.
3. Provide a corrected version of the problematic statement(s) — not the entire file, just the fixed line(s) with a brief comment explaining what changed.

Format your response exactly like this:

### Error Explanation
<your plain-English explanation here>

### Likely Cause
<what the programmer probably intended vs what they wrote>

### Suggested Fix
```
<corrected line(s) here>
```

### What Changed
<one or two sentences summarising the correction>
"""


def build_semantic_prompt(source_code: str, errors: list[str]) -> str:
    """
    Prompt for semantic errors caught by SemanticAnalyzer.
    We have rich structured info: line numbers, error messages, types.
    """
    error_block = "\n".join(f"  - {e}" for e in errors)
    error_count = len(errors)

    return f"""You are an expert programming language compiler assistant.

A source file passed syntax analysis but failed **semantic analysis** with \
{error_count} error(s):

SEMANTIC ERRORS:
{error_block}

SOURCE CODE:
```
{source_code}
```

Your job:
1. Explain each semantic error in plain English — what it means and why it is invalid.
2. For each error, quote the exact line from the source and show what the corrected line should be.
3. If errors are related (e.g. a missing declaration causing a cascade), explain the relationship.

Format your response exactly like this:

### Semantic Error Analysis

For each error, use this structure:

#### Error N: <short title>
**Line:** <line number or 'unknown'>
**Problem:** <plain-English explanation>
**Original:**
```
<the bad line>
```
**Suggested Fix:**
```
<corrected line>
```

---

### Summary
<overall summary: what went wrong and the key things to fix>
"""