"""
OpenSCAD tokenizer.

Tokenizes OpenSCAD source code into a stream of tokens for formatting.
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Iterator, Optional


class TokenType(Enum):
    """Types of tokens in OpenSCAD."""
    # Literals
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    UNDEF = auto()
    
    # Identifiers and keywords
    IDENTIFIER = auto()
    KEYWORD = auto()
    BUILTIN_MODULE = auto()
    BUILTIN_FUNCTION = auto()
    
    # Operators
    OPERATOR = auto()
    ASSIGNMENT = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMICOLON = auto()
    COMMA = auto()
    COLON = auto()
    QUESTION = auto()
    
    # Special
    COMMENT_LINE = auto()
    COMMENT_BLOCK = auto()
    WHITESPACE = auto()
    NEWLINE = auto()
    EOF = auto()
    
    # Modifiers
    MODIFIER = auto()  # *, !, #, %


@dataclass
class Token:
    """A single token from the source code."""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


# OpenSCAD keywords
KEYWORDS = {
    'module', 'function', 'if', 'else', 'for', 'let', 'each',
    'intersection_for', 'assert', 'echo', 'include', 'use'
}

# OpenSCAD builtin modules
BUILTIN_MODULES = {
    # 3D primitives
    'cube', 'sphere', 'cylinder', 'polyhedron',
    # 2D primitives
    'circle', 'square', 'polygon', 'text',
    # Transformations
    'translate', 'rotate', 'scale', 'mirror', 'multmatrix',
    'color', 'offset', 'hull', 'minkowski', 'resize',
    # Boolean operations
    'union', 'difference', 'intersection',
    # Extrusion
    'linear_extrude', 'rotate_extrude',
    # Import/render
    'import', 'surface', 'render', 'projection',
    # Children
    'children',
}

# OpenSCAD builtin functions
BUILTIN_FUNCTIONS = {
    # Math
    'abs', 'sign', 'sin', 'cos', 'tan', 'acos', 'asin', 'atan', 'atan2',
    'floor', 'round', 'ceil', 'ln', 'log', 'pow', 'sqrt', 'exp',
    'rands', 'min', 'max', 'norm', 'cross',
    # List
    'concat', 'lookup', 'len', 'search', 'chr', 'ord', 'str',
    # Type
    'is_undef', 'is_bool', 'is_num', 'is_string', 'is_list', 'is_function',
    # Other
    'version', 'version_num', 'parent_module',
}

# Operators (multi-char first for matching priority)
OPERATORS = [
    '<=', '>=', '==', '!=', '&&', '||',
    '<<', '>>', '++',
    '<', '>', '+', '-', '*', '/', '%', '^', '!',
]


class Tokenizer:
    """Tokenizes OpenSCAD source code."""
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return list of tokens."""
        while not self._at_end():
            self._scan_token()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
    
    def _at_end(self) -> bool:
        return self.pos >= len(self.source)
    
    def _peek(self, offset: int = 0) -> str:
        pos = self.pos + offset
        if pos >= len(self.source):
            return '\0'
        return self.source[pos]
    
    def _advance(self) -> str:
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char
    
    def _add_token(self, token_type: TokenType, value: str, line: int, column: int):
        self.tokens.append(Token(token_type, value, line, column))
    
    def _scan_token(self):
        start_line = self.line
        start_column = self.column
        start_pos = self.pos
        
        char = self._advance()
        
        # Newlines
        if char == '\n':
            self._add_token(TokenType.NEWLINE, '\n', start_line, start_column)
            return
        
        if char == '\r':
            if self._peek() == '\n':
                self._advance()
                self._add_token(TokenType.NEWLINE, '\r\n', start_line, start_column)
            else:
                self._add_token(TokenType.NEWLINE, '\r', start_line, start_column)
            return
        
        # Whitespace (not newlines)
        if char in ' \t':
            while self._peek() in ' \t':
                self._advance()
            value = self.source[start_pos:self.pos]
            self._add_token(TokenType.WHITESPACE, value, start_line, start_column)
            return
        
        # Line comment
        if char == '/' and self._peek() == '/':
            self._advance()  # consume second /
            while not self._at_end() and self._peek() not in '\r\n':
                self._advance()
            value = self.source[start_pos:self.pos]
            self._add_token(TokenType.COMMENT_LINE, value, start_line, start_column)
            return
        
        # Block comment
        if char == '/' and self._peek() == '*':
            self._advance()  # consume *
            while not self._at_end():
                if self._peek() == '*' and self._peek(1) == '/':
                    self._advance()  # *
                    self._advance()  # /
                    break
                self._advance()
            value = self.source[start_pos:self.pos]
            self._add_token(TokenType.COMMENT_BLOCK, value, start_line, start_column)
            return
        
        # String
        if char == '"':
            while not self._at_end() and self._peek() != '"':
                if self._peek() == '\\':
                    self._advance()  # skip escape char
                    if not self._at_end():
                        self._advance()  # skip escaped char
                else:
                    self._advance()
            if not self._at_end():
                self._advance()  # closing quote
            value = self.source[start_pos:self.pos]
            self._add_token(TokenType.STRING, value, start_line, start_column)
            return
        
        # Single-char delimiters
        if char == '(':
            self._add_token(TokenType.LPAREN, char, start_line, start_column)
            return
        if char == ')':
            self._add_token(TokenType.RPAREN, char, start_line, start_column)
            return
        if char == '[':
            self._add_token(TokenType.LBRACKET, char, start_line, start_column)
            return
        if char == ']':
            self._add_token(TokenType.RBRACKET, char, start_line, start_column)
            return
        if char == '{':
            self._add_token(TokenType.LBRACE, char, start_line, start_column)
            return
        if char == '}':
            self._add_token(TokenType.RBRACE, char, start_line, start_column)
            return
        if char == ';':
            self._add_token(TokenType.SEMICOLON, char, start_line, start_column)
            return
        if char == ',':
            self._add_token(TokenType.COMMA, char, start_line, start_column)
            return
        if char == ':':
            self._add_token(TokenType.COLON, char, start_line, start_column)
            return
        if char == '?':
            self._add_token(TokenType.QUESTION, char, start_line, start_column)
            return
        
        # Modifiers (*, !, #, % at start of statement - but we'll handle context later)
        # For now, * and % are also operators, handle specially
        
        # Assignment
        if char == '=':
            if self._peek() == '=':
                self._advance()
                self._add_token(TokenType.OPERATOR, '==', start_line, start_column)
            else:
                self._add_token(TokenType.ASSIGNMENT, '=', start_line, start_column)
            return
        
        # Operators (check multi-char first)
        self.pos = start_pos  # reset to check full operator
        self.column = start_column
        for op in OPERATORS:
            if self.source[self.pos:self.pos + len(op)] == op:
                for _ in range(len(op)):
                    self._advance()
                self._add_token(TokenType.OPERATOR, op, start_line, start_column)
                return
        
        # Re-advance the char we peeked
        self._advance()
        
        # Number
        if char.isdigit() or (char == '.' and self._peek().isdigit()):
            while self._peek().isdigit():
                self._advance()
            # Decimal part
            if self._peek() == '.' and self._peek(1).isdigit():
                self._advance()  # .
                while self._peek().isdigit():
                    self._advance()
            # Exponent
            if self._peek() in 'eE':
                self._advance()
                if self._peek() in '+-':
                    self._advance()
                while self._peek().isdigit():
                    self._advance()
            value = self.source[start_pos:self.pos]
            self._add_token(TokenType.NUMBER, value, start_line, start_column)
            return
        
        # Identifier or keyword
        if char.isalpha() or char == '_' or char == '$':
            while self._peek().isalnum() or self._peek() == '_':
                self._advance()
            value = self.source[start_pos:self.pos]
            
            # Classify
            if value in ('true', 'false'):
                self._add_token(TokenType.BOOLEAN, value, start_line, start_column)
            elif value == 'undef':
                self._add_token(TokenType.UNDEF, value, start_line, start_column)
            elif value in KEYWORDS:
                self._add_token(TokenType.KEYWORD, value, start_line, start_column)
            elif value in BUILTIN_MODULES:
                self._add_token(TokenType.BUILTIN_MODULE, value, start_line, start_column)
            elif value in BUILTIN_FUNCTIONS:
                self._add_token(TokenType.BUILTIN_FUNCTION, value, start_line, start_column)
            else:
                self._add_token(TokenType.IDENTIFIER, value, start_line, start_column)
            return
        
        # Check for modifiers: #, %
        if char == '#':
            self._add_token(TokenType.MODIFIER, char, start_line, start_column)
            return
        
        # Unknown character - treat as operator for now
        self._add_token(TokenType.OPERATOR, char, start_line, start_column)


def tokenize(source: str) -> List[Token]:
    """Tokenize OpenSCAD source code."""
    return Tokenizer(source).tokenize()
