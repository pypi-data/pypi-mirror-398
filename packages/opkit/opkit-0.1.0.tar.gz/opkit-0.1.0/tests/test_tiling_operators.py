"""
Tests for tiling operators: *: (tile_vconcat), *.. (tile_hconcat), *. (tile_lastdimconcat), *:. (tile_2d)
These operators repeat/tile arrays without adding dimensions.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from numpy_ops import tile_vconcat, tile_hconcat, tile_lastdimconcat, tile_2d
import builtins


class TestTileVconcatOperator:
    """Test the *: operator (tile vertically)"""
    
    def test_tile_vconcat_2d_array(self):
        """Test *: with a 2D array"""
        a = np.array([[1, 2]])
        result = tile_vconcat(a, 3)
        expected = np.array([[1, 2], [1, 2], [1, 2]])
        assert np.array_equal(result, expected)
    
    def test_tile_vconcat_via_builtin(self):
        """Test *: via builtins registration"""
        a = np.array([[1, 2]])
        result = builtins.__opkit_tile_vconcat__(a, 2)
        expected = np.array([[1, 2], [1, 2]])
        assert np.array_equal(result, expected)
    
    def test_tile_vconcat_invalid_count(self):
        """Test *: with invalid count"""
        a = np.array([[1, 2]])
        with pytest.raises(ValueError, match="positive integer"):
            tile_vconcat(a, 0)
        with pytest.raises(ValueError, match="positive integer"):
            tile_vconcat(a, -1)
    
    def test_tile_vconcat_rejects_1d(self):
        """Test *: rejects 1D arrays"""
        a = np.array([1, 2])
        with pytest.raises(ValueError, match="no preset orientation"):
            tile_vconcat(a, 3)


class TestTileHconcatOperator:
    """Test the *.. operator (tile horizontally)"""
    
    def test_tile_hconcat_2d_array(self):
        """Test *.. with a 2D array"""
        a = np.array([[1], [2]])
        result = tile_hconcat(a, 3)
        expected = np.array([[1, 1, 1], [2, 2, 2]])
        assert np.array_equal(result, expected)
    
    def test_tile_hconcat_via_builtin(self):
        """Test *.. via builtins registration"""
        a = np.array([[1], [2]])
        result = builtins.__opkit_tile_hconcat__(a, 2)
        expected = np.array([[1, 1], [2, 2]])
        assert np.array_equal(result, expected)
    
    def test_tile_hconcat_invalid_count(self):
        """Test *.. with invalid count"""
        a = np.array([[1], [2]])
        with pytest.raises(ValueError, match="positive integer"):
            tile_hconcat(a, 0)
    
    def test_tile_hconcat_rejects_1d(self):
        """Test *.. rejects 1D arrays"""
        a = np.array([1, 2])
        with pytest.raises(ValueError, match="no preset orientation"):
            tile_hconcat(a, 3)


class TestTileLastdimconcatOperator:
    """Test the *. operator (tile along last dimension)"""
    
    def test_tile_lastdimconcat_1d_array(self):
        """Test *. with a 1D array"""
        a = np.array([1, 2, 3])
        result = tile_lastdimconcat(a, 2)
        expected = np.array([1, 2, 3, 1, 2, 3])
        assert np.array_equal(result, expected)
    
    def test_tile_lastdimconcat_2d_array(self):
        """Test *. with a 2D array"""
        a = np.array([[1, 2], [3, 4]])
        result = tile_lastdimconcat(a, 2)
        expected = np.array([[1, 2, 1, 2], [3, 4, 3, 4]])
        assert np.array_equal(result, expected)
    
    def test_tile_lastdimconcat_via_builtin(self):
        """Test *. via builtins registration"""
        a = np.array([1, 2, 3])
        result = builtins.__opkit_tile_lastdimconcat__(a, 2)
        expected = np.array([1, 2, 3, 1, 2, 3])
        assert np.array_equal(result, expected)
    
    def test_tile_lastdimconcat_invalid_count(self):
        """Test *. with invalid count"""
        a = np.array([1, 2, 3])
        with pytest.raises(ValueError, match="positive integer"):
            tile_lastdimconcat(a, 0)


class TestTile2dOperator:
    """Test the *:. operator (tile in 2D)"""
    
    def test_tile_2d(self):
        """Test *:. with a 2D array"""
        a = np.array([[1, 2]])
        result = tile_2d(a, (3, 2))
        expected = np.array([[1, 2, 1, 2], [1, 2, 1, 2], [1, 2, 1, 2]])
        assert np.array_equal(result, expected)
    
    def test_tile_2d_via_builtin(self):
        """Test *:. via builtins registration"""
        a = np.array([[1, 2]])
        result = builtins.__opkit_tile_2d__(a, (2, 3))
        expected = np.array([[1, 2, 1, 2, 1, 2], [1, 2, 1, 2, 1, 2]])
        assert np.array_equal(result, expected)
    
    def test_tile_2d_rejects_1d(self):
        """Test *:. rejects 1D arrays"""
        a = np.array([1, 2])
        with pytest.raises(ValueError, match="no preset orientation"):
            tile_2d(a, (3, 2))
    
    def test_tile_2d_invalid_reps(self):
        """Test *:. with invalid reps"""
        a = np.array([[1, 2]])
        with pytest.raises(ValueError, match="tuple of two integers"):
            tile_2d(a, 3)
        with pytest.raises(ValueError, match="positive integers"):
            tile_2d(a, (0, 3))
