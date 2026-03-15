from dataclasses import dataclass
from typing import List, Optional, Union


class ASTNode:
    """Base class for all AST nodes."""


@dataclass
class NumberNode(ASTNode):
    """Represents a number literal, e.g. 42 or 3.14."""

    value: Union[int, float]


@dataclass
class StringNode(ASTNode):
    """Represents a string literal."""

    value: str


@dataclass
class VariableNode(ASTNode):
    """Represents a variable reference, e.g. x or counter."""

    name: str


@dataclass
class UnaryOpNode(ASTNode):
    """Represents unary operations, e.g. -x."""

    operator: str
    operand: ASTNode


@dataclass
class BinaryOpNode(ASTNode):
    """Represents binary operations, e.g. x + y or a >= b."""

    left: ASTNode
    operator: str
    right: ASTNode


@dataclass
class AssignmentNode(ASTNode):
    """Represents assignment, e.g. x = 5."""

    target: VariableNode
    value: ASTNode


@dataclass
class IfNode(ASTNode):
    """Represents an if/else statement."""

    condition: ASTNode
    then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]] = None


@dataclass
class WhileNode(ASTNode):
    """Represents a while loop."""

    condition: ASTNode
    body: List[ASTNode]


@dataclass
class PrintNode(ASTNode):
    """Represents print(expression)."""

    expression: ASTNode


@dataclass
class ProgramNode(ASTNode):
    """Root node containing all top-level statements."""

    statements: List[ASTNode]