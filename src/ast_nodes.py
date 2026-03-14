class ASTNode:
    """Base class for all AST nodes"""
    pass

class NumberNode(ASTNode):
    """Represents a number: 42, 3.14"""
    def __init__(self, value):
        self.value = value

class VariableNode(ASTNode):
    """Represents a variable: x, count"""
    def __init__(self, name):
        self.name = name

class BinaryOpNode(ASTNode):
    """Represents binary operations: x + y"""
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class AssignmentNode(ASTNode):
    """Represents assignment: x = 5"""
    def __init__(self, target, value):
        self.target = target
        self.value = value

class IfNode(ASTNode):
    """Represents if statement"""
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class WhileNode(ASTNode):
    """Represents while loop"""
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class PrintNode(ASTNode):
    """Represents print statement"""
    def __init__(self, expression):
        self.expression = expression

class ProgramNode(ASTNode):
    """Root node containing all statements"""
    def __init__(self, statements):
        self.statements = statements