"""
NumPy operator implementations
"""

import numpy as np
import builtins

def dollar_numpy(expr: list|tuple) -> np.ndarray:
    """
    Unary $ operator for lists/tuples → numpy arrays
    
    Examples:
        [1, 2, 3]$ → np.array([1, 2, 3])
        (1, 2, 3)$ → np.array((1, 2, 3))
    """
    # Accept ndarray directly; convert lists/tuples to ndarray
    if isinstance(expr, np.ndarray):
        return expr
    if isinstance(expr, (list, tuple)):
        return np.array(expr)
    raise TypeError(f"Cannot convert {type(expr).__name__} to numpy array with $ operator")


def hconcat(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    The +.. operator - horizontal concatenation (axis 1)
    
    Concatenates arrays along the horizontal axis (axis 1).
    For 1D arrays, both operands must have at least 2 dimensions.
    A 1D array can be concatenated with a 2D+ array by first expanding it.
    
    Examples: 
        np.array([[1], [2]]) +.. np.array([[3], [4]]) → np.array([[1, 3], [2, 4]])
    """
    # Reject two 1D arrays - they have no horizontal axis
    if a.ndim == 1 and b.ndim == 1:
        raise ValueError(
            "Cannot use +.. on two 1D arrays (vectors have no horizontal axis). "
            "For vectors, use +. to concatenate along the last axis, "
            "or use stacking operators: /: or /.."
        )
    
    # If one operand is 1D and the other is not, expand the 1D array along axis 1
    if a.ndim == 1 and b.ndim > 1:
        a = np.expand_dims(a, axis=1)
    elif b.ndim == 1 and a.ndim > 1:
        b = np.expand_dims(b, axis=1)
    
    return np.concatenate([a, b], axis=1)


def vconcat(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    The +: operator for numpy - vertical concatenation (axis 0)
    
    Concatenates arrays along the vertical axis (axis 0).
    For 1D arrays, both operands must have at least 2 dimensions.
    A 1D array can be concatenated with a 2D+ array by first expanding it.
    
    Examples: 
        np.array([[1, 2]]) +: np.array([[3, 4]]) → np.array([[1, 2], [3, 4]])
    """
    # Reject two 1D arrays - they have no vertical axis
    if a.ndim == 1 and b.ndim == 1:
        raise ValueError(
            "Cannot use +: on two 1D arrays (vectors have no vertical axis). "
            "For vectors, use +. to concatenate along the last axis, "
            "or use stacking operators: /: or /.."
        )
    
    # If one operand is 1D and the other is not, expand the 1D array along axis 0
    if a.ndim == 1 and b.ndim > 1:
        a = np.expand_dims(a, axis=0)
    elif b.ndim == 1 and a.ndim > 1:
        b = np.expand_dims(b, axis=0)
    
    return np.concatenate([a, b], axis=0)


def lastdimconcat(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    The +. operator - concatenation along the last axis (axis -1)
    
    For 1D arrays (vectors), this is the natural concatenation.
    For nD arrays, concatenates along the last axis.
    
    Examples: 
        np.array([1, 2]) +. np.array([3, 4]) → np.array([1, 2, 3, 4])
        np.array([[1], [2]]) +. np.array([[3], [4]]) → np.array([[1, 3], [2, 4]])
    """
    return np.concatenate([a, b], axis=-1)


# Stacking operators (/ prefix) - create a new axis
def slash_vstack(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    The /: operator - stacking along vertical axis (axis 0)
    
    Stacks arrays by adding a new dimension at axis 0.
    Both operands must have the same shape.
    
    Examples:
        np.array([1, 2]) /: np.array([3, 4]) → np.array([[1, 2], [3, 4]])
        np.array([[1, 2]]) /: np.array([[3, 4]]) → np.array([[[1, 2]], [[3, 4]]])
    """
    return np.stack([a, b], axis=0)


def slash_hstack(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    The /.. operator - stacking along horizontal axis (axis 1)
    
    Stacks arrays by adding a new dimension at axis 1.
    Both operands must have the same shape.
    For 1D arrays, this is the same as /. (both add the horizontal axis).
    
    Examples:
        np.array([1, 2]) /.. np.array([3, 4]) → np.array([[1, 2], [3, 4]])
        np.array([[1], [2]]) /.. np.array([[3], [4]]) → np.array([[[1], [3]], [[2], [4]]])
    """
    return np.stack([a, b], axis=1)


def slash_lastdimstack(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    The /. operator - stacking along the last axis (appended axis)
    
    Stacks arrays by adding a new dimension at axis -1 (last axis).
    Both operands must have the same shape.
    For 1D arrays, this adds the horizontal axis first (same as /..).
    
    Examples:
        np.array([1, 2]) /. np.array([3, 4]) → np.array([[1, 3], [2, 4]])
        np.array([[1, 2]]) /. np.array([[3, 4]]) → np.array([[[1, 3], [2, 4]]])
    """
    return np.stack([a, b], axis=-1)


# Error message for tiling operators that reject 1D arrays
_TILING_1D_ERROR_TEMPLATE = (
    "Cannot use {op} on 1D arrays (vectors have no preset orientation). "
    "Use operator *. if you want to tile along the only axis. Otherwise, "
    "use operator _ or | to reshape your array to a row / column matrix, then use the {op} operator."
)

# Tiling operators (* prefix) - repeat array
def tile_vconcat(a: np.ndarray, n: int) -> np.ndarray:
    """
    The *: operator - tile array along vertical axis (axis 0)
    
    Tiles the array n times along axis 0.
    Rejects 1D arrays (vectors) as they have no preset orientation.
    
    Examples:
        np.array([[1, 2]]) *: 3 → np.array([[1, 2], [1, 2], [1, 2]])
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"Tiling count must be a positive integer, got {n}")
    
    if a.ndim == 1:
        raise ValueError(_TILING_1D_ERROR_TEMPLATE.format(op="*:"))
    
    return np.tile(a, (n, 1))


def tile_hconcat(a: np.ndarray, n: int) -> np.ndarray:
    """
    The *.. operator - tile array along horizontal axis (axis 1)
    
    Tiles the array n times along axis 1.
    Rejects 1D arrays (vectors) as they have no preset orientation.
    
    Examples:
        np.array([[1], [2]]) *.. 3 → np.array([[1, 1, 1], [2, 2, 2]])
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"Tiling count must be a positive integer, got {n}")
    
    if a.ndim == 1:
        raise ValueError(_TILING_1D_ERROR_TEMPLATE.format(op="*.."))
    
    return np.tile(a, (1, n))


def tile_lastdimconcat(a: np.ndarray, n: int) -> np.ndarray:
    """
    The *. operator - tile array along last axis (axis -1)
    
    Tiles the array n times along the last axis.
    Accepts 1D arrays (vectors).
    
    Examples:
        np.array([1, 2, 3]) *. 2 → np.array([1, 2, 3, 1, 2, 3])
        np.array([[1, 2]]) *. 3 → np.array([[1, 2, 1, 2, 1, 2]])
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"Tiling count must be a positive integer, got {n}")
    
    return np.tile(a, n)


# More specific guidance for 2D tiling operator *:.
_TILING_1D_ERROR_TEMPLATE_2D = (
    "Cannot use *:. on 1D arrays (vectors have no preset orientation). "
    "Reshape to a row / column matrix, then use *:. with a tuple of counts, e.g. [1, 2]_ *:. (m, n) or [1, 2]| *:. (m, n)."
)


def tile_2d(a: np.ndarray, reps: tuple) -> np.ndarray:
    """
    The *:. operator - 2D tiling
    
    Tiles the array reps[0] times vertically and reps[1] times horizontally.
    Rejects 1D arrays (vectors) as they have no preset orientation.
    
    Examples:
        np.array([[1, 2]]) *:. (3, 2) → tiles 3 times vertically, 2 times horizontally
    """
    # Validate left operand type early to provide a clear error instead of AttributeError
    if not isinstance(a, np.ndarray):
        raise TypeError(
            f"Left operand for *:. must be a numpy array, got {type(a).__name__}. "
            "Convert lists/tuples with the $ operator, e.g. (1, 2, 3)$ *.:(3, 2)."
        )
    if not isinstance(reps, tuple) or len(reps) != 2:
        raise ValueError(f"2D tiling requires a tuple of two integers, got {reps}")
    
    m, n = reps
    if not isinstance(m, int) or not isinstance(n, int) or m <= 0 or n <= 0:
        raise ValueError(f"Tiling counts must be positive integers, got ({m}, {n})")
    
    if a.ndim == 1:
        # Use the 2D-specific guidance to avoid suggesting scalar counts
        raise ValueError(
            "Cannot use *:. on 1D arrays (vectors have no preset orientation). "
            "Reshape to a row / column matrix, e.g. [1, 2]_ or (3, 4, 5)|, then use *:. (m, n)."
        )
    
    return np.tile(a, (m, n))


# Unary reshape operators
def as_row(a: np.ndarray) -> np.ndarray:
    """
    The _ operator (postfix) - reshape as row matrix
    
    For 1D arrays (n,), reshapes to (1, n) - a row matrix.
    For nD arrays, inserts an extra axis at the first position.
    
    Examples:
        np.array([1, 2, 3])_ → np.array([[1, 2, 3]])  # shape (3,) to (1, 3)
        np.array([[1, 2]])_ → np.array([[[1, 2]]])    # shape (1, 2) to (1, 1, 2)
    """
    return np.expand_dims(a, axis=0)


def as_column(a: np.ndarray) -> np.ndarray:
    """
    The | operator (postfix) - reshape as column matrix
    
    For 1D arrays (n,), reshapes to (n, 1) - a column matrix.
    For nD arrays, inserts an extra axis at the second position.
    
    Examples:
        np.array([1, 2, 3])| → np.array([[1], [2], [3]])  # shape (3,) to (3, 1)
        np.array([[1, 2]])| → np.array([[[1], [2]]])      # shape (1, 2) to (1, 2, 1)
    """
    return np.expand_dims(a, axis=1)


# Register concatenation operators in builtins
builtins.__opkit_hconcat__ = hconcat
builtins.__opkit_vconcat__ = vconcat
builtins.__opkit_lastdimconcat__ = lastdimconcat

# Keep old names for backward compatibility
builtins.__opkit_hstack__ = hconcat
builtins.__opkit_vstack_numpy__ = vconcat
builtins.__opkit_dstack__ = lastdimconcat

# Register stacking operators in builtins
builtins.__opkit_slash_vstack__ = slash_vstack
builtins.__opkit_slash_hstack__ = slash_hstack
builtins.__opkit_slash_lastdimstack__ = slash_lastdimstack

# Register tiling operators in builtins
builtins.__opkit_tile_vconcat__ = tile_vconcat
builtins.__opkit_tile_hconcat__ = tile_hconcat
builtins.__opkit_tile_lastdimconcat__ = tile_lastdimconcat
builtins.__opkit_tile_2d__ = tile_2d

# Keep old names for backward compatibility during transition
builtins.__opkit_tile_vstack__ = tile_vconcat
builtins.__opkit_tile_hstack__ = tile_hconcat
builtins.__opkit_tile_dstack__ = tile_lastdimconcat

# Register unary reshape operators
builtins.__opkit_as_row__ = as_row
builtins.__opkit_as_column__ = as_column

# Register dollar operator
builtins.__opkit_dollar__ = dollar_numpy