class Node:
    def __repr__(self):
        fields = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"

class Program(Node):
    def __init__(self, body):
        self.body = body

class Assign(Node):
    def __init__(self, target, value, line):
        self.target = target
        self.value  = value
        self.line   = line

class BinOp(Node):
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op
        self.right = right

class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand

class Identifier(Node):
    def __init__(self, name, line):
        self.name = name
        self.line = line

class Literal(Node):
    def __init__(self, value, kind):
        self.value = value
        self.kind  = kind

class FuncDef(Node):
    def __init__(self, name, params, body, line):
        self.name   = name
        self.params = params
        self.body   = body
        self.line   = line

class FuncCall(Node):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line

class Return(Node):
    def __init__(self, value, line):
        self.value = value
        self.line  = line

class If(Node):
    def __init__(self, condition, body, elifs, else_body, line):
        self.condition = condition
        self.body      = body
        self.elifs     = elifs
        self.else_body = else_body
        self.line      = line

class While(Node):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body      = body
        self.line      = line

class For(Node):
    def __init__(self, target, iterable, body, line):
        self.target   = target
        self.iterable = iterable
        self.body     = body
        self.line     = line

class Pass(Node):
    def __init__(self, line):
        self.line = line
