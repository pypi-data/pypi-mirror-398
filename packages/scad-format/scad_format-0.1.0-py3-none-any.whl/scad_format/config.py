"""
Configuration handling for scad-format.

Supports .scad-format files with clang-format style syntax.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path


class BraceBreakingStyle(Enum):
    """Brace breaking styles, matching clang-format."""
    Attach = "Attach"           # Always attach braces to surrounding context
    Linux = "Linux"             # Like Attach, but break before braces on function definitions
    Mozilla = "Mozilla"         # Like Attach, but break before braces on enums and functions
    Stroustrup = "Stroustrup"   # Like Attach, but break before function definitions and catch
    Allman = "Allman"           # Always break before braces
    Whitesmiths = "Whitesmiths" # Like Allman but indent braces
    GNU = "GNU"                 # Always break, braces indented
    WebKit = "WebKit"           # Like Attach, but break before functions
    Custom = "Custom"           # Configure each brace type individually


class UseTabStyle(Enum):
    """Tab usage styles, matching clang-format."""
    Never = "Never"                       # Never use tabs
    ForIndentation = "ForIndentation"     # Use tabs only for indentation
    ForContinuationAndIndentation = "ForContinuationAndIndentation"
    AlignWithSpaces = "AlignWithSpaces"   # Use tabs for indentation, spaces for alignment
    Always = "Always"                     # Use tabs whenever possible


class LineEndingStyle(Enum):
    """Line ending styles, matching clang-format."""
    LF = "LF"           # Unix style \n
    CRLF = "CRLF"       # Windows style \r\n
    DeriveLF = "DeriveLF"     # Use LF unless input has more CRLF
    DeriveCRLF = "DeriveCRLF" # Use CRLF unless input has more LF


class SeparateDefinitionStyle(Enum):
    """Controls blank lines between definition blocks, matching clang-format."""
    Leave = "Leave"     # Keep existing blank lines as-is
    Always = "Always"   # Always insert blank line between definitions
    Never = "Never"     # Never insert blank lines between definitions


@dataclass
class FormatConfig:
    """Configuration options for formatting OpenSCAD code."""
    
    # Brace style
    BreakBeforeBraces: BraceBreakingStyle = BraceBreakingStyle.Attach
    
    # Indentation
    IndentWidth: int = 4
    TabWidth: int = 4
    ContinuationIndentWidth: int = 4
    UseTab: UseTabStyle = UseTabStyle.Never
    
    # Line endings
    LineEnding: LineEndingStyle = LineEndingStyle.DeriveLF
    
    # Additional options
    ColumnLimit: int = 0  # 0 means no limit
    MaxEmptyLinesToKeep: int = 1  # Maximum consecutive empty lines to preserve
    SeparateDefinitionBlocks: SeparateDefinitionStyle = SeparateDefinitionStyle.Leave
    SpaceAfterComma: bool = True
    SpaceBeforeParens: bool = False
    SpaceInsideParens: bool = False
    SpaceInsideBrackets: bool = False
    SpaceInsideBraces: bool = True
    SpaceAroundOperators: bool = True
    
    def get_indent_string(self, level: int = 1) -> str:
        """Get the indentation string for a given level."""
        if self.UseTab == UseTabStyle.Never:
            return ' ' * (self.IndentWidth * level)
        elif self.UseTab == UseTabStyle.Always:
            return '\t' * level
        else:
            # ForIndentation and variants: use tabs for full indents
            return '\t' * level
    
    def get_continuation_indent(self) -> str:
        """Get the continuation indentation string."""
        if self.UseTab == UseTabStyle.Never:
            return ' ' * self.ContinuationIndentWidth
        elif self.UseTab in (UseTabStyle.ForContinuationAndIndentation, UseTabStyle.Always):
            tabs = self.ContinuationIndentWidth // self.TabWidth
            spaces = self.ContinuationIndentWidth % self.TabWidth
            return '\t' * tabs + ' ' * spaces
        else:
            return ' ' * self.ContinuationIndentWidth
    
    def get_line_ending(self, source: str = "") -> str:
        """Get the line ending string to use."""
        if self.LineEnding == LineEndingStyle.LF:
            return '\n'
        elif self.LineEnding == LineEndingStyle.CRLF:
            return '\r\n'
        elif self.LineEnding == LineEndingStyle.DeriveLF:
            # Count line endings in source
            crlf_count = source.count('\r\n')
            lf_count = source.count('\n') - crlf_count
            return '\r\n' if crlf_count > lf_count else '\n'
        elif self.LineEnding == LineEndingStyle.DeriveCRLF:
            crlf_count = source.count('\r\n')
            lf_count = source.count('\n') - crlf_count
            return '\n' if lf_count > crlf_count else '\r\n'
        return '\n'


def parse_value(value_str: str) -> Any:
    """Parse a value string from config file."""
    value_str = value_str.strip()
    
    # Boolean
    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False
    
    # Integer
    try:
        return int(value_str)
    except ValueError:
        pass
    
    # String (might be enum value)
    return value_str


def load_config_from_string(content: str) -> FormatConfig:
    """Load configuration from a string in clang-format style."""
    config = FormatConfig()
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#') or line.startswith('---'):
            continue
        
        # Parse key: value
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = parse_value(value)
            
            # Map to config fields
            if key == 'BreakBeforeBraces':
                try:
                    config.BreakBeforeBraces = BraceBreakingStyle(value)
                except ValueError:
                    pass
            elif key == 'IndentWidth':
                config.IndentWidth = int(value)
            elif key == 'TabWidth':
                config.TabWidth = int(value)
            elif key == 'ContinuationIndentWidth':
                config.ContinuationIndentWidth = int(value)
            elif key == 'UseTab':
                try:
                    config.UseTab = UseTabStyle(value)
                except ValueError:
                    pass
            elif key == 'LineEnding':
                try:
                    config.LineEnding = LineEndingStyle(value)
                except ValueError:
                    pass
            elif key == 'ColumnLimit':
                config.ColumnLimit = int(value)
            elif key == 'SpaceAfterComma':
                config.SpaceAfterComma = bool(value)
            elif key == 'SpaceBeforeParens':
                config.SpaceBeforeParens = bool(value)
            elif key == 'SpaceInsideParens':
                config.SpaceInsideParens = bool(value)
            elif key == 'SpaceInsideBrackets':
                config.SpaceInsideBrackets = bool(value)
            elif key == 'SpaceInsideBraces':
                config.SpaceInsideBraces = bool(value)
            elif key == 'SpaceAroundOperators':
                config.SpaceAroundOperators = bool(value)
            elif key in ('SeparateDefinitionBlocks', 'SeparateDefinitionStyle'):
                try:
                    config.SeparateDefinitionBlocks = SeparateDefinitionStyle(value)
                except ValueError:
                    pass
            elif key == 'MaxEmptyLinesToKeep':
                config.MaxEmptyLinesToKeep = int(value)
    
    return config


def find_config_file(start_path: str) -> Optional[Path]:
    """
    Find a .scad-format config file by searching up the directory tree.
    Similar to how clang-format finds .clang-format files.
    """
    current = Path(start_path).resolve()
    
    if current.is_file():
        current = current.parent
    
    while current != current.parent:
        config_file = current / '.scad-format'
        if config_file.exists():
            return config_file
        
        # Also check for _scad-format (alternative name)
        config_file = current / '_scad-format'
        if config_file.exists():
            return config_file
        
        current = current.parent
    
    # Check root
    for name in ['.scad-format', '_scad-format']:
        config_file = current / name
        if config_file.exists():
            return config_file
    
    return None


def load_config(path: Optional[str] = None, search_path: Optional[str] = None) -> FormatConfig:
    """
    Load configuration from a file.
    
    Args:
        path: Direct path to config file. If provided, this is used.
        search_path: Path to start searching for .scad-format file.
                    If not provided, uses current directory.
    
    Returns:
        FormatConfig with loaded settings, or defaults if no config found.
    """
    config_path = None
    
    if path:
        config_path = Path(path)
    elif search_path:
        config_path = find_config_file(search_path)
    else:
        config_path = find_config_file(os.getcwd())
    
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return load_config_from_string(f.read())
    
    return FormatConfig()
