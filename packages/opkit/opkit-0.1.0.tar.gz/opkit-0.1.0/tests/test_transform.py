"""
Tests for AST transformation of custom operators
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from transform import transform_operators


class TestUnaryDollarTransform:
    """Test transformation of unary $ operator"""
    
    def test_list_dollar(self):
        """Test [1, 2, 3]$ transformation"""
        source = "[1, 2, 3]$"
        result = transform_operators(source)
        assert "__opkit_dollar__([1, 2, 3])" in result
    
    def test_tuple_dollar(self):
        """Test (1, 2, 3)$ transformation"""
        source = "(1, 2, 3)$"
        result = transform_operators(source)
        assert "__opkit_dollar__((1, 2, 3))" in result
    
    def test_dict_dollar(self):
        """Test {'a': 1}$ transformation"""
        source = "{'a': 1}$"
        result = transform_operators(source)
        assert "__opkit_dollar__({'a': 1})" in result
    
    def test_nested_list_dollar(self):
        """Test [[1, 2], [3, 4]]$ transformation"""
        source = "[[1, 2], [3, 4]]$"
        result = transform_operators(source)
        assert "__opkit_dollar__([[1, 2], [3, 4]])" in result
    
    def test_empty_list_dollar(self):
        """Test []$ transformation"""
        source = "[]$"
        result = transform_operators(source)
        assert "__opkit_dollar__([])" in result


class TestHstackTransform:
    """Test transformation of +.. operator (hstack)"""
    
    def test_basic_hstack(self):
        """Test a +.. b transformation"""
        source = "a +.. b"
        result = transform_operators(source)
        assert "__opkit_hconcat__" in result
        assert "a" in result and "b" in result
    
    def test_hstack_with_spacing(self):
        """Test a  +..  b with extra spacing"""
        source = "a  +..  b"
        result = transform_operators(source)
        assert "__opkit_hconcat__" in result
    
    def test_hstack_no_spacing(self):
        """Test a+..b without spacing"""
        source = "a+..b"
        result = transform_operators(source)
        assert "__opkit_hconcat__" in result


class TestVstackAppendTransform:
    """Test transformation of +: operator (vstack)"""
    
    def test_basic_vstack_append(self):
        """Test a +: b transformation"""
        source = "a +: b"
        result = transform_operators(source)
        assert "__opkit_vstack__" in result
        assert "a" in result and "b" in result
    
    def test_vstack_with_list(self):
        """Test a +: [1, 2] transformation"""
        source = "a +: [1, 2]"
        result = transform_operators(source)
        assert "__opkit_vstack__" in result
        assert "[1, 2]" in result or "[" in result
    
    def test_vstack_with_dict(self):
        """Test a +: {'x': 1} transformation"""
        source = "a +: {'x': 1}"
        result = transform_operators(source)
        assert "__opkit_vstack__" in result
        assert "{" in result
    
    def test_vstack_with_spacing(self):
        """Test a  +:  b with extra spacing"""
        source = "a  +:  b"
        result = transform_operators(source)
        assert "__opkit_vstack__" in result


class TestDstackTransform:
    """Test transformation of +. operator (dstack)"""
    
    def test_basic_dstack(self):
        """Test a +. b transformation"""
        source = "a +. b"
        result = transform_operators(source)
        assert "__opkit_lastdimconcat__" in result
        assert "a" in result and "b" in result
    
    def test_dstack_with_spacing(self):
        """Test a  +.  b with extra spacing"""
        source = "a  +.  b"
        result = transform_operators(source)
        assert "__opkit_lastdimconcat__" in result


class TestComplexExpressions:
    """Test transformation of complex expressions"""
    
    def test_multiple_operators(self):
        """Test expression with multiple operators"""
        source = "[1, 2]$ +.. [3, 4]$"
        result = transform_operators(source)
        # Should properly handle both $ and +.. operators
        expected = "__opkit_hconcat__(__opkit_dollar__([1, 2]), __opkit_dollar__([3, 4]))"
        assert result == expected
    
    def test_combined_unary_binary_vstack(self):
        """Test [1, 2]$ +: [3, 4]$ (combined unary and binary)"""
        source = "[1, 2]$ +: [3, 4]$"
        result = transform_operators(source)
        expected = "__opkit_vstack__(__opkit_dollar__([1, 2]), __opkit_dollar__([3, 4]))"
        assert result == expected
    
    def test_combined_unary_binary_dstack(self):
        """Test [1, 2]$ +. [3, 4]$ (combined unary and binary)"""
        source = "[1, 2]$ +. [3, 4]$"
        result = transform_operators(source)
        expected = "__opkit_lastdimconcat__(__opkit_dollar__([1, 2]), __opkit_dollar__([3, 4]))"
        assert result == expected
    
    def test_chained_combined_operators(self):
        """Test [1, 2]$ +.. [3, 4]$ +.. [5, 6]$ (chained combined)"""
        source = "[1, 2]$ +.. [3, 4]$ +.. [5, 6]$"
        result = transform_operators(source)
        # Should have nested hstack calls and three dollar calls
        assert result.count("__opkit_dollar__") == 3
        assert result.count("__opkit_hconcat__") == 2
    
    def test_assignment_with_operator(self):
        """Test variable assignment with operators"""
        source = "arr = [1, 2, 3]$"
        result = transform_operators(source)
        assert "arr = " in result
        assert "__opkit_dollar__([1, 2, 3])" in result
    
    def test_multiline_code(self):
        """Test multiline code with operators"""
        source = """a = [1, 2]$
