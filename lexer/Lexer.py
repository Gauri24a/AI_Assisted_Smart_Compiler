from Tokens import KEYWORDS, OPERATORS, DELIMITERS


class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"line {line}, col {col}: {msg}")


class LexerErrors(Exception):
    """Raised when the Lexer finds one or more errors during tokenisation.

    Unlike LexerError (single-shot raise), this collects ALL errors found
    in the source so the pipeline can report everything at once.
    The partial token list produced before/around the errors is attached
    as ``exc.tokens`` so downstream phases can still attempt their checks.
    """
    def __init__(self, errors: list, tokens: list):
        self.errors = errors          # list of LexerError instances
        self.tokens = tokens          # partial (but usable) token list
        msgs = "\n".join(str(e) for e in errors)
        super().__init__(f"{len(errors)} lexer error(s):\n{msgs}")


class Token:
    def __init__(self, type, value, line, col):
        self.type  = type
        self.value = value
        self.line  = line
        self.col   = col

    def to_dict(self):
        return {"type": self.type, "value": self.value, "line": self.line, "col": self.col}

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"


class Lexer:
    def tokenize(self, src):
        tokens, i, line, col = [], 0, 1, 1
        indent_stack, bracket_depth = [0], 0
        n = len(src)
        errors = []   # collect errors instead of raising immediately

        def emit(type, value):
            tokens.append(Token(type, value, line, col))

        while i < n:
            ch = src[i]

            if ch == "\n":
                if bracket_depth == 0 and tokens and tokens[-1].type not in ("NEWLINE", "INDENT", "DEDENT"):
                    emit("NEWLINE", "\n")
                line += 1; col = 1; i += 1

                j, spaces = i, 0
                while j < n and src[j] in (" ", "\t"):
                    spaces += 4 if src[j] == "\t" else 1
                    j += 1

                if j >= n or src[j] in ("\n", "#"):
                    continue

                if bracket_depth == 0:
                    cur = indent_stack[-1]
                    if spaces > cur:
                        indent_stack.append(spaces)
                        emit("INDENT", spaces)
                    elif spaces < cur:
                        while indent_stack[-1] > spaces:
                            indent_stack.pop()
                            emit("DEDENT", indent_stack[-1])
                        if indent_stack[-1] != spaces:
                            # Record bad-indent error and continue scanning
                            errors.append(LexerError("bad indent", line, 1))

                col += spaces; i = j
                continue

            if ch in (" ", "\t"):
                col += 1; i += 1; continue

            if ch == "#":
                while i < n and src[i] != "\n": i += 1
                continue

            if ch in ('"', "'"):
                j = i + 1
                while j < n and src[j] != ch:
                    if src[j] == "\n":
                        errors.append(LexerError("unterminated string", line, col))
                        i = j   # jump to the newline; outer loop will handle it
                        break
                    j += 1
                else:
                    if j >= n:
                        errors.append(LexerError("unterminated string", line, col))
                        i = j
                        continue
                    val = src[i:j+1]
                    emit("STRING", val); col += len(val); i = j + 1
                continue

            if ch.isdigit():
                j = i
                while j < n and src[j].isdigit(): j += 1
                if j < n and src[j] == "." and j+1 < n and src[j+1].isdigit():
                    j += 1
                    while j < n and src[j].isdigit(): j += 1
                val = src[i:j]
                emit("FLOAT" if "." in val else "INTEGER", val); col += len(val); i = j
                continue

            if ch.isalpha() or ch == "_":
                j = i
                while j < n and (src[j].isalnum() or src[j] == "_"): j += 1
                val = src[i:j]
                emit("KEYWORD" if val in KEYWORDS else "IDENTIFIER", val); col += len(val); i = j
                continue

            matched = False
            for op in OPERATORS:
                if src[i:i+len(op)] == op:
                    emit("OPERATOR", op); col += len(op); i += len(op); matched = True; break
            if matched: continue

            if ch in DELIMITERS:
                emit("DELIMITER", ch)
                if ch in ("(", "["): bracket_depth += 1
                elif ch in (")", "]"): bracket_depth = max(0, bracket_depth - 1)
                col += 1; i += 1
                continue

            # Unknown character — record and skip so scanning continues
            errors.append(LexerError(f"unknown char {ch!r}", line, col))
            col += 1; i += 1

        # Finalise token stream
        if tokens and tokens[-1].type not in ("NEWLINE", "INDENT", "DEDENT"):
            emit("NEWLINE", "\n")
        while len(indent_stack) > 1:
            indent_stack.pop()
            emit("DEDENT", indent_stack[-1])
        emit("EOF", "")

        if errors:
            raise LexerErrors(errors, tokens)

        return tokens
