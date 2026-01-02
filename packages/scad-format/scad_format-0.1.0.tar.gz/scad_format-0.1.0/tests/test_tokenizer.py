"""Tests for the tokenizer."""

import pytest
from scad_format.tokenizer import tokenize, TokenType


class TestTokenizer:
    """Test the OpenSCAD tokenizer."""
    
    def test_empty_input(self):
        """Empty input should produce just EOF."""
        tokens = tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF
    
    def test_simple_number(self):
        """Parse simple numbers."""
        tokens = tokenize("42")
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
    
    def test_float_number(self):
        """Parse floating point numbers."""
        tokens = tokenize("3.14159")
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "3.14159"
    
    def test_scientific_notation(self):
        """Parse scientific notation."""
        tokens = tokenize("1.5e-10")
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "1.5e-10"
    
    def test_string(self):
        """Parse string literals."""
        tokens = tokenize('"hello world"')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == '"hello world"'
    
    def test_string_with_escape(self):
        """Parse strings with escape sequences."""
        tokens = tokenize(r'"hello \"world\""')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == r'"hello \"world\""'
    
    def test_identifier(self):
        """Parse identifiers."""
        tokens = tokenize("my_variable")
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "my_variable"
    
    def test_special_variable(self):
        """Parse special variables starting with $."""
        tokens = tokenize("$fn")
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "$fn"
    
    def test_keyword(self):
        """Parse keywords."""
        tokens = tokenize("module")
        assert tokens[0].type == TokenType.KEYWORD
        assert tokens[0].value == "module"
    
    def test_builtin_module(self):
        """Parse builtin module names."""
        tokens = tokenize("cube")
        assert tokens[0].type == TokenType.BUILTIN_MODULE
        assert tokens[0].value == "cube"
    
    def test_builtin_function(self):
        """Parse builtin function names."""
        tokens = tokenize("sin")
        assert tokens[0].type == TokenType.BUILTIN_FUNCTION
        assert tokens[0].value == "sin"
    
    def test_boolean(self):
        """Parse boolean literals."""
        tokens = tokenize("true false")
        assert tokens[0].type == TokenType.BOOLEAN
        assert tokens[0].value == "true"
        # Skip whitespace
        assert tokens[2].type == TokenType.BOOLEAN
        assert tokens[2].value == "false"
    
    def test_undef(self):
        """Parse undef literal."""
        tokens = tokenize("undef")
        assert tokens[0].type == TokenType.UNDEF
        assert tokens[0].value == "undef"
    
    def test_operators(self):
        """Parse operators."""
        tokens = tokenize("+ - * / % < > <= >= == != && ||")
        operators = [t for t in tokens if t.type == TokenType.OPERATOR]
        assert len(operators) == 13  # 13 operators in the string
    
    def test_assignment(self):
        """Parse assignment operator."""
        tokens = tokenize("x = 5")
        assert tokens[2].type == TokenType.ASSIGNMENT
        assert tokens[2].value == "="
    
    def test_delimiters(self):
        """Parse delimiters."""
        tokens = tokenize("( ) [ ] { } ; , :")
        types = [t.type for t in tokens if t.type != TokenType.WHITESPACE and t.type != TokenType.EOF]
        expected = [
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.LBRACKET, TokenType.RBRACKET,
            TokenType.LBRACE, TokenType.RBRACE,
            TokenType.SEMICOLON, TokenType.COMMA, TokenType.COLON
        ]
        assert types == expected
    
    def test_line_comment(self):
        """Parse line comments."""
        tokens = tokenize("x = 5; // this is a comment\ny = 6;")
        comments = [t for t in tokens if t.type == TokenType.COMMENT_LINE]
        assert len(comments) == 1
        assert "// this is a comment" in comments[0].value
    
    def test_block_comment(self):
        """Parse block comments."""
        tokens = tokenize("x = 5; /* block\ncomment */ y = 6;")
        comments = [t for t in tokens if t.type == TokenType.COMMENT_BLOCK]
        assert len(comments) == 1
        assert "/* block\ncomment */" in comments[0].value
    
    def test_simple_module(self):
        """Parse a simple module definition."""
        code = "module foo() { cube(1); }"
        tokens = tokenize(code)
        
        # Find key tokens
        token_values = [(t.type, t.value) for t in tokens 
                       if t.type not in (TokenType.WHITESPACE, TokenType.EOF)]
        
        assert (TokenType.KEYWORD, "module") in token_values
        assert (TokenType.IDENTIFIER, "foo") in token_values
        assert (TokenType.LPAREN, "(") in token_values
        assert (TokenType.RPAREN, ")") in token_values
        assert (TokenType.LBRACE, "{") in token_values
        assert (TokenType.BUILTIN_MODULE, "cube") in token_values
        assert (TokenType.RBRACE, "}") in token_values
    
    def test_complex_expression(self):
        """Parse a complex expression."""
        code = "translate([x + 1, y * 2, z / 3]) rotate([0, 0, 45]) cube([1, 2, 3]);"
        tokens = tokenize(code)
        
        # Should parse without errors
        assert tokens[-1].type == TokenType.EOF
        
        # Check key elements
        builtin_modules = [t.value for t in tokens if t.type == TokenType.BUILTIN_MODULE]
        assert "translate" in builtin_modules
        assert "rotate" in builtin_modules
        assert "cube" in builtin_modules
    
    def test_for_loop(self):
        """Parse a for loop."""
        code = "for (i = [0:10]) { echo(i); }"
        tokens = tokenize(code)
        
        token_values = [(t.type, t.value) for t in tokens 
                       if t.type not in (TokenType.WHITESPACE, TokenType.EOF)]
        
        assert (TokenType.KEYWORD, "for") in token_values
        assert (TokenType.IDENTIFIER, "i") in token_values
        assert (TokenType.KEYWORD, "echo") in token_values
    
    def test_ternary_operator(self):
        """Parse ternary operator."""
        code = "x = a > 0 ? a : -a;"
        tokens = tokenize(code)
        
        assert any(t.type == TokenType.QUESTION for t in tokens)
        assert any(t.type == TokenType.COLON for t in tokens)
    
    def test_line_numbers(self):
        """Verify line numbers are tracked correctly."""
        code = "line1;\nline2;\nline3;"
        tokens = tokenize(code)
        
        # Find semicolons
        semicolons = [t for t in tokens if t.type == TokenType.SEMICOLON]
        assert len(semicolons) == 3
        assert semicolons[0].line == 1
        assert semicolons[1].line == 2
        assert semicolons[2].line == 3
    
    def test_modifier_hash(self):
        """Parse debug modifier #."""
        code = "#cube(1);"
        tokens = tokenize(code)
        
        assert tokens[0].type == TokenType.MODIFIER
        assert tokens[0].value == "#"
