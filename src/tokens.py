from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    
    # Literals
    NUMBER = auto()     
    IDENTIFIER = auto()  
    STRING = auto()      
    
    # Keywords
    IF = auto()         
    ELSE = auto()       
    WHILE = auto()      
    PRINT = auto()     
    
    # Operators
    PLUS= auto()      
    MINUS= auto()      
    MULTIPLY= auto()    
    DIVIDE= auto()      
    ASSIGN= auto()      
    
    # Comparison
    EQUAL = auto()      
    NOT_EQUAL = auto()  
    GREATER= auto()    
    LESS= auto()
    GREATER_EQ = auto()  
    LESS_EQ = auto()    
    
    # Delimiters
    SEMICOLON = auto()   
    LPAREN = auto()     
    RPAREN = auto()      
    LBRACE = auto()      
    RBRACE = auto()      
    COMMA = auto()       
    
    # Special
    EOF = auto()        
    

@dataclass
class Token:
    """
    Represents a single token from the source code
    
    Attributes:
        type: The type of token (from TokenType enum)
        value: The actual value (e.g., the number 42, or identifier name "x")
        line: Line number where token appears
        column: Column number where token starts
    """
    type: TokenType
    value: Any
    line: int
    column: int
    
    def __repr__(self):
        return f'Token({self.type.name}, {self.value!r}, {self.line}:{self.column})'


# Keywords mapping - 
KEYWORDS = {
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'print': TokenType.PRINT,
}


def lookup_identifier(name: str) -> TokenType:
    """
    Check if an identifier is actually a keyword
    
    Args:
        name: The identifier to check
        
    Returns:
        TokenType.KEYWORD if it's a keyword, TokenType.IDENTIFIER otherwise
    """
    return KEYWORDS.get(name, TokenType.IDENTIFIER)