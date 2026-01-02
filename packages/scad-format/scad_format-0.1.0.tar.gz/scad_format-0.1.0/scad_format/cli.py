"""
Command-line interface for scad-format.

Supports clang-format style arguments.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

from .config import FormatConfig, load_config, load_config_from_string
from .formatter import format_code, format_file


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with clang-format compatible options."""
    parser = argparse.ArgumentParser(
        prog='scad-format',
        description='Format OpenSCAD source code.',
        epilog='Similar to clang-format but for OpenSCAD files.'
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        help='Files to format. If none provided, reads from stdin.'
    )
    
    parser.add_argument(
        '-i', '--in-place',
        action='store_true',
        dest='inplace',
        help='Inplace edit <file>s, if specified.'
    )
    
    parser.add_argument(
        '--style',
        type=str,
        default=None,
        help='Coding style. Use "file" to load from .scad-format, '
             'or inline YAML like "{IndentWidth: 2}".'
    )
    
    parser.add_argument(
        '--assume-filename',
        type=str,
        default=None,
        dest='assume_filename',
        help='When reading from stdin, use this filename to find .scad-format '
             'and determine formatting.'
    )
    
    parser.add_argument(
        '--fallback-style',
        type=str,
        default=None,
        dest='fallback_style',
        help='Fallback style if .scad-format is not found.'
    )
    
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Do not write changes, just show what would be done.'
    )
    
    parser.add_argument(
        '--dump-config',
        action='store_true',
        dest='dump_config',
        help='Dump the current configuration and exit.'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Print version and exit.'
    )
    
    # Style override options
    parser.add_argument(
        '--indent-width',
        type=int,
        default=None,
        dest='indent_width',
        help='Override IndentWidth.'
    )
    
    parser.add_argument(
        '--tab-width',
        type=int,
        default=None,
        dest='tab_width',
        help='Override TabWidth.'
    )
    
    parser.add_argument(
        '--use-tab',
        type=str,
        default=None,
        dest='use_tab',
        help='Override UseTab (Never, ForIndentation, Always, etc.).'
    )
    
    return parser


def parse_inline_style(style_str: str) -> FormatConfig:
    """Parse an inline style specification like '{IndentWidth: 2}'."""
    # Remove braces
    style_str = style_str.strip()
    if style_str.startswith('{') and style_str.endswith('}'):
        style_str = style_str[1:-1]
    
    # Convert comma-separated to newline-separated for parser
    content = style_str.replace(',', '\n')
    return load_config_from_string(content)


def get_config(args, file_path: Optional[str] = None) -> FormatConfig:
    """Get the configuration based on arguments."""
    config = FormatConfig()
    
    # Load from style option or search for file
    if args.style:
        if args.style.lower() == 'file':
            search_path = file_path or args.assume_filename or '.'
            config = load_config(search_path=search_path)
        elif args.style.startswith('{'):
            config = parse_inline_style(args.style)
        else:
            # Try as preset name (future: add preset styles)
            pass
    elif file_path or args.assume_filename:
        config = load_config(search_path=file_path or args.assume_filename)
    
    # Apply command-line overrides
    if args.indent_width is not None:
        config.IndentWidth = args.indent_width
    if args.tab_width is not None:
        config.TabWidth = args.tab_width
    if args.use_tab is not None:
        from .config import UseTabStyle
        try:
            config.UseTab = UseTabStyle(args.use_tab)
        except ValueError:
            pass
    
    return config


def dump_config(config: FormatConfig) -> str:
    """Dump configuration to YAML-style string."""
    lines = [
        '---',
        f'BreakBeforeBraces: {config.BreakBeforeBraces.value}',
        f'IndentWidth: {config.IndentWidth}',
        f'TabWidth: {config.TabWidth}',
        f'ContinuationIndentWidth: {config.ContinuationIndentWidth}',
        f'UseTab: {config.UseTab.value}',
        f'LineEnding: {config.LineEnding.value}',
        f'ColumnLimit: {config.ColumnLimit}',
        f'SpaceAfterComma: {str(config.SpaceAfterComma).lower()}',
        f'SpaceBeforeParens: {str(config.SpaceBeforeParens).lower()}',
        f'SpaceInsideParens: {str(config.SpaceInsideParens).lower()}',
        f'SpaceInsideBrackets: {str(config.SpaceInsideBrackets).lower()}',
        f'SpaceInsideBraces: {str(config.SpaceInsideBraces).lower()}',
        f'SpaceAroundOperators: {str(config.SpaceAroundOperators).lower()}',
        '...',
    ]
    return '\n'.join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Handle version
    if args.version:
        from . import __version__
        print(f'scad-format {__version__}')
        return 0
    
    # Handle dump-config
    if args.dump_config:
        config = get_config(args)
        print(dump_config(config))
        return 0
    
    # No files: read from stdin
    if not args.files:
        if args.inplace:
            print('Error: -i/--in-place requires file arguments', file=sys.stderr)
            return 1
        
        source = sys.stdin.read()
        config = get_config(args)
        try:
            formatted = format_code(source, config)
            sys.stdout.write(formatted)
        except Exception as e:
            print(f'Error formatting: {e}', file=sys.stderr)
            return 1
        return 0
    
    # Format files
    exit_code = 0
    for file_path in args.files:
        path = Path(file_path)
        
        if not path.exists():
            print(f'Error: File not found: {file_path}', file=sys.stderr)
            exit_code = 1
            continue
        
        try:
            config = get_config(args, str(path))
            
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            formatted = format_code(source, config)
            
            if args.dry_run:
                if source != formatted:
                    print(f'Would reformat: {file_path}')
            elif args.inplace:
                if source != formatted:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(formatted)
            else:
                sys.stdout.write(formatted)
        
        except Exception as e:
            print(f'Error formatting {file_path}: {e}', file=sys.stderr)
            exit_code = 1
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
