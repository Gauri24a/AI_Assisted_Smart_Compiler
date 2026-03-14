from typing import List, Optional
from src.tokens import Token, TokenType, lookup_identifier


class LexerError:
    def __init__(self, message: str, line: int, column: int, char: str):
        self.message = message
        self.line = line
        self.column = column
        self.char = char
    
    def __repr__(self):
        return f"LexerError({self.message!r}, {self.line}:{self.column}, char={self.char!r})"


class Lexer:
    """
    Tokenizes source code into a list of tokens
    """
    
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0       # Current position in source
        self.line = 1           # Current line number
        self.column = 1         # Current column number
        self.tokens: List[Token] = []
        self.errors: List[LexerError] = []
        
    def current_char(self) -> Optional[str]:
        if self.position >= len(self.source):
            return None
        return self.source[self.position]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        peek_pos = self.position + offset
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]
    
    def advance(self) -> Optional[str]:
        if self.position >= len(self.source):
            return None
        
        char = self.source[self.position]
        self.position += 1
        
        # Track line and column numbers
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
            
        return char
    
    def skip_whitespace(self):
        while self.current_char() and self.current_char().isspace():
            self.advance()
    
    def skip_single_line_comment(self):
        if self.current_char() == '/' and self.peek_char() == '/':
            # Skip until end of line
            while self.current_char() and self.current_char() != '\n':
                self.advance()
    
    def skip_multi_line_comment(self):
        if self.current_char() == '/' and self.peek_char() == '*':
            # Skip the /*
            self.advance()
            self.advance()
            
            # Skip until we find */
            while self.current_char():
                if self.current_char() == '*' and self.peek_char() == '/':
                    self.advance()  # Skip *
                    self.advance()  # Skip /
                    break
                self.advance()
    
    def read_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        num_str = ''
        
        # Read digits before decimal point
        while self.current_char() and self.current_char().isdigit():
            num_str += self.current_char()
            self.advance()
        
        # Check for decimal point
        if self.current_char() == '.' and self.peek_char() and self.peek_char().isdigit():
            num_str += self.current_char()  # Add '.'
            self.advance()
            
            # Read digits after decimal point
            while self.current_char() and self.current_char().isdigit():
                num_str += self.current_char()
                self.advance()
        
        # Convert to appropriate type
        value = float(num_str) if '.' in num_str else int(num_str)
        
        return Token(TokenType.NUMBER, value, start_line, start_col)
    
    def read_identifier(self) -> Token:
        start_line = self.line
        start_col = self.column
        identifier = ''
        
        # First character must be letter or underscore
        # Following characters can be letters, digits, or underscores
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            identifier += self.current_char()
            self.advance()
        
        # Check if it's a keyword or regular identifier
        token_type = lookup_identifier(identifier)
        
        return Token(token_type, identifier, start_line, start_col)
    
    def read_string(self) -> Token:
        start_line = self.line
        start_col = self.column
        
        # Skip opening quote
        self.advance()
        
        string_value = ''
        
        # Read until closing quote
        while self.current_char() and self.current_char() != '"':
            # Handle escape sequences
            if self.current_char() == '\\':
                self.advance()
                if self.current_char() == 'n':
                    string_value += '\n'
                elif self.current_char() == 't':
                    string_value += '\t'
                elif self.current_char() == '"':
                    string_value += '"'
                elif self.current_char() == '\\':
                    string_value += '\\'
                else:
                    string_value += self.current_char()
                self.advance()
            else:
                string_value += self.current_char()
                self.advance()
    
        # Skip closing quote
        if self.current_char() == '"':
            self.advance()
        else:
            error = LexerError(
                "Unterminated string literal",
                start_line,
                start_col,
                '"'
            )
            self.errors.append(error)
        
        return Token(TokenType.STRING, string_value, start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        """Returns:
            List of Token objects
        """
        while self.current_char() is not None:
            # Skip whitespace
            if self.current_char().isspace():
                self.skip_whitespace()
                continue
            
            # Skip single-line comments
            if self.current_char() == '/' and self.peek_char() == '/':
                self.skip_single_line_comment()
                continue
            
            # Skip multi-line comments
            if self.current_char() == '/' and self.peek_char() == '*':
                self.skip_multi_line_comment()
                continue
            
            # Strings
            if self.current_char() == '"':
                self.tokens.append(self.read_string())
                continue
            
            # Numbers
            if self.current_char().isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Identifiers and keywords
            if self.current_char().isalpha() or self.current_char() == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Single and double character operators
            char = self.current_char()
            line = self.line
            col = self.column
            
            # Two-character operators (==, !=, >=, <=)
            if char == '=' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.EQUAL, '==', line, col))
            elif char == '!' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NOT_EQUAL, '!=', line, col))
            elif char == '>' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.GREATER_EQ, '>=', line, col))
            elif char == '<' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.LESS_EQ, '<=', line, col))
            
            # Single character tokens
            elif char == '+':
                self.tokens.append(Token(TokenType.PLUS, '+', line, col))
                self.advance()
            elif char == '-':
                self.tokens.append(Token(TokenType.MINUS, '-', line, col))
                self.advance()
            elif char == '*':
                self.tokens.append(Token(TokenType.MULTIPLY, '*', line, col))
                self.advance()
            elif char == '/':
                self.tokens.append(Token(TokenType.DIVIDE, '/', line, col))
                self.advance()
            elif char == '=':
                self.tokens.append(Token(TokenType.ASSIGN, '=', line, col))
                self.advance()
            elif char == '>':
                self.tokens.append(Token(TokenType.GREATER, '>', line, col))
                self.advance()
            elif char == '<':
                self.tokens.append(Token(TokenType.LESS, '<', line, col))
                self.advance()
            elif char == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', line, col))
                self.advance()
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', line, col))
                self.advance()
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', line, col))
                self.advance()
            elif char == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', line, col))
                self.advance()
            elif char == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', line, col))
                self.advance()
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', line, col))
                self.advance()
            else:
                # Unknown character - collect error but continue
                error = LexerError(
                    f"Unknown character",
                    line,
                    col,
                    char
                )
                self.errors.append(error)
                print(f"Warning: Unknown character '{char}' at {line}:{col}")
                self.advance()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        
        return self.tokens
    
    def get_errors(self) -> List[LexerError]:
        """Return list of lexical errors encountered"""
        return self.errors


