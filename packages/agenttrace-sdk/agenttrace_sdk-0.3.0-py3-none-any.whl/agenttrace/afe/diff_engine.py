"""
Diff Application Engine for AFE v2

Applies patches to source code with support for:
- prepend: Insert lines before target
- replace: Replace target line(s)
- wrap: Wrap target in a block
- append: Insert lines after target
"""

import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class AFEPatch:
    """Structured patch to apply."""
    patch_type: str  # "prepend", "replace", "wrap", "append"
    target_lineno: int
    original_line: str
    patched_code: str
    

class DiffEngine:
    """
    Applies patches to source code safely.
    Handles indentation preservation and multi-line patches.
    """
    
    def apply_patch(self, source: str, patch: AFEPatch) -> str:
        """
        Apply a patch to source code.
        
        Args:
            source: Original source code
            patch: AFEPatch to apply
            
        Returns:
            Patched source code
        """
        lines = source.splitlines()
        
        # Validate line number
        if patch.target_lineno < 1 or patch.target_lineno > len(lines):
            raise ValueError(f"Invalid target line {patch.target_lineno} for source with {len(lines)} lines")
        
        target_idx = patch.target_lineno - 1  # 0-indexed
        target_line = lines[target_idx]
        
        # Get indentation from target line
        indent = self._get_indent(target_line)
        
        if patch.patch_type == "prepend":
            return self._apply_prepend(lines, target_idx, patch.patched_code, indent)
        elif patch.patch_type == "replace":
            return self._apply_replace(lines, target_idx, patch.patched_code, indent)
        elif patch.patch_type == "wrap":
            return self._apply_wrap(lines, target_idx, patch.patched_code, target_line, indent)
        elif patch.patch_type == "append":
            return self._apply_append(lines, target_idx, patch.patched_code, indent)
        else:
            raise ValueError(f"Unknown patch type: {patch.patch_type}")
    
    def _apply_prepend(self, lines: List[str], target_idx: int, patch_code: str, indent: str) -> str:
        """Insert patch lines before target."""
        indented_patch = self._indent_code(patch_code, indent)
        lines.insert(target_idx, indented_patch)
        return "\n".join(lines)
    
    def _apply_replace(self, lines: List[str], target_idx: int, patch_code: str, indent: str) -> str:
        """Replace target line with patch."""
        indented_patch = self._indent_code(patch_code, indent)
        lines[target_idx] = indented_patch
        return "\n".join(lines)
    
    def _apply_wrap(self, lines: List[str], target_idx: int, patch_code: str, original: str, indent: str) -> str:
        """Wrap target line in a block (e.g., try/except, for loop)."""
        # The patch_code should contain {original_line} placeholder
        if "{original_line}" in patch_code:
            filled = patch_code.replace("{original_line}", original.strip())
        else:
            # Assume patch_code wraps around the original
            filled = patch_code + "\n" + " " * 4 + original.strip()
        
        indented_patch = self._indent_code(filled, indent)
        lines[target_idx] = indented_patch
        return "\n".join(lines)
    
    def _apply_append(self, lines: List[str], target_idx: int, patch_code: str, indent: str) -> str:
        """Insert patch lines after target."""
        indented_patch = self._indent_code(patch_code, indent)
        lines.insert(target_idx + 1, indented_patch)
        return "\n".join(lines)
    
    def _get_indent(self, line: str) -> str:
        """Extract leading whitespace from a line."""
        match = re.match(r'^(\s*)', line)
        return match.group(1) if match else ""
    
    def _indent_code(self, code: str, base_indent: str) -> str:
        """Apply base indentation to all lines of code."""
        lines = code.splitlines()
        if not lines:
            return ""
        
        # Find minimum indentation in patch (excluding empty lines)
        min_indent = float('inf')
        for line in lines:
            if line.strip():
                line_indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, line_indent)
        
        if min_indent == float('inf'):
            min_indent = 0
        
        # Remove existing indent and add base indent
        result = []
        for line in lines:
            if line.strip():
                # Remove minimum indent, add base indent
                stripped = line[min_indent:] if len(line) >= min_indent else line.lstrip()
                result.append(base_indent + stripped)
            else:
                result.append("")
        
        return "\n".join(result)
    
    def create_unified_diff(self, original: str, patched: str, filename: str = "script.py") -> str:
        """
        Create a unified diff between original and patched code.
        
        Returns:
            Unified diff string
        """
        import difflib
        original_lines = original.splitlines(keepends=True)
        patched_lines = patched.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            patched_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        )
        
        return "".join(diff)
    
    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate Python syntax of patched code.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            compile(code, "<string>", "exec")
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
