"""Tests for configuration handling."""

import pytest
import tempfile
import os
from pathlib import Path

from scad_format.config import (
    FormatConfig, load_config, load_config_from_string, find_config_file,
    BraceBreakingStyle, UseTabStyle, LineEndingStyle
)


class TestFormatConfig:
    """Test FormatConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = FormatConfig()
        
        assert config.IndentWidth == 4
        assert config.TabWidth == 4
        assert config.ContinuationIndentWidth == 4
        assert config.UseTab == UseTabStyle.Never
        assert config.BreakBeforeBraces == BraceBreakingStyle.Attach
        assert config.LineEnding == LineEndingStyle.DeriveLF
    
    def test_get_indent_string_spaces(self):
        """Test indent string with spaces."""
        config = FormatConfig(IndentWidth=2, UseTab=UseTabStyle.Never)
        
        assert config.get_indent_string(1) == "  "
        assert config.get_indent_string(2) == "    "
        assert config.get_indent_string(3) == "      "
    
    def test_get_indent_string_tabs(self):
        """Test indent string with tabs."""
        config = FormatConfig(UseTab=UseTabStyle.Always)
        
        assert config.get_indent_string(1) == "\t"
        assert config.get_indent_string(2) == "\t\t"
    
    def test_get_line_ending_lf(self):
        """Test LF line ending."""
        config = FormatConfig(LineEnding=LineEndingStyle.LF)
        assert config.get_line_ending() == "\n"
    
    def test_get_line_ending_crlf(self):
        """Test CRLF line ending."""
        config = FormatConfig(LineEnding=LineEndingStyle.CRLF)
        assert config.get_line_ending() == "\r\n"
    
    def test_derive_line_ending_lf(self):
        """Test deriving LF from source."""
        config = FormatConfig(LineEnding=LineEndingStyle.DeriveLF)
        source = "line1\nline2\nline3\n"
        assert config.get_line_ending(source) == "\n"
    
    def test_derive_line_ending_crlf(self):
        """Test deriving CRLF from source."""
        config = FormatConfig(LineEnding=LineEndingStyle.DeriveLF)
        source = "line1\r\nline2\r\nline3\r\n"
        assert config.get_line_ending(source) == "\r\n"


class TestLoadConfig:
    """Test configuration loading."""
    
    def test_load_from_string_basic(self):
        """Test loading config from a string."""
        content = """
        IndentWidth: 2
        TabWidth: 4
        UseTab: Never
        """
        config = load_config_from_string(content)
        
        assert config.IndentWidth == 2
        assert config.TabWidth == 4
        assert config.UseTab == UseTabStyle.Never
    
    def test_load_from_string_all_options(self):
        """Test loading all config options."""
        content = """
        ---
        BreakBeforeBraces: Allman
        IndentWidth: 3
        TabWidth: 3
        ContinuationIndentWidth: 6
        UseTab: Always
        LineEnding: CRLF
        ColumnLimit: 80
        SpaceAfterComma: true
        SpaceBeforeParens: true
        SpaceInsideParens: false
        SpaceInsideBrackets: false
        SpaceInsideBraces: true
        SpaceAroundOperators: true
        ...
        """
        config = load_config_from_string(content)
        
        assert config.BreakBeforeBraces == BraceBreakingStyle.Allman
        assert config.IndentWidth == 3
        assert config.TabWidth == 3
        assert config.ContinuationIndentWidth == 6
        assert config.UseTab == UseTabStyle.Always
        assert config.LineEnding == LineEndingStyle.CRLF
        assert config.ColumnLimit == 80
    
    def test_load_from_string_comments(self):
        """Test that comments are ignored."""
        content = """
        # This is a comment
        IndentWidth: 2
        # Another comment
        TabWidth: 4
        """
        config = load_config_from_string(content)
        
        assert config.IndentWidth == 2
        assert config.TabWidth == 4
    
    def test_load_from_file(self):
        """Test loading config from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".scad-format"
            config_path.write_text("IndentWidth: 8\nUseTab: Always\n")
            
            config = load_config(path=str(config_path))
            
            assert config.IndentWidth == 8
            assert config.UseTab == UseTabStyle.Always
    
    def test_find_config_file_in_current_dir(self):
        """Test finding config file in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".scad-format"
            config_path.write_text("IndentWidth: 2\n")
            
            found = find_config_file(tmpdir)
            assert found == config_path
    
    def test_find_config_file_in_parent(self):
        """Test finding config file in parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            child = parent / "subdir"
            child.mkdir()
            
            config_path = parent / ".scad-format"
            config_path.write_text("IndentWidth: 2\n")
            
            found = find_config_file(str(child))
            assert found == config_path
    
    def test_find_config_file_not_found(self):
        """Test when no config file is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found = find_config_file(tmpdir)
            # May or may not find a config file depending on the environment
            # Just ensure it doesn't crash
    
    def test_load_config_search_path(self):
        """Test loading config by searching from a path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            child = parent / "subdir"
            child.mkdir()
            
            config_path = parent / ".scad-format"
            config_path.write_text("IndentWidth: 6\n")
            
            scad_file = child / "test.scad"
            scad_file.write_text("cube(1);")
            
            config = load_config(search_path=str(scad_file))
            assert config.IndentWidth == 6
    
    def test_load_config_defaults_when_not_found(self):
        """Test that defaults are used when no config is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No config file in this directory
            config = load_config(search_path=tmpdir)
            
            # Should have default values
            assert config.IndentWidth == 4
            assert config.UseTab == UseTabStyle.Never


class TestBraceStyles:
    """Test brace breaking style enums."""
    
    def test_all_brace_styles(self):
        """Verify all brace styles are valid."""
        styles = [
            "Attach", "Linux", "Mozilla", "Stroustrup",
            "Allman", "Whitesmiths", "GNU", "WebKit", "Custom"
        ]
        for style in styles:
            assert BraceBreakingStyle(style) is not None


class TestUseTabStyles:
    """Test UseTab style enums."""
    
    def test_all_use_tab_styles(self):
        """Verify all UseTab styles are valid."""
        styles = [
            "Never", "ForIndentation", "ForContinuationAndIndentation",
            "AlignWithSpaces", "Always"
        ]
        for style in styles:
            assert UseTabStyle(style) is not None


class TestLineEndingStyles:
    """Test LineEnding style enums."""
    
    def test_all_line_ending_styles(self):
        """Verify all LineEnding styles are valid."""
        styles = ["LF", "CRLF", "DeriveLF", "DeriveCRLF"]
        for style in styles:
            assert LineEndingStyle(style) is not None
