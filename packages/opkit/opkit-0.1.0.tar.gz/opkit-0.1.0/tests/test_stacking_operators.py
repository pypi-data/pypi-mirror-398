"""
Tests for stacking operators: /: (slash_vstack), /.. (slash_hstack), /. (slash_lastdimstack)
These operators add a new dimension to arrays before stacking.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from numpy_ops import slash_vstack, slash_hstack, slash_lastdimstack
import builtins


class TestSlashVstackOperator:
    """Test the /: operator (vertical stacking - adds dimension)"""
    
    def test_slash_vstack_1d_arrays(self):
        """Test /: with two 1D arrays"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = slash_vstack(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
        assert result.shape == (2, 2)
    
    def test_slash_vstack_2d_arrays(self):
        """Test /: with two 2D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = slash_vstack(a, b)
        expected = np.array([[[1, 2]], [[3, 4]]])
        assert np.array_equal(result, expected)
        assert result.shape == (2, 1, 2)
    
    def test_slash_vstack_via_builtin(self):
        """Test /: via builtins registration"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = builtins.__opkit_slash_vstack__(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
    
    def test_slash_vstack_requires_same_shape(self):
        """Test that /: requires operands with same shape"""
        a = np.array([1, 2])
        b = np.array([3, 4, 5])
        with pytest.raises(ValueError):
            slash_vstack(a, b)


class TestSlashHstackOperator:
    """Test the /.. operator (horizontal stacking - adds dimension)"""
    
    def test_slash_hstack_1d_arrays(self):
        """Test /.. with two 1D arrays (same as /. for 1D)"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = slash_hstack(a, b)
        expected = np.array([[1, 3], [2, 4]])  # For 1D arrays, /.. and /. produce same result
        assert np.array_equal(result, expected)
        assert result.shape == (2, 2)
    
    def test_slash_hstack_2d_arrays(self):
        """Test /.. with two 2D arrays"""
        a = np.array([[1], [2]])
        b = np.array([[3], [4]])
        result = slash_hstack(a, b)
        expected = np.array([[[1], [3]], [[2], [4]]])
        assert np.array_equal(result, expected)
        assert result.shape == (2, 2, 1)
    
    def test_slash_hstack_via_builtin(self):
        """Test /.. via builtins registration"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = builtins.__opkit_slash_hstack__(a, b)
        expected = np.array([[1, 3], [2, 4]])  # For 1D arrays, /.. and /. produce same result
        assert np.array_equal(result, expected)


class TestSlashLastdimstackOperator:
    """Test the /. operator (stacking along last dimension)"""
    
    def test_slash_lastdimstack_1d_arrays(self):
        """Test /. with two 1D arrays"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = slash_lastdimstack(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
        assert result.shape == (2, 2)
    
    def test_slash_lastdimstack_2d_arrays(self):
        """Test /. with two 2D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = slash_lastdimstack(a, b)
        expected = np.array([[[1, 3], [2, 4]]])
        assert np.array_equal(result, expected)
        assert result.shape == (1, 2, 2)
    
    def test_slash_lastdimstack_via_builtin(self):
        """Test /. via builtins registration"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = builtins.__opkit_slash_lastdimstack__(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
