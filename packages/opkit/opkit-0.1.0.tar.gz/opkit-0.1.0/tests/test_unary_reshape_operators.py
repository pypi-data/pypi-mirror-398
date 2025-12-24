"""
Tests for unary reshape operators: _ (as_row), | (as_column)
These operators reshape arrays by adding dimensions for row/column orientation.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from numpy_ops import as_row, as_column
import builtins


class TestAsRowOperator:
    """Test the _ operator (reshape as row matrix)"""
    
    def test_as_row_1d_array(self):
        """Test _ with a 1D array (reshape to row matrix)"""
        a = np.array([1, 2, 3])
        result = as_row(a)
        expected = np.array([[1, 2, 3]])
        assert np.array_equal(result, expected)
        assert result.shape == (1, 3)
    
    def test_as_row_2d_array(self):
        """Test _ with a 2D array"""
        a = np.array([[1, 2]])
        result = as_row(a)
        expected = np.array([[[1, 2]]])
        assert np.array_equal(result, expected)
        assert result.shape == (1, 1, 2)
    
    def test_as_row_3d_array(self):
        """Test _ with a 3D array"""
        a = np.array([[[1, 2], [3, 4]]])
        result = as_row(a)
        assert result.shape == (1, 1, 2, 2)
    
    def test_as_row_via_builtin(self):
        """Test _ via builtins registration"""
        a = np.array([1, 2, 3])
        result = builtins.__opkit_as_row__(a)
        expected = np.array([[1, 2, 3]])
        assert np.array_equal(result, expected)


class TestAsColumnOperator:
    """Test the | operator (reshape as column matrix)"""
    
    def test_as_column_1d_array(self):
        """Test | with a 1D array (reshape to column matrix)"""
        a = np.array([1, 2, 3])
        result = as_column(a)
        expected = np.array([[1], [2], [3]])
        assert np.array_equal(result, expected)
        assert result.shape == (3, 1)
    
    def test_as_column_2d_array(self):
        """Test | with a 2D array"""
        a = np.array([[1, 2]])
        result = as_column(a)
        expected = np.array([[[1, 2]]])
        assert np.array_equal(result, expected)
        assert result.shape == (1, 1, 2)
    
    def test_as_column_3d_array(self):
        """Test | with a 3D array"""
        a = np.array([[[1, 2], [3, 4]]])
        result = as_column(a)
        assert result.shape == (1, 1, 2, 2)
    
    def test_as_column_via_builtin(self):
        """Test | via builtins registration"""
        a = np.array([1, 2, 3])
        result = builtins.__opkit_as_column__(a)
        expected = np.array([[1], [2], [3]])
        assert np.array_equal(result, expected)
    
    def test_as_row_and_column_combination(self):
        """Test combining _ and | operators"""
        a = np.array([1, 2, 3])
        # First reshape to row, then to column matrix
        row = as_row(a)  # [[1, 2, 3]] shape (1, 3)
        col = as_column(row)  # [[[1, 2, 3]]] shape (1, 1, 3)
        assert col.shape == (1, 1, 3)
        assert np.array_equal(col[0, 0, :], np.array([1, 2, 3]))
