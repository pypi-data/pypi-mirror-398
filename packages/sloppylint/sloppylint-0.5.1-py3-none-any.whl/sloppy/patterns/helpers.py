"""Helper functions for pattern matching."""

from __future__ import annotations

import ast


def get_multiline_string_lines(source: str) -> set[int]:
    """
    Get all line numbers that are inside multi-line strings.

    Uses AST to find all string literals that span multiple lines,
    including docstrings and triple-quoted strings.

    Args:
        source: The source code to analyze

    Returns:
        Set of line numbers (1-indexed) that are inside multi-line strings
    """
    multiline_lines: set[int] = set()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return multiline_lines

    for node in ast.walk(tree):
        # Check for string constants (including docstrings)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                start_line = node.lineno
                end_line = node.end_lineno
                if end_line is not None and end_line > start_line:
                    # This is a multi-line string
                    for line_num in range(start_line, end_line + 1):
                        multiline_lines.add(line_num)

        # Also check Expr nodes (docstrings are Expr containing Constant)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                if hasattr(node.value, "lineno") and hasattr(node.value, "end_lineno"):
                    start_line = node.value.lineno
                    end_line = node.value.end_lineno
                    if end_line is not None and end_line > start_line:
                        for line_num in range(start_line, end_line + 1):
                            multiline_lines.add(line_num)

    return multiline_lines


def is_in_string_or_comment(
    line: str, position: int, multiline_string_lines: set[int] | None = None, lineno: int = 0
) -> bool:
    """
    Check if a position in a line is inside a string or after a comment.

    Args:
        line: The source line
        position: Character position to check
        multiline_string_lines: Optional set of line numbers inside multi-line strings
        lineno: Current line number (1-indexed) for multi-line string check

    Returns:
        True if the position is inside a string, multi-line string, or after a # comment
    """
    # Check if entire line is inside a multi-line string
    if multiline_string_lines and lineno in multiline_string_lines:
        return True

    prefix = line[:position]

    # Track string state and look for comments
    in_string = False
    string_char = None

    i = 0
    while i < len(prefix):
        char = prefix[i]

        # Handle escape sequences
        if char == "\\" and i + 1 < len(prefix):
            i += 2
            continue

        # Handle string boundaries
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None

        # Handle comments (only outside strings)
        elif char == "#" and not in_string:
            return True  # Everything after # is a comment

        i += 1

    return in_string