b = [3, 4]$
c = a +.. b"""
        result = transform_operators(source)
        assert result.count("__opkit_dollar__") == 2
        assert "__opkit_hconcat__" in result
    
    def test_function_call_with_operator(self):
        """Test function call with operator result"""
        source = "print([1, 2, 3]$)"
        result = transform_operators(source)
        assert "print" in result
        assert "__opkit_dollar__" in result


class TestEdgeCases:
    """Test edge cases in transformation"""
    
    def test_empty_string(self):
        """Test empty string transformation"""
        source = ""
        result = transform_operators(source)
        assert result == ""
    
    def test_no_operators(self):
        """Test code without custom operators"""
        source = "a = [1, 2, 3]\nb = np.array([4, 5, 6])"
        result = transform_operators(source)
        # Should return unchanged or with minimal changes
        assert "a = " in result
        assert "b = " in result
    
    def test_string_with_dollar_inside(self):
        """Test that $ inside strings is not transformed"""
        source = '"price: $10"'
        result = transform_operators(source)
        # String content should not be transformed
        assert '"price: $10"' in result or "'price: $10'" in result
    
    def test_comment_with_operators(self):
        """Test that operators in comments are not transformed"""
        source = "# This is a comment about [1,2]$ operator"
        result = transform_operators(source)
        # Comments should remain relatively unchanged
        assert "#" in result


class TestRealWorldExamples:
    """Test real-world usage examples from README"""
    
    def test_readme_example_numpy(self):
        """Test the NumPy example from README"""
        source = """a = [1, 2, 3, 4]$
b = [5, 6, 7, 8]$
result = a +.. b"""
        result = transform_operators(source)
        assert result.count("__opkit_dollar__") == 2
        assert "__opkit_hconcat__" in result
    
    def test_readme_example_pandas(self):
        """Test the Pandas example from README"""
        source = """df = {'name': 'Alice', 'age': 25}$
df = df +: {'name': 'Bob', 'age': 30}$"""
        result = transform_operators(source)
        assert "__opkit_dollar__" in result
        assert "__opkit_vstack__" in result
    
    def test_readme_example_chaining(self):
        """Test chaining example from README"""
        source = "df +: {'a': 7}$ +: [8, 9]$ +: another_df"
        result = transform_operators(source)
        # Should have multiple vstack calls
        assert result.count("__opkit_vstack__") >= 2
