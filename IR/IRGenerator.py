import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "AST"))

from Nodes import Assign, BinOp, UnaryOp, Identifier, Literal, FuncDef, FuncCall, Return, If, While, For
from IR import Instr


class IRGenerator:
    def __init__(self):
        self._instrs = []
        self._tmp    = 0
        self._label  = 0

    def generate(self, node):
        self._visit(node)
        return self._instrs

    def _new_tmp(self):
        name = f"t{self._tmp}"
        self._tmp += 1
        return name

    def _new_label(self):
        name = f"L{self._label}"
        self._label += 1
        return name

    def _emit(self, *args, **kwargs):
        self._instrs.append(Instr(*args, **kwargs))

    def _visit(self, node):
        method = "_visit_" + type(node).__name__
        return getattr(self, method)(node)

    def _visit_Program(self, node):
        for stmt in node.body:
            self._visit(stmt)

    def _visit_Assign(self, node):
        val = self._visit(node.value)
        self._emit("assign", dest=node.target.name, a=val)

    def _visit_BinOp(self, node):
        left  = self._visit(node.left)
        right = self._visit(node.right)
        tmp   = self._new_tmp()
        self._emit("binop", dest=tmp, a=left, b=f"{node.op} {right}")
        return tmp

    def _visit_UnaryOp(self, node):
        val = self._visit(node.operand)
        tmp = self._new_tmp()
        self._emit("binop", dest=tmp, a=node.op, b=val)
        return tmp

    def _visit_Identifier(self, node):
        return node.name

    def _visit_Literal(self, node):
        return repr(node.value)

    def _visit_FuncDef(self, node):
        self._emit("funcdef", a=node.name, b=node.params)
        for stmt in node.body:
            self._visit(stmt)
        self._emit("funcend", a=node.name)

    def _visit_FuncCall(self, node):
        args = [self._visit(arg) for arg in node.args]
        for arg in args:
            self._emit("param", a=arg)
        tmp = self._new_tmp()
        self._emit("call", dest=tmp, a=node.name, b=len(args))
        return tmp

    def _visit_Return(self, node):
        val = self._visit(node.value)
        self._emit("return", a=val)

    def _visit_If(self, node):
        end_label = self._new_label()

        cond = self._visit(node.condition)
        else_label = self._new_label()
        self._emit("jumpif", a=cond, b=f"not -> {else_label}")

        for stmt in node.body:
            self._visit(stmt)
        self._emit("jump", a=end_label)
        self._emit("label", a=else_label)

        for elif_cond, elif_body in node.elifs:
            cond = self._visit(elif_cond)
            skip = self._new_label()
            self._emit("jumpif", a=cond, b=f"not -> {skip}")
            for stmt in elif_body:
                self._visit(stmt)
            self._emit("jump", a=end_label)
            self._emit("label", a=skip)

        if node.else_body:
            for stmt in node.else_body:
                self._visit(stmt)

        self._emit("label", a=end_label)

    def _visit_While(self, node):
        start = self._new_label()
        end   = self._new_label()

        self._emit("label", a=start)
        cond = self._visit(node.condition)
        self._emit("jumpif", a=cond, b=f"not -> {end}")

        for stmt in node.body:
            self._visit(stmt)
        self._emit("jump", a=start)
        self._emit("label", a=end)

    def _visit_For(self, node):
        iterable = self._visit(node.iterable)
        idx      = self._new_tmp()
        length   = self._new_tmp()
        start    = self._new_label()
        end      = self._new_label()
        cond_tmp = self._new_tmp()

        self._emit("assign", dest=idx, a="0")
        self._emit("call",   dest=length, a="len", b=iterable)
        self._emit("label",  a=start)
        self._emit("binop",  dest=cond_tmp, a=idx, b=f"< {length}")
        self._emit("jumpif", a=cond_tmp, b=f"not -> {end}")

        self._emit("call", dest=node.target.name, a="iter_get", b=f"{iterable} {idx}")

        for stmt in node.body:
            self._visit(stmt)

        next_idx = self._new_tmp()
        self._emit("binop", dest=next_idx, a=idx, b="+ 1")
        self._emit("assign", dest=idx, a=next_idx)
        self._emit("jump",   a=start)
        self._emit("label",  a=end)

    def _visit_Pass(self, node):
        self._emit("assign", dest="_", a="None")