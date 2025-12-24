"""
Runtime dispatcher for operators that work on multiple types
"""

import builtins
import numpy as np
import pandas as pd

# Import helper functions - try relative imports first (for package), then absolute (for tests)
if __package__:
    from .pandas_ops import dollar_pandas
    from .numpy_ops import vconcat
else:
    from pandas_ops import dollar_pandas
    from numpy_ops import vconcat


def __opkit_dollar__(expr):
    """
    Unary $ operator - dispatches based on type
    
    - list/tuple → numpy array
    - dict → pandas DataFrame
    """
    if isinstance(expr, (list, tuple)):
        return np.array(expr)
    elif isinstance(expr, dict):
        return dollar_pandas(expr)
    elif isinstance(expr, (np.ndarray, pd.DataFrame)):
        # Accept ndarray or DataFrame and return as-is
        return expr
    else:
        raise TypeError(f"Cannot apply $ operator to {type(expr).__name__}")


def __opkit_vstack__(a, b):
    """
    Binary +:  operator - vstack for numpy, typed vstack for pandas
    
    - numpy array → vstack
    - pandas DataFrame → vstack with DataFrame or ndarray (1-D or 2-D) right operand only
      - 1-D ndarray: length must match DataFrame column count (appends as single row)
      - 2-D ndarray: width must match DataFrame column count (appends as multiple rows)
    """
    if isinstance(a, pd.DataFrame):
        # Accept only DataFrame or ndarray (1-D or 2-D) with matching column count
        if isinstance(b, pd.DataFrame):
            return pd.concat([a, b], ignore_index=True)
        elif isinstance(b, np.ndarray):
            # Accept 1-D or 2-D arrays
            if b.ndim == 1:
                # 1-D array: check length matches column count
                if len(b) != len(a.columns):
                    raise ValueError(
                        f"1-D array length ({len(b)}) must match DataFrame column count ({len(a.columns)}). "
                        f"Expected {len(a.columns)} values for columns: {list(a.columns)}"
                    )
                # Convert to single-row DataFrame
                new_row = pd.DataFrame([b], columns=a.columns)
                return pd.concat([a, new_row], ignore_index=True)
            elif b.ndim == 2:
                # 2-D array: check width (number of columns) matches DataFrame column count
                if b.shape[1] != len(a.columns):
                    raise ValueError(
                        f"2-D array width ({b.shape[1]}) must match DataFrame column count ({len(a.columns)}). "
                        f"Expected {len(a.columns)} columns for: {list(a.columns)}"
                    )
                # Convert to DataFrame with matching columns
                new_rows = pd.DataFrame(b, columns=a.columns)
                return pd.concat([a, new_rows], ignore_index=True)
            else:
                raise ValueError(f"Only 1-D or 2-D numpy arrays are accepted as right operand for DataFrame +:. Got {b.ndim}-D array.")
        elif isinstance(b, pd.Series):
            raise TypeError(
                "Cannot use pd.Series directly with +: operator on DataFrame. "
                "Convert to typed operand first using $ operator. "
                "For dict-like Series, use: df +: dict(series)$ "
                "For array-like Series, use: df +: series.values (if 1-D and matching column count)"
            )
        elif isinstance(b, dict):
            raise TypeError(
                "Cannot use dict directly with +: operator on DataFrame. "
                "Use $ operator to convert to DataFrame first: df +: {...}$"
            )
        elif isinstance(b, (list, tuple)):
            raise TypeError(
                f"Cannot use {type(b).__name__} directly with +: operator on DataFrame. "
                f"Use $ operator to convert to numpy array first: df +: [...]$ or df +: (...)$ "
                f"(ensure length matches DataFrame column count)"
            )
        else:
            raise TypeError(
                f"DataFrame +: operator requires right operand to be DataFrame or numpy.ndarray (1-D or 2-D). "
                f"Got {type(b).__name__}. Use $ operator to convert literals to typed objects first."
            )
    elif isinstance(a, np.ndarray):
        return vconcat(a, b)
    else:
        raise TypeError(f"+: operator not supported for {type(a).__name__}")


# Register all runtime operators in builtins
builtins.__opkit_dollar__ = __opkit_dollar__
builtins.__opkit_vstack__ = __opkit_vstack__