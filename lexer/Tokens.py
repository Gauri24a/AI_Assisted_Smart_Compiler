KEYWORDS = {
    "if", "else", "elif", "while", "for", "in",
    "def", "return", "class", "import", "from",
    "pass", "break", "continue", "and", "or", "not",
    "True", "False", "None", "try", "except", "raise",
    "with", "as", "lambda", "yield", "global", "is",
}

OPERATORS = sorted([
    "//", "**", "==", "!=", "<=", ">=",
    "+=", "-=", "*=", "/=",
    "+", "-", "*", "/", "%", "=", "<", ">",
], key=len, reverse=True)

DELIMITERS = {"(", ")", "[", "]", ",", ":", "."}

COMPOUND = {"if", "elif", "else", "while", "for", "def", "class", "try", "except", "with"}
CHAIN    = {"elif", "else", "except"}