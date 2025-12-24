"""Transform custom operator syntax to valid Python."""

import re
from typing import Callable, Optional, Tuple

MAX_PASSES = 20


def _find_matching_forward(source: str, start: int, open_char: str, close_char: str) -> Optional[int]:
    """Return index just past the matching closing char, or None if unbalanced."""
    depth = 1
    idx = start + 1
    while idx < len(source) and depth:
        if source[idx] == open_char:
            depth += 1
        elif source[idx] == close_char:
            depth -= 1
        idx += 1
    return idx if depth == 0 else None


def _find_matching_backward(source: str, end: int, close_char: str, open_char: str) -> Optional[int]:
    """Return index of the matching opening bracket (inclusive)."""
    depth = 0
    idx = end - 1
    while idx >= 0:
        ch = source[idx]
        if ch == close_char:
            depth += 1
        elif ch == open_char:
            depth -= 1
            if depth == 0:
                return idx
        idx -= 1
    return None


def _extract_left_operand(source: str, op_start: int) -> Optional[Tuple[int, int, str]]:
    """Extract the left operand ending at op_start."""
    left_end = op_start
    while left_end > 0 and source[left_end - 1].isspace():
        left_end -= 1
    if left_end <= 0:
        return None

    prev = source[left_end - 1]
    if prev in ')]}':
        pairs = {')': '(', ']': '[', '}': '{'}
        open_char = pairs[prev]
        left_start = _find_matching_backward(source, left_end, prev, open_char)
        if left_start is None:
            return None
        # If the bracketed expr is a call, include the callable name before it
        k = left_start - 1
        while k >= 0 and (source[k].isalnum() or source[k] in '._'):
            k -= 1
        left_start = k + 1
        return left_start, left_end, source[left_start:left_end]

    # Identifier/function name
    left_start = left_end - 1
    while left_start > 0 and (source[left_start - 1].isalnum() or source[left_start - 1] == '_'):
        left_start -= 1
    return left_start, left_end, source[left_start:left_end]


def _extract_right_operand(source: str, op_end: int, allow_brackets: bool = False) -> Optional[Tuple[int, int, str]]:
    """Extract the right operand starting at op_end."""
    right_start = op_end
    while right_start < len(source) and source[right_start].isspace():
        right_start += 1
    if right_start >= len(source):
        return None

    ch = source[right_start]
    if allow_brackets and ch in '{[':
        close = '}' if ch == '{' else ']'
        right_end = _find_matching_forward(source, right_start, ch, close)
        if right_end is None:
            return None
        return right_start, right_end, source[right_start:right_end]

    # Identifier or function call
    if ch.isalnum() or ch == '_' or ch == '(':  # permit paren-wrapped expression
        # If starts with (, capture whole group
        if ch == '(':
            right_end = _find_matching_forward(source, right_start, '(', ')')
            if right_end is None:
                return None
            return right_start, right_end, source[right_start:right_end]

        right_end = right_start
        while right_end < len(source) and (source[right_end].isalnum() or source[right_end] == '_'):
            right_end += 1

        temp = right_end
        while temp < len(source) and source[temp].isspace():
            temp += 1

        if temp < len(source) and source[temp] == '(':
            call_end = _find_matching_forward(source, temp, '(', ')')
            if call_end is None:
                return None
            right_end = call_end
        return right_start, right_end, source[right_start:right_end]

    return None


def _transform_unary_dollar(source: str) -> str:
    result = source
    changed = True
    while changed:
        changed = False
        for i in range(len(result) - 1, 0, -1):
            if result[i] != '$':
                continue
            close_char = result[i - 1] if i > 0 else ''
            if close_char not in ')]}':
                continue
            pairs = {')': '(', ']': '[', '}': '{'}
            open_char = pairs[close_char]
            start = _find_matching_backward(result, i, close_char, open_char)
            if start is None:
                continue
            k = start - 1
            while k >= 0 and (result[k].isalnum() or result[k] in '._'):
                k -= 1
            expr_start = k + 1
            expr = result[expr_start:i]
            replacement = f'__opkit_dollar__({expr})'
            result = result[:expr_start] + replacement + result[i + 1:]
            changed = True
            break
    return result


