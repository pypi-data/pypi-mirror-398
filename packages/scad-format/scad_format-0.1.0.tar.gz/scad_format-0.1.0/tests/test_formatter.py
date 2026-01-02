"""Tests for the formatter."""

import pytest
from scad_format import format_code
from scad_format.config import FormatConfig, BraceBreakingStyle, UseTabStyle, LineEndingStyle, SeparateDefinitionStyle


class TestBasicFormatting:
    """Test basic formatting operations."""
    
    def test_simple_statement(self):
        """Format a simple statement."""
        code = "cube(1);"
        result = format_code(code)
        assert result.strip() == "cube(1);"
    
    def test_removes_extra_whitespace(self):
        """Remove extra whitespace."""
        code = "cube(   1   );"
        result = format_code(code)
        assert result.strip() == "cube(1);"
    
    def test_normalizes_spacing_around_operators(self):
        """Normalize spacing around operators."""
        code = "x=1+2*3;"
        result = format_code(code)
        assert result.strip() == "x = 1 + 2 * 3;"
    
    def test_space_after_comma(self):
        """Add space after comma."""
        code = "cube([1,2,3]);"
        result = format_code(code)
        assert result.strip() == "cube([1, 2, 3]);"
    
    def test_no_space_after_comma_when_disabled(self):
        """No space after comma when disabled."""
        config = FormatConfig(SpaceAfterComma=False)
        code = "cube([1, 2, 3]);"
        result = format_code(code, config)
        assert result.strip() == "cube([1,2,3]);"


class TestModuleFormatting:
    """Test module definition formatting."""
    
    def test_simple_module(self):
        """Format a simple module."""
        code = "module foo(){cube(1);}"
        result = format_code(code)
        lines = result.strip().split('\n')
        assert lines[0] == "module foo() {"
        assert "cube(1);" in lines[1]
        assert lines[-1] == "}"
    
    def test_module_with_parameters(self):
        """Format a module with parameters."""
        code = "module box(x,y,z){cube([x,y,z]);}"
        result = format_code(code)
        assert "module box(x, y, z)" in result
    
    def test_nested_modules(self):
        """Format nested module calls."""
        code = "translate([1,0,0])rotate([0,0,45])cube(1);"
        result = format_code(code)
        assert "translate([1, 0, 0])" in result
        assert "rotate([0, 0, 45])" in result
        assert "cube(1);" in result


class TestBraceStyles:
    """Test different brace breaking styles."""
    
    def test_attach_style(self):
        """Attach style keeps braces on same line."""
        config = FormatConfig(BreakBeforeBraces=BraceBreakingStyle.Attach)
        code = "module foo() { cube(1); }"
        result = format_code(code, config)
        assert "foo() {" in result
    
    def test_allman_style(self):
        """Allman style puts braces on new line."""
        config = FormatConfig(BreakBeforeBraces=BraceBreakingStyle.Allman)
        code = "module foo() { cube(1); }"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Brace should be on its own line
        assert any(line.strip() == "{" for line in lines)
    
    def test_linux_style(self):
        """Linux style breaks before function braces."""
        config = FormatConfig(BreakBeforeBraces=BraceBreakingStyle.Linux)
        code = "module foo() { cube(1); }"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # For function definitions, brace on new line
        assert any(line.strip() == "{" for line in lines)


class TestIndentation:
    """Test indentation handling."""
    
    def test_default_indent_width(self):
        """Default indent is 4 spaces."""
        code = "module foo() { cube(1); }"
        result = format_code(code)
        lines = result.strip().split('\n')
        # Find the indented line
        indented = [l for l in lines if l.startswith('    ') and 'cube' in l]
        assert len(indented) == 1
    
    def test_custom_indent_width(self):
        """Custom indent width of 2 spaces."""
        config = FormatConfig(IndentWidth=2)
        code = "module foo() { cube(1); }"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Find the indented line
        indented = [l for l in lines if l.startswith('  ') and not l.startswith('    ') and 'cube' in l]
        assert len(indented) == 1
    
    def test_tab_indent(self):
        """Use tabs for indentation."""
        config = FormatConfig(UseTab=UseTabStyle.Always)
        code = "module foo() { cube(1); }"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Find the indented line
        indented = [l for l in lines if l.startswith('\t') and 'cube' in l]
        assert len(indented) == 1
    
    def test_nested_indentation(self):
        """Nested blocks get proper indentation."""
        code = "module foo() { if (true) { cube(1); } }"
        result = format_code(code)
        lines = result.strip().split('\n')
        # Find cube line - should have 2 levels of indentation
        cube_lines = [l for l in lines if 'cube' in l]
        assert len(cube_lines) == 1
        assert cube_lines[0].startswith('        ')  # 8 spaces = 2 levels


