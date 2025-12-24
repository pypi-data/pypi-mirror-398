"""
Tests for numpy binary operators: +.. (hstack), +: (vstack), +. (dstack)
Updated for new concatenation semantics (no longer stacking).
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
    
    def test_basic_hconcat(self):
        """Test hstack with 2D arrays - no longer works with 1D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = hconcat(a, b)
        expected = np.array([[1, 2, 3, 4]])
        assert np.array_equal(result, expected)
    
    def test_hstack_2d_arrays_vertical(self):
        """Test hstack with 2D arrays (vertical orientation)"""
        a = np.array([[1], [2]])
        b = np.array([[3], [4]])
        result = hconcat(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
    
    def test_hstack_rejects_1d_arrays(self):
        """Test that hstack rejects two 1D arrays"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        with pytest.raises(ValueError, match="Cannot use \\+\\.\\. on two 1D arrays"):
            hconcat(a, b)
    
    def test_hstack_1d_with_2d(self):
        """Test hstack with 1D and 2D array"""
        a = np.array([1, 2])
        b = np.array([[3], [4]])
        result = hconcat(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)
    
    def test_hstack_via_builtin(self):
        """Test hstack via builtins registration"""
        a = np.array([[1], [2]])
        b = np.array([[3], [4]])
        result = builtins.__opkit_hstack__(a, b)
        expected = np.array([[1, 3], [2, 4]])
        assert np.array_equal(result, expected)


class TestVconcatOperator:
    """Test the +: operator for numpy (vertical concatenation along axis 0)"""
    
    def test_basic_vconcat(self):
        """Test vstack with 2D arrays - no longer works with 1D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = vconcat(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
    
    def test_vstack_same_size(self):
        """Test vstack with same sized 2D arrays"""
        a = np.array([[1, 2, 3]])
        b = np.array([[4, 5, 6]])
        result = vconcat(a, b)
        expected = np.array([[1, 2, 3], [4, 5, 6]])
        assert np.array_equal(result, expected)
    
    def test_vstack_2d_arrays(self):
        """Test vstack with 2D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = vconcat(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
    
    def test_vstack_multiple_rows(self):
        """Test vstack with multiple rows"""
        a = np.array([[1, 2], [3, 4]])
        b = np.array([[5, 6]])
        result = vconcat(a, b)
        expected = np.array([[1, 2], [3, 4], [5, 6]])
        assert np.array_equal(result, expected)
    
    def test_vstack_rejects_1d_arrays(self):
        """Test that vstack rejects two 1D arrays"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        with pytest.raises(ValueError, match="Cannot use \\+: on two 1D arrays"):
            vconcat(a, b)
    
    def test_vstack_via_runtime(self):
        """Test vstack via runtime dispatcher with 2D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = __opkit_vstack__(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)


class TestLastdimconcatOperator:
    """Test the +. operator (concatenation along last axis)"""
    
    def test_basic_lastdimconcat(self):
        """Test +. with 1D arrays (now concatenates, not stacks)"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = lastdimconcat(a, b)
        expected = np.array([1, 2, 3, 4])
        assert np.array_equal(result, expected)
    
    def test_dstack_shape(self):
        """Test that dstack produces correct shape for 1D arrays"""
        a = np.array([1, 2, 3])
        b = np.array([4, 5, 6])
        result = lastdimconcat(a, b)
        # Concatenation along last axis for 1D arrays gives 1D result
        assert result.shape == (6,)
    
    def test_dstack_2d_arrays(self):
        """Test dstack with 2D arrays (concatenates along last axis)"""
        a = np.array([[1, 2], [3, 4]])
        b = np.array([[5, 6], [7, 8]])
        result = lastdimconcat(a, b)
        expected = np.array([[1, 2, 5, 6], [3, 4, 7, 8]])
        assert np.array_equal(result, expected)
        # Shape should be (2, 4) not (2, 2, 2)
        assert result.shape == (2, 4)
    
    def test_dstack_values(self):
        """Test dstack produces correct values for 1D arrays"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = lastdimconcat(a, b)
        # Check specific values - result is 1D concatenation
        assert result[0] == 1
        assert result[1] == 2
        assert result[2] == 3
        assert result[3] == 4
    
    def test_dstack_via_builtin(self):
        """Test dstack via builtins registration"""
        a = np.array([1, 2])
        b = np.array([3, 4])
        result = builtins.__opkit_dstack__(a, b)
        expected = np.array([1, 2, 3, 4])
        assert np.array_equal(result, expected)
