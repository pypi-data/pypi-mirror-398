"""
Entry point for running scad_format as a module.

Usage: python -m scad_format [args]
"""

import sys
from .cli import main

if __name__ == '__main__':
    sys.exit(main())
