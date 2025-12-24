"""
Tests for pandas +: operator (smart_append) - append dict/list/DataFrame/Series to DataFrame
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from pandas_ops import smart_append, dollar_pandas
from runtime_ops import __opkit_vstack__, __opkit_dollar__
import builtins


class TestPandasAppendDict:
    """Test +: operator with dict (must use $ operator)"""
    
    def test_append_dict_with_dollar_basic(self):
        """Test df +: {'a': 5, 'b': 6}$"""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        dict_as_df = __opkit_dollar__({'a': 5, 'b': 6})
        result = __opkit_vstack__(df, dict_as_df)
        expected = pd.DataFrame({'a': [1, 2, 5], 'b': [3, 4, 6]})
        assert result.equals(expected)
    
    def test_append_dict_without_dollar_raises_error(self):
        """Test that dict without $ raises TypeError"""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        with pytest.raises(TypeError, match="Cannot use dict directly"):
            __opkit_vstack__(df, {'a': 3, 'b': 4})
    
    def test_append_dict_dollar_single_row_df(self):
        """Test appending to single-row DataFrame using $"""
        df = pd.DataFrame({'name': ['Alice'], 'age': [25]})
        dict_as_df = __opkit_dollar__({'name': 'Bob', 'age': 30})
        result = __opkit_vstack__(df, dict_as_df)
        expected = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})
        assert result.equals(expected)


class TestPandasAppendList:
    """Test +: operator with list (must use $ operator)"""
    
    def test_append_list_with_dollar_basic(self):
        """Test df +: [5, 6]$"""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        list_as_array = __opkit_dollar__([5, 6])
        result = __opkit_vstack__(df, list_as_array)
        expected = pd.DataFrame({'a': [1, 2, 5], 'b': [3, 4, 6]})
        assert result.equals(expected)
    
    def test_append_list_without_dollar_raises_error(self):
        """Test that list without $ raises TypeError"""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        with pytest.raises(TypeError, match="Cannot use list directly"):
            __opkit_vstack__(df, [3, 4])
    
    def test_append_tuple_without_dollar_raises_error(self):
        """Test that tuple without $ raises TypeError"""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        with pytest.raises(TypeError, match="Cannot use tuple directly"):
            __opkit_vstack__(df, (3, 4))


class TestPandasAppendDataFrame:
    """Test +: operator with DataFrame"""
    
    def test_append_dataframe_basic(self):
        """Test df +: other_df"""
        df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        df2 = pd.DataFrame({'a': [5, 6], 'b': [7, 8]})
        result = __opkit_vstack__(df1, df2)
        expected = pd.DataFrame({'a': [1, 2, 5, 6], 'b': [3, 4, 7, 8]})
        assert result.equals(expected)
    
    def test_append_single_row_dataframe(self):
        """Test appending single-row DataFrame"""
        df1 = pd.DataFrame({'x': [1], 'y': [2]})
        df2 = pd.DataFrame({'x': [3], 'y': [4]})
        result = __opkit_vstack__(df1, df2)
        expected = pd.DataFrame({'x': [1, 3], 'y': [2, 4]})
        assert result.equals(expected)
    
    def test_append_empty_dataframe(self):
        """Test appending empty DataFrame"""
        df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        df2 = pd.DataFrame(columns=['a', 'b'])
        result = __opkit_vstack__(df1, df2)
        assert result.shape == (2, 2)
        # Check values match even though indices are reset
        assert result['a'].tolist() == [1, 2]
        assert result['b'].tolist() == [3, 4]
    
    def test_append_resets_index(self):
        """Test that result has reset index"""
        df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4]}, index=[5, 6])
        df2 = pd.DataFrame({'a': [7, 8], 'b': [9, 10]}, index=[10, 11])
        result = __opkit_vstack__(df1, df2)
        # Index should be reset to 0, 1, 2, 3
        assert list(result.index) == [0, 1, 2, 3]


class TestPandasAppendSeries:
    """Test +: operator with Series (no longer supported directly)"""
    
    def test_append_series_raises_error(self):
        """Test that pd.Series without conversion raises TypeError"""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        series = pd.Series({'a': 5, 'b': 6})
        with pytest.raises(TypeError, match="Cannot use pd.Series directly"):
            __opkit_vstack__(df, series)


class TestPandasChaining:
    """Test chaining multiple +: operations (with $ operator)"""
    
    def test_chain_dict_and_list_with_dollar(self):
        """Test df +: dict$ +: list$"""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        result = __opkit_vstack__(df, __opkit_dollar__({'a': 3, 'b': 4}))
        result = __opkit_vstack__(result, __opkit_dollar__([5, 6]))
        expected = pd.DataFrame({'a': [1, 3, 5], 'b': [2, 4, 6]})
        assert result.equals(expected)
    
    def test_chain_multiple_dicts_with_dollar(self):
        """Test df +: dict$ +: dict$ +: dict$"""
        df = pd.DataFrame({'name': ['Alice'], 'age': [25]})
        result = __opkit_vstack__(df, __opkit_dollar__({'name': 'Bob', 'age': 30}))
        result = __opkit_vstack__(result, __opkit_dollar__({'name': 'Charlie', 'age': 35}))
        result = __opkit_vstack__(result, __opkit_dollar__({'name': 'Diana', 'age': 28}))
        assert result.shape == (4, 2)
        assert list(result['name']) == ['Alice', 'Bob', 'Charlie', 'Diana']
        assert list(result['age']) == [25, 30, 35, 28]


class TestPandasAppendNumpyArray:
    """Test +: operator with numpy arrays (new requirement)"""
    
    def test_append_1d_array_basic(self):
        """Test df +: np.array([5, 6])"""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        arr = np.array([5, 6])
        result = __opkit_vstack__(df, arr)
        expected = pd.DataFrame({'a': [1, 2, 5], 'b': [3, 4, 6]})
        assert result.equals(expected)
    
    def test_append_1d_array_wrong_length(self):
        """Test that wrong-length 1D array raises ValueError"""
        df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3]})
        arr = np.array([4, 5])  # Only 2 values for 3 columns
        with pytest.raises(ValueError, match="1-D array length .* must match DataFrame column count"):
            __opkit_vstack__(df, arr)
    
    def test_append_2d_array_basic(self):
        """Test df +: np.array([[5, 6], [7, 8]]) - 2D array"""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        arr = np.array([[5, 6], [7, 8]])
        result = __opkit_vstack__(df, arr)
        expected = pd.DataFrame({'a': [1, 2, 5, 7], 'b': [3, 4, 6, 8]})
        assert result.equals(expected)
    
    def test_append_2d_array_wrong_width(self):
        """Test that wrong-width 2D array raises ValueError"""
        df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3]})
        arr = np.array([[4, 5]])  # Only 2 columns for 3 DataFrame columns
        with pytest.raises(ValueError, match="2-D array width .* must match DataFrame column count"):
            __opkit_vstack__(df, arr)
    
    def test_append_3d_array_raises_error(self):
        """Test that 3D array raises ValueError"""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        arr = np.array([[[1, 2]]])
        with pytest.raises(ValueError, match="Only 1-D or 2-D numpy arrays are accepted"):
            __opkit_vstack__(df, arr)


class TestRuntimeDispatcher:
    """Test the runtime dispatcher for +: operator"""
    
    def test_dispatcher_with_dataframe(self):
        """Test that dispatcher correctly routes DataFrame operations"""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        df_to_append = __opkit_dollar__({'a': 3, 'b': 4})
        result = __opkit_vstack__(df, df_to_append)
        expected = pd.DataFrame({'a': [1, 3], 'b': [2, 4]})
        assert result.equals(expected)
    
    def test_dispatcher_with_numpy(self):
        """Test that dispatcher correctly routes numpy operations with 2D arrays"""
        a = np.array([[1, 2]])
        b = np.array([[3, 4]])
        result = __opkit_vstack__(a, b)
        expected = np.array([[1, 2], [3, 4]])
        assert np.array_equal(result, expected)
    
    def test_dispatcher_with_invalid_type(self):
        """Test that dispatcher raises error for invalid types"""
        with pytest.raises(TypeError, match=r"\+: operator not supported"):
            __opkit_vstack__("invalid", [1, 2])


class TestPandasErrorHandling:
    """Test error handling in pandas operators"""
    
    def test_invalid_type_raises_error(self):
        """Test that invalid types raise TypeError"""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        with pytest.raises(TypeError, match="DataFrame \\+: operator requires"):
            __opkit_vstack__(df, "invalid")
        
        with pytest.raises(TypeError, match="DataFrame \\+: operator requires"):
            __opkit_vstack__(df, 123)
