import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "AST"))

from Nodes import (Program, Assign, BinOp, UnaryOp, Identifier,
                   Literal, FuncDef, FuncCall, Return, If, While, For, Pass)


class SemanticError(Exception):
    def __init__(self, msg, line):
        super().__init__(f"line {line}: {msg}")


BUILTINS = {"print", "range", "len", "int", "float", "str", "bool", "input"}

TYPE_OPS = {
    ("int",   "+", "int"):   "int",
    ("int",   "-", "int"):   "int",
    ("int",   "*", "int"):   "int",
    ("int",   "/", "int"):   "float",
    ("int",   "//", "int"):  "int",
    ("int",   "%", "int"):   "int",
    ("int",   "**", "int"):  "int",
    ("float", "+", "float"): "float",
    ("float", "-", "float"): "float",
    ("float", "*", "float"): "float",
    ("float", "/", "float"): "float",
    ("str",   "+", "str"):   "str",
    ("int",   "+", "float"): "float",
    ("float", "+", "int"):   "float",
    ("int",   "-", "float"): "float",
    ("float", "-", "int"):   "float",
    ("int",   "*", "float"): "float",
    ("float", "*", "int"):   "float",
}

COMPARE_OPS = {"==", "!=", "<", ">", "<=", ">="}


class SemanticAnalyzer:
    def __init__(self):
        self._scopes   = [{}]
        self._errors   = []
        self._in_func  = False

    def analyze(self, node):
        self._visit(node)
        return self._errors

    def _scope(self):
        return self._scopes[-1]

    def _push(self):
        self._scopes.append({})

    def _pop(self):
        self._scopes.pop()

    def _declare(self, name, type):
        self._scope()[name] = type

    def _lookup(self, name):
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def _error(self, msg, line):
        self._errors.append(SemanticError(msg, line))

    def _visit(self, node):
        method = "_visit_" + type(node).__name__
        visitor = getattr(self, method, None)
        if visitor:
            return visitor(node)
        return "any"

    def _visit_Program(self, node):
        for stmt in node.body:
            self._visit(stmt)

    def _visit_Assign(self, node):
        t = self._visit(node.value)
        if isinstance(node.target, Identifier):
            self._declare(node.target.name, t)

    def _visit_BinOp(self, node):
        left  = self._visit(node.left)
        right = self._visit(node.right)

        if node.op in COMPARE_OPS or node.op in ("and", "or"):
            return "bool"

        if "any" in (left, right):
            return "any"

        result = TYPE_OPS.get((left, node.op, right))
        if result is None:
            line = getattr(node.left, "line", 0)
            self._error(f"type mismatch: {left} {node.op} {right}", line)
            return "any"
        return result

    def _visit_UnaryOp(self, node):
        t = self._visit(node.operand)
        if node.op == "not":
            return "bool"
        return t

    def _visit_Identifier(self, node):
        if node.name in BUILTINS:
            return "any"
        t = self._lookup(node.name)
        if t is None:
            self._error(f"'{node.name}' used before definition", node.line)
            return "any"
        return t

    def _visit_Literal(self, node):
        return node.kind

    def _visit_FuncDef(self, node):
        self._declare(node.name, "func")
        self._push()
        for param in node.params:
            self._declare(param, "any")
        outer = self._in_func
        self._in_func = True
        for stmt in node.body:
            self._visit(stmt)
        self._in_func = outer
        self._pop()

    def _visit_FuncCall(self, node):
        if node.name not in BUILTINS:
            t = self._lookup(node.name)
            if t is None:
                self._error(f"'{node.name}' called before definition", node.line)
        for arg in node.args:
            self._visit(arg)
        return "any"

    def _visit_Return(self, node):
        if not self._in_func:
            self._error("return outside function", node.line)
        return self._visit(node.value)

    def _visit_If(self, node):
        self._visit(node.condition)
        self._push()
        for stmt in node.body:
            self._visit(stmt)
        self._pop()
        for cond, body in node.elifs:
            self._visit(cond)
            self._push()
            for stmt in body:
                self._visit(stmt)
            self._pop()
        if node.else_body:
            self._push()
            for stmt in node.else_body:
                self._visit(stmt)
            self._pop()

    def _visit_While(self, node):
        self._visit(node.condition)
        self._push()
        for stmt in node.body:
            self._visit(stmt)
        self._pop()

    def _visit_For(self, node):
        self._visit(node.iterable)
        self._push()
        self._declare(node.target.name, "any")
        for stmt in node.body:
            self._visit(stmt)
        self._pop()

    def _visit_Pass(self, node):
        pass
