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
from src.lexer import Lexer
from src.tokens import TokenType


class Parser:
    """
    Recursive-descent parser for a C-style mini language.

    Grammar (EBNF-like):
      program        -> statement* EOF
      statement      -> assignment
                     | print_stmt
                     | if_stmt
                     | while_stmt

      assignment     -> IDENTIFIER '=' expression ';'
      print_stmt     -> 'print' '(' expression ')' ';'
      if_stmt        -> 'if' '(' expression ')' block ('else' block)?
      while_stmt     -> 'while' '(' expression ')' block
      block          -> '{' statement* '}'

      expression     -> equality
      equality       -> comparison ( ( '==' | '!=' ) comparison )*
      comparison     -> term ( ( '>' | '>=' | '<' | '<=' ) term )*
      term           -> factor ( ( '+' | '-' ) factor )*
      factor         -> unary ( ( '*' | '/' ) unary )*
      unary          -> '-' unary | primary
      primary        -> NUMBER | STRING | IDENTIFIER | '(' expression ')'
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[0]

    def parse(self):
        """Main entry point - parse complete token stream into a ProgramNode."""
        program = self.parse_program()
        self.expect(TokenType.EOF, "Expected end of input")
        return program

    def advance(self):
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
        return self.current_token

    def expect(self, token_type, message=None):
        if self.current_token.type != token_type:
            self.error(message or f"Expected {token_type.name}, got {self.current_token.type.name}")
        token = self.current_token
        self.advance()
        return token

    def match(self, *token_types):
        if self.current_token.type in token_types:
            matched = self.current_token
            self.advance()
            return matched
        return None

    def error(self, message):
        token = self.current_token
        raise SyntaxError(f"{message} at line {token.line}, column {token.column}")

    def parse_program(self):
        statements = []
        while self.current_token.type != TokenType.EOF:
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    def parse_statement(self):
        if self.current_token.type == TokenType.IF:
            return self.parse_if_statement()
        if self.current_token.type == TokenType.WHILE:
            return self.parse_while_statement()
        if self.current_token.type == TokenType.PRINT:
            return self.parse_print_statement()
        if self.current_token.type == TokenType.IDENTIFIER:
            return self.parse_assignment()

        self.error(f"Unexpected token {self.current_token.type.name}")

    def parse_block(self):
        self.expect(TokenType.LBRACE, "Expected '{' to start block")
        statements = []
        while self.current_token.type not in (TokenType.RBRACE, TokenType.EOF):
            statements.append(self.parse_statement())
        self.expect(TokenType.RBRACE, "Expected '}' to close block")
        return statements

    def parse_assignment(self):
        name_token = self.expect(TokenType.IDENTIFIER, "Expected variable name")
        self.expect(TokenType.ASSIGN, "Expected '=' in assignment")
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Expected ';' after assignment")
        return AssignmentNode(VariableNode(name_token.value), value)

    def parse_print_statement(self):
        self.expect(TokenType.PRINT, "Expected 'print'")
        self.expect(TokenType.LPAREN, "Expected '(' after print")
        expression = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after print expression")
        self.expect(TokenType.SEMICOLON, "Expected ';' after print statement")
        return PrintNode(expression)

    def parse_if_statement(self):
        self.expect(TokenType.IF, "Expected 'if'")
        self.expect(TokenType.LPAREN, "Expected '(' after if")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after if condition")
        then_block = self.parse_block()

        else_block = None
        if self.match(TokenType.ELSE):
            else_block = self.parse_block()

        return IfNode(condition, then_block, else_block)

    def parse_while_statement(self):
        self.expect(TokenType.WHILE, "Expected 'while'")
        self.expect(TokenType.LPAREN, "Expected '(' after while")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after while condition")
        body = self.parse_block()
        return WhileNode(condition, body)

    def parse_expression(self):
        return self.parse_equality()

    def parse_equality(self):
        node = self.parse_comparison()

        while self.current_token.type in (TokenType.EQUAL, TokenType.NOT_EQUAL):
            operator_token = self.current_token
            self.advance()
            right = self.parse_comparison()
            node = BinaryOpNode(node, operator_token.value, right)

        return node

    def parse_comparison(self):
        node = self.parse_term()

        while self.current_token.type in (
            TokenType.GREATER,
            TokenType.GREATER_EQ,
            TokenType.LESS,
            TokenType.LESS_EQ,
        ):
            operator_token = self.current_token
            self.advance()
            right = self.parse_term()
            node = BinaryOpNode(node, operator_token.value, right)

        return node

    def parse_term(self):
        node = self.parse_factor()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            operator_token = self.current_token
            self.advance()
            right = self.parse_factor()
            node = BinaryOpNode(node, operator_token.value, right)

        return node

    def parse_factor(self):
        node = self.parse_unary()

        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            operator_token = self.current_token
            self.advance()
            right = self.parse_unary()
            node = BinaryOpNode(node, operator_token.value, right)

        return node

    def parse_unary(self):
        if self.current_token.type == TokenType.MINUS:
            operator_token = self.current_token
            self.advance()
            operand = self.parse_unary()
            return UnaryOpNode(operator_token.value, operand)

        return self.parse_primary()

    def parse_primary(self):
        token = self.current_token

        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(token.value)

        if token.type == TokenType.STRING:
            self.advance()
            return StringNode(token.value)

        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return VariableNode(token.value)

        if token.type == TokenType.LPAREN:
            self.advance()
            expression = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after expression")
            return expression

        self.error(f"Expected expression, got {token.type.name}")


def parse_source(source_code: str) -> ProgramNode:
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    if lexer.get_errors():
        first_error = lexer.get_errors()[0]
        raise SyntaxError(
            f"Cannot parse due to lexical error: {first_error.message} "
            f"at line {first_error.line}, column {first_error.column}"
        )

    parser = Parser(tokens)
    return parser.parse()


if __name__ == "__main__":
    import sys
    from pprint import pprint

    if len(sys.argv) < 2:
        print("Usage: python -m src.parser <source_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            source = file.read()
        ast = parse_source(source)
        print("Syntax analysis successful. AST:")
        pprint(ast)
    except FileNotFoundError:
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    except SyntaxError as error:
        print(f"Syntax error: {error}")
        sys.exit(1)