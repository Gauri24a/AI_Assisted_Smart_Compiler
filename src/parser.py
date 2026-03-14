class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[0]
    
    def parse(self):
        """Main entry point - parses entire program"""
        return self.parse_program()
    
    def parse_program(self):
        """Parse complete program"""
        statements = []
        while self.current_token.type != TokenType.EOF:
            stmt = self.parse_statement()
            statements.append(stmt)
        return ProgramNode(statements)
    
    def parse_statement(self):
        if self.current_token.type == TokenType.IF:
            return self.parse_if_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self.parse_while_statement()
        elif self.current_token.type == TokenType.PRINT:
            return self.parse_print_statement()
        elif self.current_token.type == TokenType.IDENTIFIER:
            return self.parse_assignment()
        else:
            raise SyntaxError(f"Unexpected token: {self.current_token}")
    
    def parse_expression(self):
        """Parse an expression with operator precedence"""
        # Implements: expression → term ((+|-) term)*
        # This handles: 5 + 3 - 2
        pass
    
    # ... more parsing methods