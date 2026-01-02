#!/usr/bin/env python3
"""
scad-format: A code formatter for OpenSCAD files.

This script can be run standalone:
    python scad-format.py file.scad
    python scad-format.py -i file.scad
    cat file.scad | python scad-format.py

Or the module can be imported:
    import scad_format
    formatted = scad_format.format("module foo() { cube(1); }")
"""

import sys
import os

# Add the parent directory to path so we can import scad_format
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from scad_format.cli import main

if __name__ == '__main__':
    sys.exit(main())
