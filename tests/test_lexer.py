import pytest

from src.ast_nodes import AssignmentNode, BinaryOpNode, IfNode, PrintNode, ProgramNode, WhileNode
from src.lexer import Lexer
from src.parser import Parser


def _parse(code: str):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def test_simple_assignment():
    ast = _parse("x = 5;")
    assert isinstance(ast, ProgramNode)
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], AssignmentNode)


def test_operator_precedence():
    ast = _parse("x = 2 + 3 * 4;")
    assign = ast.statements[0]
    assert isinstance(assign, AssignmentNode)
    assert isinstance(assign.value, BinaryOpNode)
    assert assign.value.operator == "+"
    assert isinstance(assign.value.right, BinaryOpNode)
    assert assign.value.right.operator == "*"


def test_if_else_and_while_blocks():
    code = """
    x = 0;
    if (x == 0) {
        print(x);
    } else {
        x = x + 1;
    }
    while (x < 3) {
        x = x + 1;
    }
    """
    ast = _parse(code)

    assert isinstance(ast.statements[1], IfNode)
    assert isinstance(ast.statements[2], WhileNode)


def test_missing_semicolon_raises_syntax_error():
    with pytest.raises(SyntaxError):
        _parse("x = 5")


def test_print_statement():
    ast = _parse("print(\"hello\");")
    assert isinstance(ast.statements[0], PrintNode)