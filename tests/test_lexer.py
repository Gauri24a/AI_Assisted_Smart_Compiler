def test_simple_assignment():
    code = "x = 5;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert isinstance(ast, ProgramNode)
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], AssignmentNode)