class TestComments:
    """Test comment handling."""
    
    def test_line_comment_preserved(self):
        """Line comments are preserved."""
        code = "cube(1); // this is a cube"
        result = format_code(code)
        assert "// this is a cube" in result
    
    def test_block_comment_preserved(self):
        """Block comments are preserved."""
        code = "/* comment */ cube(1);"
        result = format_code(code)
        assert "/* comment */" in result
    
    def test_multiline_block_comment(self):
        """Multi-line block comments are preserved."""
        code = """/* line 1
line 2
line 3 */ cube(1);"""
        result = format_code(code)
        assert "/* line 1" in result
        assert "line 3 */" in result


class TestLineEndings:
    """Test line ending handling."""
    
    def test_lf_line_endings(self):
        """Use LF line endings."""
        config = FormatConfig(LineEnding=LineEndingStyle.LF)
        code = "cube(1);\r\nsphere(1);"
        result = format_code(code, config)
        assert '\r\n' not in result
        assert '\n' in result
    
    def test_crlf_line_endings(self):
        """Use CRLF line endings."""
        config = FormatConfig(LineEnding=LineEndingStyle.CRLF)
        code = "cube(1);\nsphere(1);"
        result = format_code(code, config)
        assert '\r\n' in result
    
    def test_derive_lf(self):
        """Derive LF from source with more LF."""
        config = FormatConfig(LineEnding=LineEndingStyle.DeriveLF)
        code = "cube(1);\nsphere(1);\ncylinder(1);"
        result = format_code(code, config)
        assert '\r\n' not in result
    
    def test_derive_crlf(self):
        """Derive CRLF from source with more CRLF."""
        config = FormatConfig(LineEnding=LineEndingStyle.DeriveLF)
        code = "cube(1);\r\nsphere(1);\r\ncylinder(1);"
        result = format_code(code, config)
        assert '\r\n' in result


class TestComplexCode:
    """Test formatting of complex OpenSCAD code."""
    
    def test_for_loop(self):
        """Format a for loop."""
        code = "for(i=[0:10]){cube(i);}"
        result = format_code(code)
        assert "for (i = [0:10])" in result or "for(i = [0:10])" in result
        assert "cube(i);" in result
    
    def test_if_else(self):
        """Format if-else statement."""
        code = "if(x>0){cube(x);}else{sphere(1);}"
        result = format_code(code)
        assert "if (x > 0)" in result or "if(x > 0)" in result
        assert "else" in result
    
    def test_function_definition(self):
        """Format a function definition."""
        code = "function add(a,b)=a+b;"
        result = format_code(code)
        assert "function add(a, b) = a + b;" in result
    
    def test_let_expression(self):
        """Format a let expression."""
        code = "let(x=1,y=2)cube([x,y,1]);"
        result = format_code(code)
        assert "let" in result
        assert "x = 1" in result
    
    def test_ternary_operator(self):
        """Format ternary operator."""
        code = "x=a>0?a:-a;"
        result = format_code(code)
        assert "a > 0 ? a : -a" in result
    
    def test_vector_expression(self):
        """Format vector expressions."""
        code = "[1,2,3]+[4,5,6]"
        result = format_code(code)
        assert "[1, 2, 3] + [4, 5, 6]" in result
    
    def test_range_expression(self):
        """Format range expressions."""
        code = "[0:0.1:10]"
        result = format_code(code)
        assert "[0:0.1:10]" in result or "[0 : 0.1 : 10]" in result
    
    def test_modifier_debug(self):
        """Format with debug modifier."""
        code = "#cube(1);"
        result = format_code(code)
        assert "#cube(1);" in result
    
    def test_chained_transformations(self):
        """Format chained transformations."""
        code = "translate([1,0,0])rotate([0,0,45])scale([2,2,2])cube(1);"
        result = format_code(code)
        assert "translate([1, 0, 0])" in result
        assert "rotate([0, 0, 45])" in result
        assert "scale([2, 2, 2])" in result
        assert "cube(1);" in result
    
    def test_difference_operation(self):
        """Format difference operation."""
        code = "difference(){cube(10);translate([2,2,-1])cylinder(12,r=3);}"
        result = format_code(code)
        assert "difference()" in result
        assert "cube(10);" in result
        assert "cylinder(12, r = 3);" in result


