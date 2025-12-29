"""Helper utilities for AST processing and filtering"""

import ast
import re
from typing import Optional, Union, List, Tuple, Any


def safe_unparse(node: Union[ast.AST, None]) -> str:
    """
    Safely unparse an AST node to string, compatible with Python 3.8
    """
    if node is None:
        return ""
        
    if hasattr(ast, 'unparse'):
        return ast.unparse(node)
    
    # Fallback for Python 3.8
    try:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif hasattr(ast, 'Str') and isinstance(node, ast.Str): # Python 3.8
            return node.s
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num): # Python 3.8
            return str(node.n)
        elif isinstance(node, ast.Attribute):
            return f"{safe_unparse(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            func = safe_unparse(node.func)
            args = ", ".join(safe_unparse(arg) for arg in node.args)
            return f"{func}({args})"
        elif isinstance(node, ast.Subscript):
            return f"{safe_unparse(node.value)}[{safe_unparse(node.slice)}]"
        elif isinstance(node, ast.Index): # Python 3.8
            return safe_unparse(node.value)
        elif isinstance(node, ast.BinOp):
            # Basic support for flags (A | B) or string concat
            op_str = "|" if isinstance(node.op, ast.BitOr) else "+"
            return f"{safe_unparse(node.left)} {op_str} {safe_unparse(node.right)}"
        elif isinstance(node, ast.List):
            return "[" + ", ".join(safe_unparse(e) for e in node.elts) + "]"
        elif isinstance(node, ast.Tuple):
            return "(" + ", ".join(safe_unparse(e) for e in node.elts) + ")"
    except Exception:
        pass
        
    # Last resort: return empty string or type to avoid crashing
    return ""


def extract_ast_snippet(code: str, node: ast.AST, max_length: int = 200) -> str:
    """
    Extract code snippet from AST node
    
    Args:
        code: Full source code
        node: AST node to extract snippet from
        max_length: Maximum snippet length
    
    Returns:
        Code snippet string
    """
    lines = code.splitlines()
    
    if not hasattr(node, 'lineno'):
        return ""
    
    start_line = max(0, node.lineno - 1)
    end_line = min(len(lines), getattr(node, 'end_lineno', node.lineno))
    
    snippet_lines = lines[start_line:end_line]
    snippet = ' '.join(line.strip() for line in snippet_lines)
    
    if len(snippet) > max_length:
        snippet = snippet[:max_length] + "..."
    
    return snippet


def extract_context_lines(code: str, node: Any, context_lines: int = 2) -> Tuple[List[str], int, int]:
    """
    Extract code lines with surrounding context for AI agents.
    Supports Python AST nodes and Esprima JS nodes.
    
    Args:
        code: Full source code
        node: AST node or Esprima node
        context_lines: Number of lines before and after to include
        
    Returns:
        Tuple of (list of code lines, start_line_number, end_line_number)
        Line numbers are 1-based.
    """
    lines = code.splitlines()
    total_lines = len(lines)
    
    # Determine start/end lines
    node_start = 0
    node_end = 0
    
    if hasattr(node, 'lineno'): # Python AST
        node_start = node.lineno
        node_end = getattr(node, 'end_lineno', node.lineno)
    elif hasattr(node, 'loc'): # Esprima JS
        # Esprima loc is usually an object with start/end attributes
        loc = node.loc
        if hasattr(loc, 'start') and hasattr(loc.start, 'line'):
            node_start = loc.start.line
            node_end = loc.end.line if hasattr(loc, 'end') else loc.start.line
        elif isinstance(loc, dict):
             node_start = loc.get('start', {}).get('line', 0)
             node_end = loc.get('end', {}).get('line', 0)
    
    if node_start == 0:
        return [], 0, 0

    # Calculate context range (0-based indices for list access)
    start_idx = max(0, node_start - 1 - context_lines)
    end_idx = min(total_lines, node_end + context_lines)
    
    # Extract lines
    extracted_lines = lines[start_idx:end_idx]
    
    # Return 1-based start/end line numbers for the whole block
    return extracted_lines, start_idx + 1, end_idx


def should_filter_log_finding(snippet: str, context: str) -> bool:
    """
    Determine if a LOG_PII finding should be filtered
    
    Args:
        snippet: Code snippet
        context: Context description
    
    Returns:
        True if should be filtered (ignored)
    """
    system_log_patterns = [
        r"file content truncated:",
        r"permission denied:",
        r"error reading file",
        r"database connection established",
        r"health check passed",
        r"failed to get redis info",
        r"fetched \d+ results",
        r"storing workspace result",
        r"worker started",
        r"task.*completed"
    ]
    
    snippet_lower = snippet.lower()
    
    for pattern in system_log_patterns:
        if re.search(pattern, snippet_lower, re.I):
            return True
    
    return False


def should_filter_db_finding(snippet: str) -> bool:
    """
    Determine if a DB_WRITE finding should be filtered
    
    Args:
        snippet: Code snippet
    
    Returns:
        True if should be filtered (ignored)
    """
    very_safe_patterns = [
        r"select.*count\(\*\)",
        r"select.*version\(\)",
        r"savepoint|rollback|commit",
        r"vacuum|analyze"
    ]
    
    snippet_lower = snippet.lower()
    
    for pattern in very_safe_patterns:
        if re.search(pattern, snippet_lower, re.I):
            return True
    
    return False
