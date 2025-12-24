"""
Tests for concatenation operators: +.. (hconcat), +: (vconcat), +. (lastdimconcat)
These operators concatenate arrays without adding dimensions.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from numpy_ops import hconcat, vconcat, lastdimconcat
from runtime_ops import __opkit_vstack__
import builtins


class TestHconcatOperator:
    """Test the +.. operator (horizontal concatenation along axis 1)"""
    
    def test_hconcat_rejects_two_1d_arrays(self):
        """Test that +.. rejects two 1D arrays"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        with pytest.raises(ValueError, match="Cannot use \\+\\.\\. on two 1D arrays"):
            hconcat(a, b)
    
    def test_hconcat_1d_with_2d(self):
        """Test +.. with one 1D and one 2D array"""
        a = np.array([1, 2])  # 1D
        b = np.array([[3], [4]])  # 2D
        result = hconcat(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
    
    def test_hconcat_2d_with_1d(self):
        """Test +.. with one 2D and one 1D array"""
        a = np.array([[1], [2]])  # 2D
        b = np.array([3, 4])  # 1D
        result = hconcat(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
    
    def test_hconcat_2d_arrays(self):
        """Test +.. with two 2D arrays"""
        a = np.array([[1], [2]])
        b = np.array([[3], [4]])
        result = hconcat(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
    
    def test_hconcat_via_builtin(self):
        """Test +.. via builtins registration"""
        a = np.array([[1], [2]])
        b = np.array([[3], [4]])
        result = builtins.__opkit_hconcat__(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)


class TestVconcatOperator:
    """Test the +: operator (vertical concatenation along axis 0)"""
    
    def test_vconcat_rejects_two_1d_arrays(self):
        """Test that +: rejects two 1D arrays"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        with pytest.raises(ValueError, match="Cannot use \\+: on two 1D arrays"):
            vconcat(a, b)
    
    def test_vconcat_1d_with_2d(self):
        """Test +: with one 1D and one 2D array"""
        a = np.array([1, 2])  # 1D
        b = np.array([[3, 4]])  # 2D
        result = vconcat(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
    
    def test_vconcat_2d_with_1d(self):
        """Test +: with one 2D and one 1D array"""
        a = np.array([[1, 2]])  # 2D
        b = np.array([3, 4])  # 1D
        result = vconcat(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
    
    def test_vconcat_2d_arrays(self):
        """Test +: with two 2D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = vconcat(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
    
    def test_vconcat_via_runtime(self):
        """Test +: via runtime dispatcher with 2D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = __opkit_vstack__(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)


class TestLastdimconcatOperator:
    """Test the +. operator (concatenation along last axis)"""
    
    def test_lastdimconcat_1d_arrays(self):
        """Test +. with two 1D arrays (now allowed - concatenates along last axis)"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = lastdimconcat(a, b)
        expected = np.array([1, 2, 3, 4])
        assert np.array_equal(result, expected)
    
    def test_lastdimconcat_2d_arrays(self):
        """Test +. with two 2D arrays (concatenates along last axis)"""
        a = np.array([[1], [2]])
        b = np.array([[3], [4]])
        result = lastdimconcat(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
    
    def test_lastdimconcat_via_builtin(self):
        """Test +. via builtins registration"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = builtins.__opkit_dstack__(a, b)
        expected = np.array([1, 2, 3, 4])
        assert np.array_equal(result, expected)
