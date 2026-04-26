from Nodes import (Program, Assign, BinOp, UnaryOp, Identifier,
                   Literal, FuncDef, FuncCall, Return, If, While, For, Pass)


class ParseError(Exception):
    def __init__(self, msg, line):
        super().__init__(f"line {line}: {msg}")


class ParseErrors(Exception):
    """Raised when the Parser encounters one or more errors.

    All errors are collected (error-recovery skips to the next statement
    after each failure) so the full error set is reported at once.
    A partial AST is attached as ``exc.partial_ast`` so semantic analysis
    can still run on the well-formed parts.
    """
    def __init__(self, errors: list, partial_ast):
        self.errors      = errors
        self.partial_ast = partial_ast
        msgs = "\n".join(str(e) for e in errors)
        super().__init__(f"{len(errors)} parse error(s):\n{msgs}")


class Parser:
    PRECEDENCE = {
        "or": 1, "and": 2,
        "==": 3, "!=": 3, "<": 3, ">": 3, "<=": 3, ">=": 3,
        "+": 4, "-": 4,
        "*": 5, "/": 5, "//": 5, "%": 5,
        "**": 6,
    }

    def __init__(self, tokens, cache=None, hint_model=None):
        self.tokens  = tokens
        self.pos     = 0
        self._cache  = cache
        self._hint   = hint_model

    def parse(self):
        body   = []
        errors = []

        while not self._at("EOF"):
            self._skip("NEWLINE", "INDENT", "DEDENT")
            if self._at("EOF"):
                break
            try:
                body.append(self._stmt())
            except ParseError as e:
                errors.append(e)
                # Error recovery: skip tokens until the next statement boundary
                self._recover()

        ast = Program(body)
        if errors:
            raise ParseErrors(errors, ast)
        return ast

    def _recover(self):
        """Skip tokens until we reach a safe restart point (next statement)."""
        # Skip until NEWLINE, DEDENT, or a keyword that starts a new statement,
        # then consume the NEWLINE so the next iteration starts cleanly.
        stmt_starters = {"def", "return", "if", "elif", "else",
                         "while", "for", "pass"}
        while not self._at("EOF"):
            t = self._peek()
            if t.type in ("NEWLINE", "DEDENT"):
                self._eat()
                return
            if t.type == "KEYWORD" and t.value in stmt_starters:
                return   # let the outer loop handle it
            self._eat()

    # ── token helpers ──────────────────────────────────────────────────

    def _peek(self):    return self.tokens[self.pos]
    def _eat(self):     t = self.tokens[self.pos]; self.pos += 1; return t
    def _at(self, *t):  return self._peek().type in t
    def _val(self, *v): return self._peek().value in v

    def _expect(self, type, value=None):
        t = self._eat()
        if t.type != type or (value and t.value != value):
            raise ParseError(f"expected {value or type}, got {t.value!r}", t.line)
        return t

    def _skip(self, *types):
        while self._peek().type in types:
            self._eat()

    # ── ML hooks ───────────────────────────────────────────────────────

    def _keys(self):
        hint_key, cache_key, i = [], [], self.pos
        while i < len(self.tokens) and self.tokens[i].type not in ("NEWLINE", "EOF", "INDENT", "DEDENT"):
            t = self.tokens[i]
            if i == self.pos and t.type == "KEYWORD":
                hint_key.append(("KEYWORD", t.value))
            else:
                hint_key.append(t.type)
            cache_key.append((t.type, t.value))
            i += 1
        return tuple(hint_key), tuple(cache_key)

    def _skip_stmt_tokens(self):
        while not self._at("NEWLINE", "EOF", "INDENT", "DEDENT"):
            self._eat()
        if self._at("NEWLINE"):
            self._eat()

    def _node_label(self, node):
        return {
            "FuncDef": "funcdef", "Return": "return", "If": "if",
            "While": "while", "For": "for", "Pass": "pass",
            "Assign": "assignment",
        }.get(type(node).__name__, "expr")

    def _stmt(self):
        hint_key, cache_key = self._keys()

        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._skip_stmt_tokens()
                return cached

        if self._hint is not None:
            saved = self.pos
            handler = {
                "funcdef": self._funcdef, "return": self._return,
                "if": self._if, "while": self._while,
                "for": self._for, "pass": self._pass,
                "assignment": self._assign_or_expr, "expr": self._assign_or_expr,
            }.get(self._hint.predict(hint_key))
            if handler:
                try:
                    node = handler()
                    self._hint.learn(hint_key, self._node_label(node))
                    if self._cache is not None:
                        self._cache.put(cache_key, node)
                    return node
                except ParseError:
                    self.pos = saved

        node = self._dispatch()
        if self._hint is not None:
            self._hint.learn(hint_key, self._node_label(node))
        if self._cache is not None:
            self._cache.put(cache_key, node)
        return node

    def _dispatch(self):
        t = self._peek()
        if t.type == "KEYWORD":
            if t.value == "def":    return self._funcdef()
            if t.value == "return": return self._return()
            if t.value == "if":     return self._if()
            if t.value == "while":  return self._while()
            if t.value == "for":    return self._for()
            if t.value == "pass":   return self._pass()
        return self._assign_or_expr()

    # ── statements ─────────────────────────────────────────────────────

    def _assign_or_expr(self):
        line = self._peek().line
        expr = self._expr()
        if self._at("OPERATOR") and self._val("="):
            self._eat()
            value = self._expr()
            self._skip("NEWLINE")
            return Assign(expr, value, line)
        self._skip("NEWLINE")
        return expr

    def _block(self):
        self._expect("INDENT")
        stmts = []
        while not self._at("DEDENT", "EOF"):
            self._skip("NEWLINE")
            if self._at("DEDENT", "EOF"):
                break
            stmts.append(self._stmt())
        if self._at("DEDENT"):
            self._eat()
        return stmts

    def _funcdef(self):
        line = self._peek().line
        self._eat()
        name = self._expect("IDENTIFIER").value
        self._expect("DELIMITER", "(")
        params = []
        while not (self._at("DELIMITER") and self._val(")")):
            params.append(self._expect("IDENTIFIER").value)
            if self._at("DELIMITER") and self._val(","):
                self._eat()
        self._expect("DELIMITER", ")")
        self._expect("DELIMITER", ":")
        self._skip("NEWLINE")
        return FuncDef(name, params, self._block(), line)

    def _return(self):
        line = self._eat().line
        value = self._expr()
        self._skip("NEWLINE")
        return Return(value, line)

    def _if(self):
        line = self._eat().line
        cond = self._expr()
        self._expect("DELIMITER", ":")
        self._skip("NEWLINE")
        body = self._block()
        elifs, else_body = [], []
        while self._at("KEYWORD") and self._val("elif"):
            self._eat()
            ec = self._expr()
            self._expect("DELIMITER", ":")
            self._skip("NEWLINE")
            elifs.append((ec, self._block()))
        if self._at("KEYWORD") and self._val("else"):
            self._eat()
            self._expect("DELIMITER", ":")
            self._skip("NEWLINE")
            else_body = self._block()
        return If(cond, body, elifs, else_body, line)

    def _while(self):
        line = self._eat().line
        cond = self._expr()
        self._expect("DELIMITER", ":")
        self._skip("NEWLINE")
        return While(cond, self._block(), line)

    def _for(self):
        line = self._eat().line
        target = Identifier(self._expect("IDENTIFIER").value, line)
        self._expect("KEYWORD", "in")
        iterable = self._expr()
        self._expect("DELIMITER", ":")
        self._skip("NEWLINE")
        return For(target, iterable, self._block(), line)

    def _pass(self):
        line = self._eat().line
        self._skip("NEWLINE")
        return Pass(line)

    # ── expressions ────────────────────────────────────────────────────

    def _expr(self):
        return self._binop(0)

    def _binop(self, min_prec):
        left = self._unary()
        while True:
            t = self._peek()
            prec = self.PRECEDENCE.get(t.value if t.type in ("OPERATOR", "KEYWORD") else "", -1)
            if prec < min_prec:
                break
            op    = self._eat().value
            right = self._binop(prec + 1)
            left  = BinOp(left, op, right)
        return left

    def _unary(self):
        t = self._peek()
        if t.type == "OPERATOR" and t.value == "-":
            self._eat(); return UnaryOp("-", self._unary())
        if t.type == "KEYWORD" and t.value == "not":
            self._eat(); return UnaryOp("not", self._unary())
        return self._primary()

    def _primary(self):
        t = self._peek()
        if t.type == "INTEGER":  self._eat(); return Literal(int(t.value), "int")
        if t.type == "FLOAT":    self._eat(); return Literal(float(t.value), "float")
        if t.type == "STRING":   self._eat(); return Literal(t.value[1:-1], "str")
        if t.type == "KEYWORD" and t.value in ("True", "False"):
            self._eat(); return Literal(t.value == "True", "bool")
        if t.type == "KEYWORD" and t.value == "None":
            self._eat(); return Literal(None, "none")
        if t.type == "IDENTIFIER":
            self._eat()
            if self._at("DELIMITER") and self._val("("):
                self._eat()
                args = []
                while not (self._at("DELIMITER") and self._val(")")):
                    args.append(self._expr())
                    if self._at("DELIMITER") and self._val(","):
                        self._eat()
                self._expect("DELIMITER", ")")
                return FuncCall(t.value, args, t.line)
            return Identifier(t.value, t.line)
        if t.type == "DELIMITER" and t.value == "(":
            self._eat()
            expr = self._expr()
            self._expect("DELIMITER", ")")
            return expr
        raise ParseError(f"unexpected token {t.value!r}", t.line)
