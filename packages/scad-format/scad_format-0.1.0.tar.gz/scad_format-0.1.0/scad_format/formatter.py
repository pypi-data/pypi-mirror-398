"""
OpenSCAD code formatter.

Takes tokenized code and reformats it according to configuration.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from .tokenizer import Token, TokenType, tokenize
from .config import FormatConfig, BraceBreakingStyle, SeparateDefinitionStyle, load_config


@dataclass
class BreakPoint:
    """A potential line break point."""
    position: int  # Position in the line string
    depth: int     # Nesting depth (lower = higher scope, preferred)
    token_index: int  # Index of token after which to break
    align_column: int = 0  # Column to align continuation with (0 = use default)


class Formatter:
    """Formats OpenSCAD code based on configuration."""
    
    def __init__(self, config: FormatConfig, source: str = ""):
        self.config = config
        self.source = source
        self.line_ending = config.get_line_ending(source)
        self.indent_level = 0
        self.output: List[str] = []
        self.current_line: List[str] = []
        self.at_line_start = True
        self.last_token: Optional[Token] = None
        self.paren_depth = 0
        self.bracket_depth = 0
        self.in_for_header = False
        self.pending_newline = False
        # For line breaking
        self.break_points: List[BreakPoint] = []
        self.current_line_tokens: List[Tuple[Token, str]] = []  # (token, formatted_text)
        self.line_start_indent: int = 0  # Indent level when current line started
        # Track opening paren/bracket positions for alignment
        self.paren_columns: List[int] = []  # Stack of column positions after opening parens
        self.bracket_columns: List[int] = []  # Stack of column positions after opening brackets
        # Track if we just finished a definition block (for SeparateDefinitionBlocks)
        self.last_was_definition_close = False
    
    def format(self, tokens: List[Token]) -> str:
        """Format a list of tokens and return the formatted string."""
        # Filter out whitespace but track newlines for empty line preservation
        significant_tokens = []
        pending_newlines = 0  # Count consecutive newlines
        for token in tokens:
            if token.type == TokenType.EOF:
                continue
            if token.type == TokenType.WHITESPACE:
                continue
            if token.type == TokenType.NEWLINE:
                pending_newlines += 1
                # Keep track that there was a newline for comment handling
                if significant_tokens and significant_tokens[-1].type == TokenType.COMMENT_LINE:
                    significant_tokens.append(token)
                continue
            # Store how many empty lines preceded this token (newlines - 1)
            token.empty_lines_before = max(0, pending_newlines - 1)
            pending_newlines = 0
            significant_tokens.append(token)
        
        i = 0
        while i < len(significant_tokens):
            token = significant_tokens[i]
            next_token = significant_tokens[i + 1] if i + 1 < len(significant_tokens) else None
            prev_token = significant_tokens[i - 1] if i > 0 else None
            
            self._format_token(token, prev_token, next_token)
            self.last_token = token
            i += 1
        
        # Finalize
        self._finish_line()
        
        result = self.line_ending.join(self.output)
        
        # Ensure file ends with newline
        if result and not result.endswith(self.line_ending):
            result += self.line_ending
        
        return result
    
    def _emit(self, text: str):
        """Add text to current line."""
        if text:
            self.current_line.append(text)
            self.at_line_start = False
    
    def _emit_indent(self):
        """Emit indentation at current level."""
        if self.at_line_start:
            self.line_start_indent = self.indent_level
            if self.indent_level > 0:
                self._emit(self.config.get_indent_string(self.indent_level))
    
    def _current_line_length(self) -> int:
        """Get the current line length."""
        return len(''.join(self.current_line))
    
    def _get_nesting_depth(self) -> int:
        """Get the current nesting depth for break point priority."""
        return self.paren_depth + self.bracket_depth
    
    def _record_break_point(self, token_index: int):
        """Record a potential break point at the current position."""
        if self.config.ColumnLimit > 0:
            pos = self._current_line_length()
            depth = self._get_nesting_depth()
            # Record the current alignment column (innermost paren or bracket position)
            align_col = 0
            if self.paren_columns:
                align_col = self.paren_columns[-1]
            elif self.bracket_columns:
                align_col = self.bracket_columns[-1]
            self.break_points.append(BreakPoint(pos, depth, token_index, align_col))
    
    def _break_line_if_needed(self) -> bool:
        """
        Check if the current line exceeds ColumnLimit and break if needed.
        Returns True if a break was performed.
        """
        if self.config.ColumnLimit <= 0:
            return False
        
        line = ''.join(self.current_line)
        if len(line) <= self.config.ColumnLimit:
            return False
        
        if not self.break_points:
            return False
        
        # Sort break points by depth (lowest first = highest scope)
        # For equal depth, prefer later positions (fewer lines)
        sorted_breaks = sorted(self.break_points, key=lambda bp: (bp.depth, -bp.position))
        
        # Find the best break point that keeps the first part within limit
        best_break = None
        for bp in sorted_breaks:
            if bp.position <= self.config.ColumnLimit and bp.position > 0:
                best_break = bp
                break
        
        # If no break fits, take the earliest one at the lowest depth
        if best_break is None:
            # Filter to just the lowest depth breaks
            min_depth = min(bp.depth for bp in self.break_points)
            lowest_depth_breaks = [bp for bp in self.break_points if bp.depth == min_depth]
            # Take the first (earliest) one
            best_break = min(lowest_depth_breaks, key=lambda bp: bp.position)
        
        if best_break and best_break.position > 0:
            # Split the line at the break point
            first_part = line[:best_break.position].rstrip()
            second_part = line[best_break.position:].lstrip()
            
            # Output the first part
            self.output.append(first_part)
            
            # Calculate continuation indent - use alignment column from break point
            if best_break.align_column > 0:
                cont_indent = ' ' * best_break.align_column
            else:
                # No paren alignment - use line's starting indent + continuation indent
                cont_indent = self.config.get_indent_string(self.line_start_indent)
                cont_indent += ' ' * self.config.ContinuationIndentWidth
            
            # Set up for the continuation line
            self.current_line = [cont_indent, second_part]
            
            # Update break points for the new line
            offset = best_break.position
            new_indent_len = len(cont_indent)
            self.break_points = [
                BreakPoint(bp.position - offset + new_indent_len, bp.depth, bp.token_index, bp.align_column)
                for bp in self.break_points
                if bp.position > best_break.position
            ]
            
            # Recursively break if still too long
            self._break_line_if_needed()
            return True
        
        return False
    
    def _newline(self):
        """Finish current line and start a new one."""
        # Apply column limit breaking before finishing line
        self._break_line_if_needed()
        self.output.append(''.join(self.current_line).rstrip())
        self.current_line = []
        self.break_points = []
        self.current_line_tokens = []
        self.at_line_start = True
    
    def _finish_line(self):
        """Finish the current line."""
        if self.current_line:
            # Apply column limit breaking before finishing line
            self._break_line_if_needed()
            self.output.append(''.join(self.current_line).rstrip())
            self.current_line = []
            self.break_points = []
            self.current_line_tokens = []
            self.at_line_start = True
    
    def _space(self):
        """Add a space if not at line start and last char isn't space."""
        if not self.at_line_start:
            line = ''.join(self.current_line)
            if line and not line.endswith(' ') and not line.endswith('\t'):
                self._emit(' ')
    
    def _needs_space_before(self, token: Token, prev_token: Optional[Token]) -> bool:
        """Determine if we need a space before this token."""
        if prev_token is None:
            return False
        
        if self.at_line_start:
            return False
        
        # After opening brackets/parens - depends on config
        if prev_token.type == TokenType.LPAREN:
            return self.config.SpaceInsideParens
        if prev_token.type == TokenType.LBRACKET:
            return self.config.SpaceInsideBrackets
        if prev_token.type == TokenType.LBRACE:
            return self.config.SpaceInsideBraces
        
        # Before closing brackets
        if token.type == TokenType.RPAREN:
            return self.config.SpaceInsideParens
        if token.type == TokenType.RBRACKET:
            return self.config.SpaceInsideBrackets
        if token.type == TokenType.RBRACE:
            return self.config.SpaceInsideBraces
        
        # After comma
        if prev_token.type == TokenType.COMMA:
            return self.config.SpaceAfterComma
        
        # Before comma, semicolon - no space
        if token.type in (TokenType.COMMA, TokenType.SEMICOLON):
            return False
        
        # Colon handling - space in ternary, no space in ranges
        if token.type == TokenType.COLON:
            # In brackets (range expression), no space before colon
            if self.bracket_depth > 0:
                return False
            # In ternary, space before colon
            return True
        
        # After colon
        if prev_token.type == TokenType.COLON:
            # In brackets (range expression), no space after colon
            if self.bracket_depth > 0:
                return False
            # In ternary, space after colon (but not before unary minus)
            return True
        
        # Around assignment
        if token.type == TokenType.ASSIGNMENT or prev_token.type == TokenType.ASSIGNMENT:
            return True
        
        # Around operators
        if token.type == TokenType.OPERATOR:
            # Unary operators don't get space before
            if token.value in ('!',) and prev_token.type in (TokenType.LPAREN, TokenType.LBRACKET, 
                                                              TokenType.COMMA, TokenType.ASSIGNMENT,
                                                              TokenType.OPERATOR, TokenType.COLON,
                                                              TokenType.QUESTION):
                return False
            if token.value == '-' and prev_token.type in (TokenType.LPAREN, TokenType.LBRACKET,
                                                           TokenType.COMMA, TokenType.ASSIGNMENT,
                                                           TokenType.OPERATOR, TokenType.COLON,
                                                           TokenType.QUESTION):
                return False
            return self.config.SpaceAroundOperators
        
        if prev_token.type == TokenType.OPERATOR:
            # After unary operators (!, -)
            if prev_token.value == '!' and token.type in (TokenType.IDENTIFIER, TokenType.BOOLEAN,
                                                           TokenType.BUILTIN_FUNCTION, TokenType.LPAREN):
                return False
            # After unary minus - check if the minus was after something that makes it unary
            if prev_token.value == '-':
                # Look at what's before the minus in the output
                line = ''.join(self.current_line).rstrip()
                if line.endswith(('=', '(', '[', ',', ':', '?', '+', '-', '*', '/', '%', '<', '>', '&', '|')):
                    return False
            return self.config.SpaceAroundOperators
        
        # Before parens - function calls
        if token.type == TokenType.LPAREN:
            if prev_token.type in (TokenType.IDENTIFIER, TokenType.BUILTIN_MODULE, 
                                    TokenType.BUILTIN_FUNCTION, TokenType.KEYWORD):
                return self.config.SpaceBeforeParens
            return False
        
        # After question mark (ternary)
        if prev_token.type == TokenType.QUESTION:
            return True
        if token.type == TokenType.QUESTION:
            return True
        
        # Keywords need space after
        if prev_token.type == TokenType.KEYWORD:
            return True
        
        # Modifiers don't need space after
        if prev_token.type == TokenType.MODIFIER:
            return False
        
        # Default: space between most tokens
        if prev_token.type in (TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING,
                                TokenType.BOOLEAN, TokenType.UNDEF, TokenType.RPAREN,
                                TokenType.RBRACKET, TokenType.RBRACE):
            if token.type in (TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.BUILTIN_MODULE,
                              TokenType.BUILTIN_FUNCTION, TokenType.NUMBER, TokenType.STRING,
                              TokenType.BOOLEAN, TokenType.UNDEF):
                return True
        
        return False
    
    def _should_break_before_brace(self, token: Token, prev_token: Optional[Token]) -> bool:
        """Determine if we should break before an opening brace."""
        style = self.config.BreakBeforeBraces
        
        if style == BraceBreakingStyle.Allman:
            return True
        if style == BraceBreakingStyle.GNU:
            return True
        if style == BraceBreakingStyle.Whitesmiths:
            return True
        
        if style in (BraceBreakingStyle.Linux, BraceBreakingStyle.Mozilla,
                     BraceBreakingStyle.Stroustrup, BraceBreakingStyle.WebKit):
            # Break before function/module definitions
            if prev_token and prev_token.type == TokenType.RPAREN:
                return True
        
        return False
    
    def _format_token(self, token: Token, prev_token: Optional[Token], next_token: Optional[Token]):
        """Format a single token."""
        
        # Preserve empty lines from source (up to MaxEmptyLinesToKeep)
        empty_lines = getattr(token, 'empty_lines_before', 0)
        if empty_lines > 0 and self.at_line_start and self.config.MaxEmptyLinesToKeep > 0:
            lines_to_add = min(empty_lines, self.config.MaxEmptyLinesToKeep)
            for _ in range(lines_to_add):
                self.output.append('')
        
        # Handle comments specially
        if token.type == TokenType.COMMENT_LINE:
            if not self.at_line_start:
                self._space()
            else:
                self._emit_indent()
            self._emit(token.value)
            self._newline()
            return
        
        if token.type == TokenType.COMMENT_BLOCK:
            if not self.at_line_start:
                self._space()
            else:
                self._emit_indent()
            # Handle multi-line block comments
            lines = token.value.split('\n')
            for i, line in enumerate(lines):
                if i > 0:
                    self._newline()
                    if line.strip():
                        self._emit_indent()
                self._emit(line if i == 0 else line.lstrip())
            return
        
        if token.type == TokenType.NEWLINE:
            # Only emit if after line comment
            return
        
        # Track for/let header for semicolon handling
        if token.type == TokenType.KEYWORD and token.value in ('for', 'let', 'intersection_for'):
            self.in_for_header = True
        
        # Opening brace
        if token.type == TokenType.LBRACE:
            if self._should_break_before_brace(token, prev_token):
                self._newline()
                self._emit_indent()
            else:
                self._space()
            self._emit('{')
            self.indent_level += 1
            self._newline()
            return
        
        # Closing brace
        if token.type == TokenType.RBRACE:
            self.indent_level = max(0, self.indent_level - 1)
            if not self.at_line_start:
                self._newline()
            self._emit_indent()
            self._emit('}')
            # Track if this closes a top-level definition block
            if self.indent_level == 0:
                self.last_was_definition_close = True
            # Check if followed by else/semicolon
            if next_token and next_token.type == TokenType.KEYWORD and next_token.value == 'else':
                # In Allman style, else goes on its own line
                if self.config.BreakBeforeBraces == BraceBreakingStyle.Allman:
                    self._newline()
                # Otherwise space will be added by _needs_space_before
            elif next_token and next_token.type == TokenType.SEMICOLON:
                pass  # No newline, semicolon follows
            elif next_token and next_token.type not in (TokenType.RBRACE, TokenType.EOF, None):
                self._newline()
                # Handle SeparateDefinitionBlocks for next definition
                if self.last_was_definition_close and next_token.type == TokenType.KEYWORD:
                    if next_token.value in ('module', 'function'):
                        if self.config.SeparateDefinitionBlocks == SeparateDefinitionStyle.Always:
                            self._newline()  # Add blank line
            return
        
        # Semicolon
        if token.type == TokenType.SEMICOLON:
            self._emit(';')
            self.in_for_header = False
            if next_token and next_token.type not in (TokenType.RBRACE, TokenType.COMMENT_LINE):
                self._newline()
            elif next_token and next_token.type == TokenType.COMMENT_LINE:
                pass  # Comment will add its own handling
            return
        
        # Track parentheses
        if token.type == TokenType.LPAREN:
            self.paren_depth += 1
            if self._needs_space_before(token, prev_token):
                self._space()
            self._emit('(')
            # Track column position after opening paren for alignment
            self.paren_columns.append(self._current_line_length())
            # Record break point after opening paren
            self._record_break_point(0)
            return
        
        if token.type == TokenType.RPAREN:
            self.paren_depth = max(0, self.paren_depth - 1)
            if self.paren_columns:
                self.paren_columns.pop()
            if self.paren_depth == 0:
                self.in_for_header = False
            if self._needs_space_before(token, prev_token):
                self._space()
            self._emit(')')
            # Record break point after closing paren at depth 0 (between chained calls)
            if self.paren_depth == 0 and self.bracket_depth == 0:
                self._record_break_point(0)
            return
        
        # Brackets
        if token.type == TokenType.LBRACKET:
            self.bracket_depth += 1
            if self._needs_space_before(token, prev_token):
                self._space()
            self._emit('[')
            # Track column position after opening bracket for alignment
            self.bracket_columns.append(self._current_line_length())
            # Record break point after opening bracket
            self._record_break_point(0)
            return
        
        if token.type == TokenType.RBRACKET:
            self.bracket_depth = max(0, self.bracket_depth - 1)
            if self.bracket_columns:
                self.bracket_columns.pop()
            if self._needs_space_before(token, prev_token):
                self._space()
            self._emit(']')
            return
        
        # Comma - record break point after
        if token.type == TokenType.COMMA:
            self._emit(',')
            # Record break point after comma (before space)
            self._record_break_point(0)
            return
        
        # Default handling
        if self.at_line_start:
            self._emit_indent()
        elif self._needs_space_before(token, prev_token):
            self._space()
        
        self._emit(token.value)
        
        # Record break point after binary operators
        if token.type == TokenType.OPERATOR and token.value in ('+', '-', '*', '/', '%', '&&', '||', '<', '>', '<=', '>=', '==', '!='):
            # Only if not unary (check if space was added before)
            line = ''.join(self.current_line)
            if len(line) >= 2 and line[-len(token.value)-1] == ' ':
                self._record_break_point(0)


def format_code(source: str, config: Optional[FormatConfig] = None) -> str:
    """
    Format OpenSCAD source code.
    
    Args:
        source: The OpenSCAD source code to format.
        config: Optional FormatConfig. If not provided, uses defaults.
    
    Returns:
        Formatted source code.
    """
    if config is None:
        config = FormatConfig()
    
    tokens = tokenize(source)
    formatter = Formatter(config, source)
    return formatter.format(tokens)


def format_file(path: str, config: Optional[FormatConfig] = None, 
                in_place: bool = False) -> str:
    """
    Format an OpenSCAD file.
    
    Args:
        path: Path to the .scad file.
        config: Optional FormatConfig. If not provided, searches for .scad-format.
        in_place: If True, overwrites the file with formatted content.
    
    Returns:
        Formatted source code.
    """
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    if config is None:
        config = load_config(search_path=path)
    
    formatted = format_code(source, config)
    
    if in_place:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(formatted)
    
    return formatted
