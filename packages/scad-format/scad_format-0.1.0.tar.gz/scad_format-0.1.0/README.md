# scad-format

A code formatter for OpenSCAD files, similar to clang-format.

## Features

- Format OpenSCAD source code with configurable style options
- Supports `.scad-format` configuration files (clang-format style syntax)
- Command-line interface compatible with clang-format workflows
- Can be used as a Python module or standalone script
- Supports piping, in-place editing, and batch processing

## Installation

```bash
pip install scad-format
```

Or install from source:

```bash
git clone https://github.com/ashleyharris-maptek-com-au/scad-format
cd scad-format
pip install -e .
```

## Usage

### Command Line

```bash
# Format a file and print to stdout
scad-format myfile.scad

# Format in place
scad-format -i myfile.scad

# Format multiple files in place
scad-format -i *.scad

# Read from stdin
cat myfile.scad | scad-format

# Use specific style
scad-format --style="{IndentWidth: 2}" myfile.scad

# Use config file from directory tree
scad-format --style=file myfile.scad

# Dry run (show what would change)
scad-format -n myfile.scad

# Dump current config
scad-format --dump-config
```

### As a Python Module

```python
import scad_format

# Simple formatting
code = "module foo(){cube(1);}"
formatted = scad_format.format(code)
print(formatted)

# With custom configuration
from scad_format import FormatConfig, format_code

config = FormatConfig(IndentWidth=2, UseTab="Never")
formatted = format_code(code, config)

# Format a file
from scad_format import format_file

formatted = format_file("myfile.scad")

# Format a file in place
format_file("myfile.scad", in_place=True)
```

### As a Standalone Script

```bash
python scad-format.py myfile.scad
python scad-format.py -i myfile.scad
cat myfile.scad | python scad-format.py
```

## Configuration

Create a `.scad-format` file in your project directory (searches parent directories like clang-format):

```yaml
---
# Indentation
IndentWidth: 4
TabWidth: 4
ContinuationIndentWidth: 4
UseTab: Never

# Brace style: Attach, Allman, Linux, Mozilla, Stroustrup, WebKit, GNU, Whitesmiths
BreakBeforeBraces: Attach

# Line endings: LF, CRLF, DeriveLF, DeriveCRLF
LineEnding: DeriveLF

# Optional settings
ColumnLimit: 0
SpaceAfterComma: true
SpaceBeforeParens: false
SpaceInsideParens: false
SpaceInsideBrackets: false
SpaceInsideBraces: true
SpaceAroundOperators: true
...
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `IndentWidth` | int | 4 | Number of spaces per indentation level |
| `TabWidth` | int | 4 | Width of a tab character |
| `ContinuationIndentWidth` | int | 4 | Indent for continuation lines |
| `UseTab` | enum | Never | Tab usage: Never, ForIndentation, Always |
| `BreakBeforeBraces` | enum | Attach | Brace breaking style |
| `LineEnding` | enum | DeriveLF | Line ending style |
| `ColumnLimit` | int | 0 | Max line length (0 = no limit) |
| `SpaceAfterComma` | bool | true | Add space after commas |
| `SpaceBeforeParens` | bool | false | Add space before parentheses |
| `SpaceInsideParens` | bool | false | Add space inside parentheses |
| `SpaceInsideBrackets` | bool | false | Add space inside brackets |
| `SpaceInsideBraces` | bool | true | Add space inside braces |
| `SpaceAroundOperators` | bool | true | Add space around operators |

### Brace Breaking Styles

- **Attach**: `module foo() {` - Brace on same line
- **Allman**: Brace on new line, aligned with statement
- **Linux**: Like Attach, but break before function definitions
- **Stroustrup**: Like Attach, but break before function definitions and catch
- **GNU**: Always break, braces are indented

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=scad_format
```

## License

MIT License