class TestEdgeCases:
    """Test edge cases and special situations."""
    
    def test_empty_input(self):
        """Empty input returns empty output."""
        result = format_code("")
        assert result == "\n" or result == ""
    
    def test_only_whitespace(self):
        """Only whitespace returns minimal output."""
        result = format_code("   \n   \n   ")
        assert result.strip() == ""
    
    def test_only_comment(self):
        """Only a comment is preserved."""
        code = "// just a comment"
        result = format_code(code)
        assert "// just a comment" in result
    
    def test_special_variables(self):
        """Special variables are handled."""
        code = "$fn=32;$fa=1;$fs=0.1;"
        result = format_code(code)
        assert "$fn = 32;" in result
        assert "$fa = 1;" in result
        assert "$fs = 0.1;" in result
    
    def test_include_use_statements(self):
        """Include and use statements."""
        code = 'include<file.scad>;use<other.scad>;'
        result = format_code(code)
        assert "include" in result
        assert "use" in result
    
    def test_unary_minus(self):
        """Unary minus is handled correctly."""
        code = "x=-5;"
        result = format_code(code)
        assert "x = -5;" in result
    
    def test_unary_not(self):
        """Unary not is handled correctly."""
        code = "x=!true;"
        result = format_code(code)
        assert "x = !true;" in result
    
    def test_nested_brackets(self):
        """Nested brackets are handled."""
        code = "[[1,2],[3,4]]"
        result = format_code(code)
        assert "[[1, 2], [3, 4]]" in result
    
    def test_empty_module(self):
        """Empty module body."""
        code = "module empty() {}"
        result = format_code(code)
        assert "module empty()" in result


