"""
Integration tests for combined unary-binary operator expressions
Tests real execution of transformed code
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from runtime_ops import __opkit_dollar__, __opkit_vstack__
from numpy_ops import hconcat, vconcat, lastdimconcat
from transform import transform_operators


class TestCombinedOperatorsIntegration:
    """Test that combined unary-binary operators work end-to-end"""
    
    def test_list_dollar_hstack(self):
        """Test [[1], [2]]$ +.. [[3], [4]]$ works correctly for 2D arrays"""
        # Transform the expression - now using 2D arrays
        source = "[[1], [2]]$ +.. [[3], [4]]$"
        transformed = transform_operators(source)
        
        # Execute the transformed code
        result = eval(transformed)
        
        # Verify result
        expected = np.array([[1, 3], [2, 4]])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_list_dollar_vstack(self):
        """Test [[1, 2]]$ +: [[3, 4]]$ works correctly for 2D arrays"""
        source = "[[1, 2]]$ +: [[3, 4]]$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 2], [3, 4]])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_list_dollar_dstack(self):
        """Test [1, 2]$ +. [3, 4]$ works correctly (concatenates for vectors)"""
        source = "[1, 2]$ +. [3, 4]$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        assert isinstance(result, np.ndarray)
        expected = np.array([1, 2, 3, 4])
        assert np.array_equal(result, expected)
        assert result.shape == (4,)
    
    def test_tuple_dollar_hstack(self):
        """Test ((1,), (2,))$ +.. ((3,), (4,))$ works correctly for 2D arrays"""
        source = "((1,), (2,))$ +.. ((3,), (4,))$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 3], [2, 4]])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_chained_hstack(self):
        """Test [[1], [2]]$ +.. [[3], [4]]$ +.. [[5], [6]]$ works correctly"""
        source = "[[1], [2]]$ +.. [[3], [4]]$ +.. [[5], [6]]$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 3, 5], [2, 4, 6]])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_dict_dollar_with_pandas_append(self):
        """Test {'a': 1}$ +: {'a': 2}$ works correctly"""
        source = "{'a': 1}$ +: {'a': 2}$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 1)
        assert list(result['a']) == [1, 2]
    
    def test_readme_example(self):
        """Test an example with vectors using +. for concatenation"""
        # Create arrays using $ operator, then combine with +.
        source = "[1, 2, 3, 4]$ +. [5, 6, 7, 8]$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        assert np.array_equal(result, expected)
    
    def test_stacking_operators(self):
        """Test stacking operators /: and /.  """
        # Test /:
        source = "[1, 2]$ /: [3, 4]$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
        
        # Test /.
        source = "[1, 2]$ /. [3, 4]$"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
    
    def test_tiling_operators(self):
        """Test tiling operators *: and *.  """
        # Test *:
        source = "[[1, 2]]$ *: 3"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 2], [1, 2], [1, 2]])
        assert np.array_equal(result, expected)
        
        # Test *.
        source = "[1, 2, 3]$ *. 2"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([1, 2, 3, 1, 2, 3])  # Changed: np.tile repeats the whole array
        assert np.array_equal(result, expected)
    
    def test_reshape_operators(self):
        """Test reshape operators _ and |"""
        # Test _ (as_row)
        source = "[1, 2, 3]$_"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 2, 3]])
        assert np.array_equal(result, expected)
        assert result.shape == (1, 3)
        
        # Test | (as_column)
        source = "[1, 2, 3]$|"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1], [2], [3]])
        assert np.array_equal(result, expected)
        assert result.shape == (3, 1)
    
    def test_tile_2d_operator(self):
        """Test *:. operator for 2D tiling"""
        source = "[[1, 2]]$ *:. (3, 2)"
        transformed = transform_operators(source)
        result = eval(transformed)
        
        expected = np.array([[1, 2, 1, 2], [1, 2, 1, 2], [1, 2, 1, 2]])
        assert np.array_equal(result, expected)


class TestTransformationAccuracy:
    """Test that transformations are syntactically correct"""
    
    def test_balanced_parentheses(self):
        """Test that transformed expressions have balanced parentheses"""
        test_cases = [
            "[[1], [2]]$ +.. [[3], [4]]$",
            "[[1, 2]]$ +: [[3, 4]]$",
            "[1, 2]$ +. [3, 4]$",
            "[[1]]$ +.. [[2]]$ +.. [[3]]$",
            "[1, 2]$ /: [3, 4]$",
            "[[1, 2]]$ *: 3",
        ]
        
        for source in test_cases:
            transformed = transform_operators(source)
            # Count parentheses
            open_count = transformed.count('(')
            close_count = transformed.count(')')
            assert open_count == close_count, f"Unbalanced parens in: {transformed}"
    
    def test_no_syntax_errors(self):
        """Test that all transformed expressions are valid Python"""
        test_cases = [
            "[[1], [2]]$ +.. [[3], [4]]$",
            "[[1, 2]]$ +: [[3, 4]]$",
            "[1, 2]$ +. [3, 4]$",
            "((1,), (2,))$ +.. ((3,), (4,))$",
            "{'a': 1}$ +: {'a': 2}$",
            "[1, 2]$ /: [3, 4]$",
            "[1, 2]$ /. [3, 4]$",
            "[[1, 2]]$ *: 3",
            "[1, 2, 3]$ *. 2",
        ]
        
        for source in test_cases:
            transformed = transform_operators(source)
            # Try to compile - should not raise SyntaxError
            try:
                compile(transformed, '<string>', 'eval')
            except SyntaxError as e:
                pytest.fail(f"Transformation produced invalid Python: {transformed}\nError: {e}")
