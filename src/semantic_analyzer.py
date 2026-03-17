from dataclasses import dataclass
from typing import Dict, List, Optional

from src.ast_nodes import (
    AssignmentNode,
    BinaryOpNode,
    IfNode,
    NumberNode,
    PrintNode,
    ProgramNode,
    StringNode,
    UnaryOpNode,
    VariableNode,
    WhileNode,
)


@dataclass
class SymbolInfo:
    name: str
    symbol_type: str
    scope_level: int


@dataclass
class SemanticIssue:
    level: str
    message: str
    node_type: str


class Scope:
    def __init__(self, level: int, parent: Optional["Scope"] = None):
        self.level = level
        self.parent = parent
        self.symbols: Dict[str, SymbolInfo] = {}

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        scope = self
        while scope is not None:
            symbol = scope.symbols.get(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None


class SemanticAnalyzer:
    """
    Semantic analyzer with symbol table + lexical scope management.

    Notes:
    - Variables are implicitly declared on first assignment.
    - Each block (`if`, `else`, `while`) creates a child scope.
    - ML classification is used as a hint for statement dispatch when provided.
    """

    def __init__(self):
        self.issues: List[SemanticIssue] = []
        self.global_scope = Scope(level=0)
        self.current_scope = self.global_scope
        self.scope_history: List[Scope] = [self.global_scope]

    def analyze(self, program: ProgramNode, classification_hints: Optional[List[dict]] = None) -> dict:
        hints = classification_hints or []

        for idx, statement in enumerate(program.statements):
            hint = hints[idx] if idx < len(hints) else None
            self._analyze_statement(statement, hint)

        return {
            "status": "ok" if not self.issues else "error",
            "issues": [issue.__dict__ for issue in self.issues],
            "symbol_table": self._serialize_symbols(),
        }

    def _serialize_symbols(self) -> List[dict]:
        rows: List[dict] = []
        for scope in self.scope_history:
            for symbol in scope.symbols.values():
                rows.append(
                    {
                        "name": symbol.name,
                        "type": symbol.symbol_type,
                        "scope_level": symbol.scope_level,
                    }
                )
        return rows

    def _analyze_statement(self, node, hint: Optional[dict] = None):
        predicted = (hint or {}).get("predicted_type", "").lower()

        if isinstance(node, AssignmentNode) or "assignment" in predicted:
            self._analyze_assignment(node)
            return
        if isinstance(node, IfNode) or predicted in {"if", "if_statement", "conditional"}:
            self._analyze_if(node)
            return
        if isinstance(node, WhileNode) or "while" in predicted:
            self._analyze_while(node)
            return
        if isinstance(node, PrintNode) or "print" in predicted:
            self._analyze_print(node)
            return

        self._error(f"Unsupported statement type for semantic analysis: {node.__class__.__name__}", node)

    def _analyze_assignment(self, node: AssignmentNode):
        value_type = self._infer_type(node.value)
        if value_type == "unknown":
            return

        existing = self.current_scope.lookup(node.target.name)
        if existing is None:
            self.current_scope.symbols[node.target.name] = SymbolInfo(
                name=node.target.name,
                symbol_type=value_type,
                scope_level=self.current_scope.level,
            )
            return

        if existing.symbol_type != value_type:
            self._error(
                f"Type mismatch for '{node.target.name}': expected {existing.symbol_type}, got {value_type}",
                node,
            )

    def _analyze_if(self, node: IfNode):
        cond_type = self._infer_type(node.condition)
        if cond_type not in {"bool", "number", "unknown"}:
            self._error("If condition must be numeric or boolean", node)

        self._enter_scope()
        for statement in node.then_block:
            self._analyze_statement(statement)
        self._leave_scope()

        if node.else_block is not None:
            self._enter_scope()
            for statement in node.else_block:
                self._analyze_statement(statement)
            self._leave_scope()

    def _analyze_while(self, node: WhileNode):
        cond_type = self._infer_type(node.condition)
        if cond_type not in {"bool", "number", "unknown"}:
            self._error("While condition must be numeric or boolean", node)

        self._enter_scope()
        for statement in node.body:
            self._analyze_statement(statement)
        self._leave_scope()

    def _analyze_print(self, node: PrintNode):
        self._infer_type(node.expression)

    def _infer_type(self, node) -> str:
        if isinstance(node, NumberNode):
            return "number"

        if isinstance(node, StringNode):
            return "string"

        if isinstance(node, VariableNode):
            symbol = self.current_scope.lookup(node.name)
            if symbol is None:
                self._error(f"Use of undefined variable '{node.name}'", node)
                return "unknown"
            return symbol.symbol_type

        if isinstance(node, UnaryOpNode):
            operand_type = self._infer_type(node.operand)
            if node.operator == "-" and operand_type not in {"number", "unknown"}:
                self._error("Unary '-' requires numeric operand", node)
                return "unknown"
            return operand_type

        if isinstance(node, BinaryOpNode):
            left_type = self._infer_type(node.left)
            right_type = self._infer_type(node.right)
            op = node.operator

            if op in {"+", "-", "*", "/"}:
                if left_type != "number" or right_type != "number":
                    if left_type != "unknown" and right_type != "unknown":
                        self._error(
                            f"Operator '{op}' requires numeric operands, got {left_type} and {right_type}",
                            node,
                        )
                    return "unknown"
                return "number"

            if op in {">", ">=", "<", "<="}:
                if left_type != "number" or right_type != "number":
                    if left_type != "unknown" and right_type != "unknown":
                        self._error(
                            f"Comparison '{op}' requires numeric operands, got {left_type} and {right_type}",
                            node,
                        )
                    return "unknown"
                return "bool"

            if op in {"==", "!="}:
                if left_type != right_type and "unknown" not in {left_type, right_type}:
                    self._error(
                        f"Equality '{op}' compares incompatible types: {left_type} and {right_type}",
                        node,
                    )
                    return "unknown"
                return "bool"

            self._error(f"Unsupported operator '{op}'", node)
            return "unknown"

        self._error(f"Unsupported expression node type: {node.__class__.__name__}", node)
        return "unknown"

    def _enter_scope(self):
        child = Scope(level=self.current_scope.level + 1, parent=self.current_scope)
        self.current_scope = child
        self.scope_history.append(child)

    def _leave_scope(self):
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent

    def _error(self, message: str, node):
        self.issues.append(
            SemanticIssue(level="error", message=message, node_type=node.__class__.__name__)
        )