def _transform_unary_postfix(source: str, operator: str, function: str) -> str:
    """Transform postfix unary operators like _ and |"""
    result = source
    changed = True
    while changed:
        changed = False
        for i in range(len(result) - 1, 0, -1):
            if result[i] != operator:
                continue
            close_char = result[i - 1] if i > 0 else ''
            if close_char not in ')]}':
                continue
            pairs = {')': '(', ']': '[', '}': '{'}
            open_char = pairs[close_char]
            start = _find_matching_backward(result, i, close_char, open_char)
            if start is None:
                continue
            k = start - 1
            while k >= 0 and (result[k].isalnum() or result[k] in '._'):
                k -= 1
            expr_start = k + 1
            expr = result[expr_start:i]
            replacement = f'{function}({expr})'
            result = result[:expr_start] + replacement + result[i + 1:]
            changed = True
            break
    return result


def _transform_binary(
    source: str,
    pattern: str,
    builder: Callable[[str, str], str],
    allow_brackets: bool = False,
    max_passes: int = MAX_PASSES,
) -> str:
    for _ in range(max_passes):
        match = re.search(pattern, source)
        if not match:
            break

        op_start, op_end = match.span()
        left = _extract_left_operand(source, op_start)
        right = _extract_right_operand(source, op_end, allow_brackets=allow_brackets)

        if not left or not right:
            break

        left_start, left_end, left_operand = left
        right_start, right_end, right_operand = right
        replacement = builder(left_operand, right_operand)
        source = source[:left_start] + replacement + source[right_end:]
    return source


def transform_operators(source: str) -> str:
    """Transform custom operator syntax to function calls."""
    # Order matters: handle unary first, then binary operators.
    # Process in order: most specific patterns first
    source = _transform_unary_dollar(source)
    
    # Unary postfix reshape operators
    source = _transform_unary_postfix(source, '_', '__opkit_as_row__')
    source = _transform_unary_postfix(source, '|', '__opkit_as_column__')
    
    # Stacking operators (/ prefix)
    source = _transform_binary(source, r'/\.\.', lambda a, b: f'__opkit_slash_hstack__({a}, {b})', allow_brackets=True)
    source = _transform_binary(source, r'/:' , lambda a, b: f'__opkit_slash_vstack__({a}, {b})', allow_brackets=True)
    source = _transform_binary(source, r'/\.(?![.:])', lambda a, b: f'__opkit_slash_lastdimstack__({a}, {b})', allow_brackets=True)
    
    # Tiling operators (* prefix) - right operand is a number or tuple
    # Note: Process *:. before *: to match the more specific pattern first
    source = _transform_binary(source, r'\*:\.', lambda a, b: f'__opkit_tile_2d__({a}, {b})', allow_brackets=True)
    source = _transform_binary(source, r'\*\.\.', lambda a, b: f'__opkit_tile_hconcat__({a}, {b})', allow_brackets=False)
    source = _transform_binary(source, r'\*:', lambda a, b: f'__opkit_tile_vconcat__({a}, {b})', allow_brackets=False)
    source = _transform_binary(source, r'\*\.(?![.:])', lambda a, b: f'__opkit_tile_lastdimconcat__({a}, {b})', allow_brackets=False)
    
    # Concatenation operators (+ prefix)
    source = _transform_binary(source, r'\+\.\.', lambda a, b: f'__opkit_hconcat__({a}, {b})', allow_brackets=True)
    source = _transform_binary(source, r'\+:', lambda a, b: f'__opkit_vstack__({a}, {b})', allow_brackets=True)
    source = _transform_binary(source, r'\+\.(?![.:])', lambda a, b: f'__opkit_lastdimconcat__({a}, {b})', allow_brackets=True)
    
    return source


def transform_operators_advanced(source: str) -> str:
    """Placeholder for a tokenization-based transformer."""
    return transform_operators(source)