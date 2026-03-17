from src.lexer import Lexer
from src.parser import Parser
from src.semantic_analyzer import SemanticAnalyzer


def _parse(code: str):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def test_symbol_table_tracks_assigned_variables():
    ast = _parse("x = 5; y = x + 2;")
    report = SemanticAnalyzer().analyze(ast)

    assert report["status"] == "ok"
    symbols = {row["name"]: row["type"] for row in report["symbol_table"]}
    assert symbols["x"] == "number"
    assert symbols["y"] == "number"


def test_use_before_assignment_reports_error():
    ast = _parse("print(x);")
    report = SemanticAnalyzer().analyze(ast)

    assert report["status"] == "error"
    assert any("undefined variable 'x'" in issue["message"] for issue in report["issues"])


def test_scope_management_limits_block_variables():
    code = """
    if (1) {
        temp = 10;
    }
    print(temp);
    """
    ast = _parse(code)
    report = SemanticAnalyzer().analyze(ast)

    assert report["status"] == "error"
    assert any("undefined variable 'temp'" in issue["message"] for issue in report["issues"])


def test_type_mismatch_is_reported():
    ast = _parse('x = 5; x = "hello";')
    report = SemanticAnalyzer().analyze(ast)

    assert report["status"] == "error"
    assert any("Type mismatch for 'x'" in issue["message"] for issue in report["issues"])
