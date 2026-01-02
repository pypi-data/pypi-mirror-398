"""Integration tests for scad-format."""

import pytest
import tempfile
import subprocess
import sys
from pathlib import Path

import scad_format
from scad_format import format_code, format_file, FormatConfig, load_config


class TestModuleImport:
    """Test importing and using as a module."""
    
    def test_import_format_function(self):
        """Can import format function."""
        from scad_format import format
        assert callable(format)
    
    def test_import_format_code(self):
        """Can import format_code function."""
        from scad_format import format_code
        assert callable(format_code)
    
    def test_import_config(self):
        """Can import FormatConfig."""
        from scad_format import FormatConfig
        config = FormatConfig()
        assert config.IndentWidth == 4
    
    def test_format_simple_code(self):
        """Format simple code via module."""
        result = scad_format.format("cube(1);")
        assert "cube(1);" in result
    
    def test_format_with_config(self):
        """Format with custom config via module."""
        config = FormatConfig(IndentWidth=2)
        result = scad_format.format_code("module foo() { cube(1); }", config)
        lines = result.split('\n')
        # Should have 2-space indent
        indented = [l for l in lines if l.startswith('  ') and not l.startswith('    ') and 'cube' in l]
        assert len(indented) >= 1


class TestFormatFile:
    """Test file formatting."""
    
    def test_format_file_returns_content(self):
        """format_file returns formatted content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.scad'
            test_file.write_text('cube(  1  );')
            
            result = format_file(str(test_file))
            assert 'cube(1);' in result
    
    def test_format_file_inplace(self):
        """format_file with in_place=True modifies file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.scad'
            test_file.write_text('cube(  1  );')
            
            format_file(str(test_file), in_place=True)
            
            content = test_file.read_text()
            assert 'cube(1);' in content
    
    def test_format_file_uses_config(self):
        """format_file uses provided config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.scad'
            test_file.write_text('module foo() { cube(1); }')
            
            config = FormatConfig(IndentWidth=8)
            result = format_file(str(test_file), config=config)
            
            # Should have 8-space indent
            lines = result.split('\n')
            indented = [l for l in lines if l.startswith('        ') and 'cube' in l]
            assert len(indented) >= 1
    
    def test_format_file_finds_config(self):
        """format_file finds .scad-format in parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            subdir = parent / 'src'
            subdir.mkdir()
            
            # Create config
            config_file = parent / '.scad-format'
            config_file.write_text('IndentWidth: 6\n')
            
            # Create test file in subdir
            test_file = subdir / 'test.scad'
            test_file.write_text('module foo() { cube(1); }')
            
            result = format_file(str(test_file))
            
            # Should use 6-space indent from config
            lines = result.split('\n')
            indented = [l for l in lines if 'cube' in l and l.startswith('      ')]
            assert len(indented) >= 1


class TestConfigFileParsing:
    """Test .scad-format file parsing."""
    
    def test_yaml_style_config(self):
        """Parse YAML-style config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / '.scad-format'
            config_file.write_text("""---
IndentWidth: 3
TabWidth: 3
UseTab: Never
BreakBeforeBraces: Allman
LineEnding: LF
...
""")
            
            config = load_config(path=str(config_file))
            
            assert config.IndentWidth == 3
            assert config.TabWidth == 3
    
    def test_simple_config(self):
        """Parse simple key: value config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / '.scad-format'
            config_file.write_text("""IndentWidth: 2
UseTab: Always
""")
            
            config = load_config(path=str(config_file))
            
            assert config.IndentWidth == 2


class TestEndToEnd:
    """End-to-end formatting tests."""
    
    def test_complete_module(self):
        """Format a complete module with various constructs."""
        code = """
module gear(teeth=20,module=1,thickness=5){
pitch_radius=module*teeth/2;
outer_radius=pitch_radius+module;
difference(){
cylinder(h=thickness,r=outer_radius,$fn=teeth*4);
translate([0,0,-1])cylinder(h=thickness+2,r=pitch_radius/3,$fn=32);
for(i=[0:teeth-1]){
rotate([0,0,i*360/teeth])translate([pitch_radius,0,-1])
cylinder(h=thickness+2,r=module*0.4,$fn=16);
}
}
}

gear();
translate([50,0,0])gear(teeth=30,module=1.5);
"""
        result = format_code(code)
        
        # Check structure is maintained
        assert 'module gear' in result
        assert 'difference()' in result
        assert 'for' in result
        assert 'gear();' in result
        assert 'translate([50, 0, 0])' in result
    
    def test_preserves_functionality(self):
        """Formatted code should be functionally equivalent."""
        # This test just ensures we don't corrupt the code
        code = """
x = 1 + 2 * 3;
y = [1, 2, 3];
z = x > 0 ? x : -x;
cube([x, y[0], z]);
"""
        result = format_code(code)
        
        # Key elements preserved
        assert 'x = 1 + 2 * 3;' in result
        assert 'y = [1, 2, 3];' in result
        assert 'x > 0 ? x : -x' in result
        assert 'cube([x, y[0], z]);' in result
    
    def test_idempotent(self):
        """Formatting should be idempotent."""
        code = "module foo() { cube([1, 2, 3]); }"
        
        result1 = format_code(code)
        result2 = format_code(result1)
        
        assert result1 == result2
    
    def test_different_configs_different_output(self):
        """Different configs should produce different output."""
        code = "module foo() { cube(1); }"
        
        config2 = FormatConfig(IndentWidth=2)
        config4 = FormatConfig(IndentWidth=4)
        
        result2 = format_code(code, config2)
        result4 = format_code(code, config4)
        
        # Should differ in indentation
        assert result2 != result4


class TestScriptExecution:
    """Test running as a script."""
    
    def test_script_help(self):
        """Script shows help."""
        result = subprocess.run(
            [sys.executable, '-m', 'scad_format', '--help'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        assert result.returncode == 0
        assert 'scad-format' in result.stdout.lower() or 'usage' in result.stdout.lower()
    
    def test_script_version(self):
        """Script shows version."""
        result = subprocess.run(
            [sys.executable, '-m', 'scad_format', '--version'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        assert result.returncode == 0
        assert 'scad-format' in result.stdout
    
    def test_script_format_file(self):
        """Script formats a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.scad'
            test_file.write_text('cube(  1  );')
            
            result = subprocess.run(
                [sys.executable, '-m', 'scad_format', str(test_file)],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )
            
            assert result.returncode == 0
            assert 'cube(1);' in result.stdout
    
    def test_script_stdin(self):
        """Script reads from stdin."""
        result = subprocess.run(
            [sys.executable, '-m', 'scad_format'],
            input='cube(  1  );',
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert 'cube(1);' in result.stdout
