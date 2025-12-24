"""
Tests for unary $ operator - converts lists/tuples to numpy arrays and dicts to DataFrames
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from runtime_ops import __opkit_dollar__
from numpy_ops import dollar_numpy
from pandas_ops import dollar_pandas


class TestDollarOperator:
    """Test the unary $ operator"""
    
    def test_list_to_numpy(self):
        """Test [1, 2, 3]$ → np.array([1, 2, 3])"""
        result = __opkit_dollar__([1, 2, 3])
        expected = np.array([1, 2, 3])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_tuple_to_numpy(self):
        """Test (1, 2, 3)$ → np.array((1, 2, 3))"""
        result = __opkit_dollar__((1, 2, 3))
        expected = np.array((1, 2, 3))
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_dict_to_dataframe(self):
        """Test {'a': 1, 'b': 2}$ → pd.DataFrame({'a': [1], 'b': [2]})"""
        result = __opkit_dollar__({'a': 1, 'b': 2})
        expected = pd.DataFrame({'a': [1], 'b': [2]})
        assert isinstance(result, pd.DataFrame)
        assert result.equals(expected)
    
    def test_nested_list_to_numpy(self):
        """Test nested list conversion"""
        result = __opkit_dollar__([[1, 2], [3, 4]])
        expected = np.array([[1, 2], [3, 4]])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_empty_list_to_numpy(self):
        """Test empty list conversion"""
        result = __opkit_dollar__([])
        expected = np.array([])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
    
    def test_dict_with_lists_to_dataframe(self):
        """Test dict with list values → DataFrame"""
        result = __opkit_dollar__({'a': [1, 2], 'b': [3, 4]})
        expected = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        assert isinstance(result, pd.DataFrame)
        assert result.equals(expected)
    
    def test_invalid_type_raises_error(self):
        """Test that invalid types raise TypeError"""
        with pytest.raises(TypeError):
            __opkit_dollar__(123)
        
        with pytest.raises(TypeError):
            __opkit_dollar__("string")
        
        with pytest.raises(TypeError):
            __opkit_dollar__(None)


class TestDollarNumpy:
    """Test dollar_numpy function directly"""
    
    def test_list_conversion(self):
        """Test list to numpy array"""
        result = dollar_numpy([1, 2, 3])
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, np.array([1, 2, 3]))
    
    def test_tuple_conversion(self):
        """Test tuple to numpy array"""
        result = dollar_numpy((4, 5, 6))
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, np.array((4, 5, 6)))
    
    def test_invalid_type(self):
        """Test that invalid types raise TypeError"""
        with pytest.raises(TypeError):
            dollar_numpy({'a': 1})


class TestDollarPandas:
    """Test dollar_pandas function directly"""
    
    def test_dict_conversion(self):
        """Test dict to DataFrame"""
        result = dollar_pandas({'a': 1, 'b': 2})
        expected = pd.DataFrame({'a': [1], 'b': [2]})
        assert isinstance(result, pd.DataFrame)
        assert result.equals(expected)
    
    def test_dict_with_lists(self):
        """Test dict with list values"""
        result = dollar_pandas({'x': [1, 2, 3], 'y': [4, 5, 6]})
        expected = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
        assert isinstance(result, pd.DataFrame)
        assert result.equals(expected)
    
    def test_invalid_type(self):
        """Test that invalid types raise TypeError"""
        with pytest.raises(TypeError):
            dollar_pandas([1, 2, 3])
