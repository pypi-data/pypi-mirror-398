"""Tests for the command-line interface."""

import pytest
import tempfile
import os
from pathlib import Path
from io import StringIO
import sys

from scad_format.cli import main, create_parser, get_config, parse_inline_style, dump_config
from scad_format.config import FormatConfig


class TestArgumentParser:
    """Test argument parsing."""
    
    def test_no_args(self):
        """No arguments is valid (reads from stdin)."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.files == []
        assert not args.inplace
    
    def test_single_file(self):
        """Single file argument."""
        parser = create_parser()
        args = parser.parse_args(['test.scad'])
        assert args.files == ['test.scad']
    
    def test_multiple_files(self):
        """Multiple file arguments."""
        parser = create_parser()
        args = parser.parse_args(['a.scad', 'b.scad', 'c.scad'])
        assert args.files == ['a.scad', 'b.scad', 'c.scad']
    
    def test_inplace_flag(self):
        """In-place flag."""
        parser = create_parser()
        args = parser.parse_args(['-i', 'test.scad'])
        assert args.inplace
        
        args = parser.parse_args(['--in-place', 'test.scad'])
        assert args.inplace
    
    def test_style_option(self):
        """Style option."""
        parser = create_parser()
        args = parser.parse_args(['--style', 'file', 'test.scad'])
        assert args.style == 'file'
    
    def test_inline_style(self):
        """Inline style option."""
        parser = create_parser()
        args = parser.parse_args(['--style', '{IndentWidth: 2}', 'test.scad'])
        assert args.style == '{IndentWidth: 2}'
    
    def test_assume_filename(self):
        """Assume filename option."""
        parser = create_parser()
        args = parser.parse_args(['--assume-filename', 'dir/test.scad'])
        assert args.assume_filename == 'dir/test.scad'
    
    def test_dry_run(self):
        """Dry run flag."""
        parser = create_parser()
        args = parser.parse_args(['-n', 'test.scad'])
        assert args.dry_run
    
    def test_dump_config(self):
        """Dump config flag."""
        parser = create_parser()
        args = parser.parse_args(['--dump-config'])
        assert args.dump_config
    
    def test_version(self):
        """Version flag."""
        parser = create_parser()
        args = parser.parse_args(['--version'])
        assert args.version
    
    def test_indent_width_override(self):
        """Indent width override."""
        parser = create_parser()
        args = parser.parse_args(['--indent-width', '2', 'test.scad'])
        assert args.indent_width == 2


class TestInlineStyleParsing:
    """Test inline style string parsing."""
    
    def test_simple_style(self):
        """Parse simple inline style."""
        config = parse_inline_style('{IndentWidth: 2}')
        assert config.IndentWidth == 2
    
    def test_multiple_options(self):
        """Parse multiple options."""
        config = parse_inline_style('{IndentWidth: 2, TabWidth: 4, UseTab: Never}')
        assert config.IndentWidth == 2
        assert config.TabWidth == 4
    
    def test_without_braces(self):
        """Parse without braces."""
        config = parse_inline_style('IndentWidth: 2')
        assert config.IndentWidth == 2


class TestGetConfig:
    """Test configuration resolution."""
    
    def test_default_config(self):
        """Get default config when no options specified."""
        parser = create_parser()
        args = parser.parse_args([])
        config = get_config(args)
        
        assert config.IndentWidth == 4  # default
    
    def test_inline_style_override(self):
        """Inline style overrides defaults."""
        parser = create_parser()
        args = parser.parse_args(['--style', '{IndentWidth: 2}'])
        config = get_config(args)
        
        assert config.IndentWidth == 2
    
    def test_command_line_override(self):
        """Command line options override style."""
        parser = create_parser()
        args = parser.parse_args(['--style', '{IndentWidth: 2}', '--indent-width', '8'])
        config = get_config(args)
        
        assert config.IndentWidth == 8


class TestDumpConfig:
    """Test config dumping."""
    
    def test_dump_default_config(self):
        """Dump default configuration."""
        config = FormatConfig()
        output = dump_config(config)
        
        assert 'IndentWidth: 4' in output
        assert 'TabWidth: 4' in output
        assert 'UseTab: Never' in output
        assert '---' in output  # YAML header


class TestMainFunction:
    """Test main CLI entry point."""
    
    def test_version_output(self, capsys):
        """Test --version output."""
        result = main(['--version'])
        captured = capsys.readouterr()
        
        assert result == 0
        assert 'scad-format' in captured.out
    
    def test_dump_config_output(self, capsys):
        """Test --dump-config output."""
        result = main(['--dump-config'])
        captured = capsys.readouterr()
        
        assert result == 0
        assert 'IndentWidth' in captured.out
    
    def test_format_file(self, capsys):
        """Test formatting a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.scad'
            test_file.write_text('cube(1);')
            
            result = main([str(test_file)])
            captured = capsys.readouterr()
            
            assert result == 0
            assert 'cube(1);' in captured.out
    
    def test_format_file_inplace(self):
        """Test in-place formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.scad'
            test_file.write_text('cube(  1  );')
            
            result = main(['-i', str(test_file)])
            
            assert result == 0
            content = test_file.read_text()
            assert 'cube(1);' in content
    
    def test_format_missing_file(self, capsys):
        """Test error on missing file."""
        result = main(['nonexistent.scad'])
        captured = capsys.readouterr()
        
        assert result == 1
        assert 'not found' in captured.err.lower() or 'error' in captured.err.lower()
    
    def test_dry_run(self, capsys):
        """Test dry run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.scad'
            original = 'cube(  1  );'
            test_file.write_text(original)
            
            result = main(['-n', str(test_file)])
            
            assert result == 0
            # File should be unchanged
            assert test_file.read_text() == original
    
    def test_inplace_requires_files(self, capsys):
        """Test that -i requires file arguments."""
        result = main(['-i'])
        captured = capsys.readouterr()
        
        assert result == 1
        assert 'requires' in captured.err.lower() or 'error' in captured.err.lower()
    
    def test_multiple_files(self, capsys):
        """Test formatting multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / 'a.scad'
            file2 = Path(tmpdir) / 'b.scad'
            file1.write_text('cube(1);')
            file2.write_text('sphere(2);')
            
            result = main([str(file1), str(file2)])
            captured = capsys.readouterr()
            
            assert result == 0
            assert 'cube(1);' in captured.out
            assert 'sphere(2);' in captured.out
    
    def test_with_config_file(self, capsys):
        """Test using a config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file
            config_file = Path(tmpdir) / '.scad-format'
            config_file.write_text('IndentWidth: 2\n')
            
            # Create test file
            test_file = Path(tmpdir) / 'test.scad'
            test_file.write_text('module foo() { cube(1); }')
            
            result = main(['--style', 'file', str(test_file)])
            captured = capsys.readouterr()
            
            assert result == 0
            # Should use 2-space indent from config
            lines = captured.out.split('\n')
            indented = [l for l in lines if l.startswith('  ') and 'cube' in l]
            assert len(indented) >= 1


class TestStdinProcessing:
    """Test stdin processing."""
    
    def test_stdin_input(self, monkeypatch, capsys):
        """Test reading from stdin."""
        input_code = 'cube(  1  );'
        monkeypatch.setattr('sys.stdin', StringIO(input_code))
        
        result = main([])
        captured = capsys.readouterr()
        
        assert result == 0
        assert 'cube(1);' in captured.out
    
    def test_stdin_with_style(self, monkeypatch, capsys):
        """Test stdin with inline style."""
        input_code = 'module foo() { cube(1); }'
        monkeypatch.setattr('sys.stdin', StringIO(input_code))
        
        result = main(['--style', '{IndentWidth: 2}'])
        captured = capsys.readouterr()
        
        assert result == 0
        # Check 2-space indentation
        lines = captured.out.split('\n')
        indented = [l for l in lines if l.startswith('  ') and not l.startswith('    ') and 'cube' in l]
        assert len(indented) >= 1