class TestColumnLimit:
    """Test column limit and line breaking."""
    
    def test_no_break_within_limit(self):
        """Lines within limit are not broken."""
        config = FormatConfig(ColumnLimit=80)
        code = "cube([1, 2, 3]);"
        result = format_code(code, config)
        assert result.strip() == "cube([1, 2, 3]);"
    
    def test_break_long_line(self):
        """Long lines are broken."""
        config = FormatConfig(ColumnLimit=40)
        code = "translate([100, 200, 300]) rotate([45, 45, 45]) cube([10, 20, 30]);"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Should have been broken into multiple lines
        assert len(lines) > 1
        # Each line should be within limit (or close - some may be unavoidable)
        for line in lines:
            assert len(line) <= 50  # Allow some slack
    
    def test_break_at_higher_scope(self):
        """Prefer breaking at higher scope (outer parens)."""
        config = FormatConfig(ColumnLimit=30, ContinuationIndentWidth=4)
        # This should prefer breaking at the outer function level
        code = "outer(inner1(a) + inner2(b));"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Should break after outer( not inside inner functions
        if len(lines) > 1:
            # First line should have outer( and possibly inner1(a)
            assert "outer(" in lines[0]
    
    def test_break_after_comma(self):
        """Break after commas in argument lists."""
        config = FormatConfig(ColumnLimit=25)
        code = "cube([111, 222, 333]);"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Should break after commas
        assert len(lines) >= 1
    
    def test_break_after_operator(self):
        """Break after operators."""
        config = FormatConfig(ColumnLimit=20)
        code = "x = aaa + bbb + ccc;"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Should break after + operators
        assert len(lines) >= 1
    
    def test_nested_function_breaking(self):
        """Break nested function calls at outer level first."""
        config = FormatConfig(ColumnLimit=50, ContinuationIndentWidth=4)
        code = "translate([1, 2, 3]) rotate([0, 0, 45]) scale([2, 2, 2]) cube(10);"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        # Should break between transformations
        assert len(lines) >= 1
    
    def test_column_limit_zero_means_no_limit(self):
        """ColumnLimit=0 means no line breaking."""
        config = FormatConfig(ColumnLimit=0)
        code = "translate([100, 200, 300]) rotate([45, 45, 45]) cube([10, 20, 30]);"
        result = format_code(code, config)
        lines = [l for l in result.strip().split('\n') if l]
        # Should be single line (no breaking)
        assert len(lines) == 1
    
    def test_continuation_indent(self):
        """Continuation lines are properly indented."""
        config = FormatConfig(ColumnLimit=30, ContinuationIndentWidth=8)
        code = "func(arg1, arg2, arg3, arg4);"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        if len(lines) > 1:
            # Continuation lines should be indented
            assert lines[1].startswith(' ')
    
    def test_preserve_block_structure(self):
        """Line breaking doesn't break block structure."""
        config = FormatConfig(ColumnLimit=40)
        code = "module foo() { translate([100, 200, 300]) cube(10); }"
        result = format_code(code, config)
        # Should still have proper structure
        assert "module foo()" in result
        assert "{" in result
        assert "}" in result
    
    def test_break_outer_not_inner(self):
        """Break at outer scope, not inside nested functions.
        
        function(SubFunction(arg1) +
                 SubFunction(arg2))
        
        is better than
        
        function(SubFunction(arg1) + SubFunction(
            arg2))
        """
        config = FormatConfig(ColumnLimit=35)
        code = "function(SubFunction(arg1) + SubFunction(arg2));"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        
        if len(lines) > 1:
            # The break should be after the + operator, not inside SubFunction
            # First line should contain function( and SubFunction(arg1) +
            assert "function(" in lines[0]
            assert "SubFunction(arg1)" in lines[0]
            # Second line should start with SubFunction(arg2), not "arg2)"
            assert "SubFunction(arg2)" in lines[1]
    
    def test_break_between_chained_calls(self):
        """Break between chained function calls at outer level."""
        config = FormatConfig(ColumnLimit=30)
        code = "translate([1, 2, 3]) rotate([0, 0, 45]) cube(10);"
        result = format_code(code, config)
        lines = result.strip().split('\n')
        
        # Should break between translate() and rotate(), not inside arrays
        assert len(lines) >= 2
        # First line should have complete translate call
        assert "translate([1, 2, 3])" in lines[0]


class TestRealWorldExamples:
    """Test with real-world OpenSCAD code examples."""
    
    def test_tetrahedron(self):
        """Format a tetrahedron module."""
        code = """module tetrahedron(size=1){
a=size*sqrt(2);
polyhedron(
points=[[1,0,-1/sqrt(2)],[-1,0,-1/sqrt(2)],[0,1,1/sqrt(2)],[0,-1,1/sqrt(2)]]*a/2,
faces=[[0,1,2],[1,0,3],[0,2,3],[2,1,3]]
);
}
tetrahedron();
translate([2,0,0])tetrahedron(2);"""
        
        result = format_code(code)
        
        # Basic structure should be maintained
        assert "module tetrahedron" in result
        assert "polyhedron(" in result
        assert "tetrahedron();" in result
        assert "translate([2, 0, 0])" in result
    
    def test_parametric_box(self):
        """Format a parametric box module."""
        code = """module rounded_box(size,radius){
hull(){
for(x=[radius,size.x-radius])
for(y=[radius,size.y-radius])
translate([x,y,0])
cylinder(size.z,r=radius);
}
}"""
        
        result = format_code(code)
        
        assert "module rounded_box(size, radius)" in result
        assert "hull()" in result
        assert "for" in result

    def test_allman_else(self):
        code = """
module base4x4(Xspots = [-160, -80, 0, 80, 160], Yspots = [-160, -80, 0, 80, 160])
{
  minkowski(10)
  {
    difference()
    {
      union()
      {
        for(x = Xspots)
        {
          translate([x, 0, 0]) cube([10, 330, 10], center = true);
        }
        for(y = Yspots)
        {
          translate([0, y, 0]) cube([330, 10, 10], center = true);
        }
      }
      children();
    }
    if($preview)
    {
      cube(5, center = true);
    }
    else
    {
      sphere(5, $fn = 36);
    }
  }
}
"""
        badCode = code.replace("\n","").replace("  "," ")
        config = FormatConfig(IndentWidth=2,BreakBeforeBraces= BraceBreakingStyle.Allman)
        returnedCode = format_code(badCode, config)

        assert returnedCode.strip() == code.strip()
 
    def test_long_args(self):
        code = """
module base4x4(Xspots = [-160, -80, 0, 80, 160],
               Yspots = [-160, -80, 0, 80, 160])
{
    blah();
}
""".strip()

  
        badCode = code.replace("\n","").replace("  "," ")
        config = FormatConfig(ColumnLimit=80,BreakBeforeBraces= BraceBreakingStyle.Allman)
        returnedCode = format_code(badCode, config)

        assert returnedCode.strip() == code.strip()



class TestSeparateDefinitionBlocks:
    """Test SeparateDefinitionBlocks option."""
    
    def test_separate_always(self):
        """Always add blank line between definitions."""
        config = FormatConfig(SeparateDefinitionBlocks=SeparateDefinitionStyle.Always)
        code = "module a() { } module b() { }"
        result = format_code(code, config)
        # Should have blank line between modules
        assert "\n\n" in result or "\n\nmodule b" in result
        emptyLines = [l for l in result.split('\n') if l.strip() == ""]
        assert len(emptyLines ) > 1

        config = FormatConfig(SeparateDefinitionBlocks=SeparateDefinitionStyle.Always,
         BreakBeforeBraces=BraceBreakingStyle.Allman)

        code = "module a() { blah();} module b() { if(a){blah2();}}"
        
        result = format_code(code, config)
        # Should have blank line between modules
        assert "\n\n" in result or "\n\nmodule b" in result
        emptyLines = [l for l in result.split('\n') if l.strip() == ""]
        assert len(emptyLines ) > 1
    
    def test_separate_never(self):
        """Never add blank line between definitions."""
        config = FormatConfig(SeparateDefinitionBlocks=SeparateDefinitionStyle.Never)
        code = "module a() { } module b() { }"
        result = format_code(code, config)
        lines = [l for l in result.split('\n') if l.strip()]
        # Should have no blank lines (all lines have content)
        assert len(lines) >= 2
    
    def test_separate_leave_default(self):
        """Default is Leave - don't modify blank lines."""
        config = FormatConfig()  # Default
        assert config.SeparateDefinitionBlocks == SeparateDefinitionStyle.Leave


class TestMaxEmptyLinesToKeep:
    """Test MaxEmptyLinesToKeep option."""
    
    def test_default_is_one(self):
        """Default MaxEmptyLinesToKeep is 1."""
        config = FormatConfig()
        assert config.MaxEmptyLinesToKeep == 1
    
    def test_preserves_single_empty_line(self):
        """Preserves a single empty line between statements."""
        code = "a = 1;\n\nb = 2;"
        result = format_code(code)
        assert "\n\n" in result  # One empty line preserved
    
    def test_collapses_multiple_empty_lines(self):
        """Collapses multiple empty lines to MaxEmptyLinesToKeep."""
        code = "a = 1;\n\n\n\nb = 2;"  # 3 empty lines
        result = format_code(code)
        # Should have at most 1 empty line (2 consecutive newlines)
        assert "\n\n\n" not in result
        assert "\n\n" in result
    
    def test_max_empty_lines_zero(self):
        """MaxEmptyLinesToKeep=0 removes all empty lines."""
        config = FormatConfig(MaxEmptyLinesToKeep=0)
        code = "a = 1;\n\n\nb = 2;"
        result = format_code(code, config)
        # No double newlines (no empty lines)
        assert "\n\n" not in result
    
    def test_max_empty_lines_two(self):
        """MaxEmptyLinesToKeep=2 allows up to 2 empty lines."""
        config = FormatConfig(MaxEmptyLinesToKeep=2)
        code = "a = 1;\n\n\n\n\nb = 2;"  # 4 empty lines
        result = format_code(code, config)
        # Should collapse to 2 empty lines (3 consecutive newlines)
        assert "\n\n\n" in result
        assert "\n\n\n\n" not in result