# Main entry point for testing
if __name__ == '__main__':
    import sys
    
    # Check if file argument provided
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f:
                source_code = f.read()
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found!")
            sys.exit(1)
    else:
        # Default test code
        source_code = """
// Test Program for Compiler
x = 5;
y = x + 3;
z = y * 2;
name = "Alice";

if (z > 10) {
    result = 1;
    print(result);
} else {
    result = 0;
}

/* Multi-line comment
   This is ignored by the lexer
*/

counter = 0;
while (counter < 5) {
    counter = counter + 1;
    print("Hello");
}
"""
    
    print("=" * 70)
    print("LEXER - TOKENIZATION")
    print("=" * 70)
    print("\nSource Code:")
    print("-" * 70)
    print(source_code)
    print("-" * 70)
    
    # Create lexer and tokenize
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    print("\nTokens Generated:")
    print("-" * 70)
    
    # Print tokens in a nice format
    for i, token in enumerate(tokens, 1):
        if token.type != TokenType.EOF:
            print(f"{i:3}. {token}")
    
    # Print any errors
    if lexer.errors:
        print("\n" + "=" * 70)
        print("LEXICAL ERRORS FOUND:")
        print("=" * 70)
        for error in lexer.errors:
            print(f"  {error}")
    
    print("\n" + "=" * 70)
    print(f"Successfully tokenized {len(tokens)} tokens!")
    if lexer.errors:
        print(f"Error Found {len(lexer.errors)} lexical errors")
    print("=" * 70)




