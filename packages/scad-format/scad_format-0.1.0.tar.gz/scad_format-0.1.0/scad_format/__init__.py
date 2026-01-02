"""
scad-format: A code formatter for OpenSCAD files.

Usage as module:
    import scad_format
    formatted = scad_format.format("module foo() { cube(1); }")
    
Usage as CLI:
    python -m scad_format file.scad
    python -m scad_format -i file.scad  # in-place
    cat file.scad | python -m scad_format  # pipe
"""

from .formatter import format_code, format_file
from .config import FormatConfig, load_config
from .tokenizer import tokenize

__version__ = "0.1.0"
__all__ = ["format_code", "format_file", "FormatConfig", "load_config", "tokenize"]

# Convenience alias
format = format_code
