"""
Pandas operator implementations
"""

import pandas as pd
from typing import Union, Dict, List
import builtins

def dollar_pandas(expr: Dict) -> pd.DataFrame:
    """
    Unary $ operator for dicts → pandas DataFrames
    
    Examples: 
        {'a': 1, 'b': 2}$ → pd.DataFrame({'a': [1], 'b': [2]})
    """
    if isinstance(expr, dict):
        # Ensure all values are lists
        row_dict = {k: [v] if not isinstance(v, list) else v for k, v in expr.items()}
        return pd.DataFrame(row_dict)
    raise TypeError(f"Cannot convert {type(expr).__name__} to pandas DataFrame with $ operator")


def smart_append(left: pd.DataFrame, right: Union[pd.DataFrame, Dict, List, pd.Series]) -> pd.DataFrame:
    """
    The +: operator for pandas DataFrames - smart append
    
    Handles:
    - DataFrame:  standard concat
    - Dict: convert to single-row DataFrame, then concat
    - List: convert to single-row DataFrame (match columns), then concat
    - Series: append as new row
    
    Examples:
        df +: {'a': 5, 'b': 6}  # Append dict as row
        df +: [7, 8]            # Append list as row
        df +: other_df          # Concat DataFrames
    """
    
    if isinstance(right, pd.DataFrame):
        return pd.concat([left, right], ignore_index=True)
    
    if isinstance(right, pd.Series):
        return pd.concat([left, right.to_frame().T], ignore_index=True)
    
    if isinstance(right, dict):
        # Validate and prepare dict
        missing_cols = set(left.columns) - set(right.keys())
        extra_cols = set(right.keys()) - set(left.columns)
        
        if missing_cols:
            for col in missing_cols:
                right[col] = None
        
        if extra_cols:
            import warnings
            warnings.warn(f"Ignoring extra columns: {extra_cols}")
            right = {k: v for k, v in right.items() if k in left.columns}
        
        # Convert to DataFrame
        row_dict = {k: [v] for k, v in right.items()}
        new_row = pd.DataFrame(row_dict)
        return pd.concat([left, new_row], ignore_index=True)
    
    if isinstance(right, list):
        if len(right) != len(left.columns):
            raise ValueError(
                f"List length ({len(right)}) must match DataFrame columns ({len(left.columns)}). "
                f"Expected {len(left.columns)} values for columns: {list(left.columns)}"
            )
        
        new_row = pd.DataFrame([right], columns=left.columns)
        return pd.concat([left, new_row], ignore_index=True)
    
    raise TypeError(
        f"Cannot append {type(right).__name__} to DataFrame.  "
        f"Supported types: DataFrame, Series, dict, list"
    )


# Note: smart_append is kept for backward compatibility but is no longer used in the +: operator path
# The +: operator now uses __opkit_vstack__ directly with typed operands only