"""
Exception Extractor for AFE v2

Extracts structured context from tracebacks for precise fix generation.
"""

import re
import ast
import traceback as tb_module
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ExceptionContext:
    """Structured context extracted from an exception."""
    exception_type: str = "UnknownError"
    message: str = ""
    lineno: int = 0
    filename: str = ""
    function: str = ""
    failing_line: str = ""
    locals: Dict[str, Any] = field(default_factory=dict)
    globals: Dict[str, Any] = field(default_factory=dict)
    context_lines: List[str] = field(default_factory=list)
    
    # Extracted expression details
    failing_expression: str = ""
    operands: List[str] = field(default_factory=list)
    

class ExceptionExtractor:
    """
    Extracts structured ExceptionContext from error events and tracebacks.
    """
    
    def extract(self, error_event: Dict[str, Any], source_code: str = "") -> ExceptionContext:
        """
        Extract structured context from an error event.
        
        Args:
            error_event: Dict containing exception info (type, message, traceback, locals, globals)
            source_code: Optional source code of the failing script
            
        Returns:
            ExceptionContext with all extracted details
        """
        ctx = ExceptionContext()
        
        # Extract exception type and message
        ctx.exception_type = self._extract_exception_type(error_event)
        ctx.message = self._extract_message(error_event)
        
        # Extract location info from traceback
        traceback_str = error_event.get("traceback", "")
        location = self._extract_location(traceback_str)
        ctx.lineno = location.get("lineno", 0)
        ctx.filename = location.get("filename", "")
        ctx.function = location.get("function", "")
        ctx.failing_line = location.get("failing_line", "")
        
        # Extract locals and globals
        ctx.locals = self._sanitize_vars(error_event.get("locals", {}))
        ctx.globals = self._sanitize_vars(error_event.get("globals", {}))
        
        # Extract context lines from source code
        if source_code and ctx.lineno > 0:
            ctx.context_lines = self._extract_context_lines(source_code, ctx.lineno)
        
        # Analyze failing expression
        if ctx.failing_line:
            expr_info = self._analyze_expression(ctx.failing_line, ctx.exception_type)
            ctx.failing_expression = expr_info.get("expression", "")
            ctx.operands = expr_info.get("operands", [])
        
        return ctx
    
    def _extract_exception_type(self, event: Dict) -> str:
        """Extract exception type from event."""
        # Try direct field
        if "exception_type" in event:
            return event["exception_type"]
        
        # Try parsing from traceback (last line usually has Type: Message)
        tb = event.get("traceback", "")
        if tb:
            lines = tb.strip().split("\n")
            last_line = lines[-1]
            if ":" in last_line:
                return last_line.split(":", 1)[0].strip()
            
            # Fallback regex for standard python tracebacks
            match = re.search(r'^(\w+):', last_line)
            if match:
                return match.group(1)
        
        # Try parsing from message
        msg = event.get("message", "") or event.get("error", "")
        match = re.search(r'^(\w+Error|\w+Exception)', msg)
        if match:
            return match.group(1)
        
        return "UnknownError"
    
    def _extract_message(self, event: Dict) -> str:
        """Extract error message."""
        if "message" in event:
            return event["message"]
        if "error" in event:
            return event["error"]
        
        # Parse from traceback
        tb = event.get("traceback", "")
        lines = tb.strip().split("\n")
        if lines:
            last_line = lines[-1]
            # Remove exception type prefix
            if ":" in last_line:
                return last_line.split(":", 1)[1].strip()
            return last_line
        
        return ""
    
    def _extract_location(self, traceback_str: str) -> Dict[str, Any]:
        """Extract file, line, function from traceback."""
        result = {"lineno": 0, "filename": "", "function": "", "failing_line": ""}
        
        if not traceback_str:
            return result
        
        # Match: File "script.py", line 74, in compute_ratio
        # Also capture the next line which is the failing code
        pattern = r'File "([^"]+)", line (\d+), in (\w+)\s*\n\s*(.+?)(?:\n|$)'
        matches = list(re.finditer(pattern, traceback_str, re.MULTILINE))
        
        if matches:
            # Get the last match (innermost frame)
            last_match = matches[-1]
            result["filename"] = last_match.group(1)
            result["lineno"] = int(last_match.group(2))
            result["function"] = last_match.group(3)
            result["failing_line"] = last_match.group(4).strip()
        
        return result
    
    def _sanitize_vars(self, vars_dict: Dict) -> Dict[str, Any]:
        """Sanitize variables for safe serialization and display."""
        if not vars_dict:
            return {}
        
        sanitized = {}
        for key, value in vars_dict.items():
            # Skip private/dunder attributes
            if key.startswith("_"):
                continue
            # Skip modules and functions
            if isinstance(value, type) or callable(value):
                continue
            # Truncate long strings
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            # Convert complex objects to repr
            try:
                if not isinstance(value, (int, float, str, bool, list, dict, type(None))):
                    value = repr(value)[:100]
                sanitized[key] = value
            except:
                sanitized[key] = "<unserializable>"
        
        return sanitized
    
    def _extract_context_lines(self, source: str, lineno: int, context: int = 5) -> List[str]:
        """Extract lines around the failing line."""
        lines = source.splitlines()
        start = max(0, lineno - context - 1)
        end = min(len(lines), lineno + context)
        
        result = []
        for i in range(start, end):
            prefix = ">>> " if (i + 1) == lineno else "    "
            result.append(f"{i + 1:4d} {prefix}{lines[i]}")
        
        return result
    
    def _analyze_expression(self, line: str, exception_type: str) -> Dict[str, Any]:
        """Analyze the failing expression to extract operands."""
        result = {"expression": "", "operands": []}
        
        try:
            # Parse the line as AST
            tree = ast.parse(line.strip())
            if not tree.body:
                return result
            
            node = tree.body[0]
            
            # For assignment, look at the value
            if isinstance(node, ast.Assign) and node.value:
                expr_node = node.value
            elif isinstance(node, ast.Expr):
                expr_node = node.value
            else:
                expr_node = node
            
            # Extract based on exception type
            if exception_type == "ZeroDivisionError":
                result = self._analyze_division(expr_node, line)
            elif exception_type == "KeyError":
                result = self._analyze_subscript(expr_node, line)
            elif exception_type == "TypeError":
                result = self._analyze_binop(expr_node, line)
            elif exception_type == "IndexError":
                result = self._analyze_subscript(expr_node, line)
            elif exception_type == "AttributeError":
                result = self._analyze_attribute(expr_node, line)
            else:
                result["expression"] = line.strip()
                
        except SyntaxError:
            result["expression"] = line.strip()
        
        return result
    
    def _analyze_division(self, node: ast.AST, line: str) -> Dict[str, Any]:
        """Find division operands in expression."""
        result = {"expression": line.strip(), "operands": [], "operator": "/"}
        
        def find_div(n):
            if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                # Get source representation
                left = ast.unparse(n.left) if hasattr(ast, 'unparse') else str(n.left)
                right = ast.unparse(n.right) if hasattr(ast, 'unparse') else str(n.right)
                result["operands"] = [left, right]
                result["numerator"] = left
                result["denominator"] = right
                return True
            
            for child in ast.iter_child_nodes(n):
                if find_div(child):
                    return True
            return False
        
        find_div(node)
        return result
    
    def _analyze_subscript(self, node: ast.AST, line: str) -> Dict[str, Any]:
        """Find subscript access (dict/list) in expression."""
        result = {"expression": line.strip(), "operands": []}
        
        def find_subscript(n):
            if isinstance(n, ast.Subscript):
                container = ast.unparse(n.value) if hasattr(ast, 'unparse') else str(n.value)
                key = ast.unparse(n.slice) if hasattr(ast, 'unparse') else str(n.slice)
                result["operands"] = [container, key]
                result["container"] = container
                result["key"] = key
                return True
            
            for child in ast.iter_child_nodes(n):
                if find_subscript(child):
                    return True
            return False
        
        find_subscript(node)
        return result
    
    def _analyze_binop(self, node: ast.AST, line: str) -> Dict[str, Any]:
        """Find binary operation in expression."""
        result = {"expression": line.strip(), "operands": []}
        
        def find_binop(n):
            if isinstance(n, ast.BinOp):
                left = ast.unparse(n.left) if hasattr(ast, 'unparse') else str(n.left)
                right = ast.unparse(n.right) if hasattr(ast, 'unparse') else str(n.right)
                result["operands"] = [left, right]
                result["left"] = left
                result["right"] = right
                return True
            
            for child in ast.iter_child_nodes(n):
                if find_binop(child):
                    return True
            return False
        
        find_binop(node)
        return result
    
    def _analyze_attribute(self, node: ast.AST, line: str) -> Dict[str, Any]:
        """Find attribute access in expression."""
        result = {"expression": line.strip(), "operands": []}
        
        def find_attr(n):
            if isinstance(n, ast.Attribute):
                obj = ast.unparse(n.value) if hasattr(ast, 'unparse') else str(n.value)
                attr = n.attr
                result["operands"] = [obj, attr]
                result["object"] = obj
                result["attribute"] = attr
                return True
            
            for child in ast.iter_child_nodes(n):
                if find_attr(child):
                    return True
            return False
        
        find_attr(node)
        return result
