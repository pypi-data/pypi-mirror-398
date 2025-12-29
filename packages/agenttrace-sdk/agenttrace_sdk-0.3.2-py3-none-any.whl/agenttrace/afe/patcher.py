import ast
import json
import os
import re
from typing import Optional, Dict, Any
from .models import AFECandidate

class ApplyEngine:
    """
    Applies fixes (code patches or config changes) to source files.
    Uses AST for robust Python code replacement.
    """

    def apply_file_patch(self, file_path: str, candidate: AFECandidate) -> bool:
        """
        Applies the candidate fix to the specified file.
        """
        if not os.path.exists(file_path):
            print(f"❌ Patcher: File not found: {file_path}")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = self.apply_patch(content, candidate, file_path)
            
            if new_content == content:
                print("⚠️ Patcher: No changes applied.")
                return False

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            print(f"✅ Patcher: Applied {candidate.type} to {file_path}")
            return True

        except Exception as e:
            print(f"❌ Patcher: Failed to apply patch: {e}")
            return False

    def apply_patch(self, source_code: str, candidate: AFECandidate, filename: str = "") -> str:
        """
        Dispatches to specific patch logic based on candidate type.
        """
        if candidate.type == "code_patch":
            return self._apply_code_patch(source_code, candidate.diff)
        elif candidate.type == "config_change":
            return self._apply_config_change(source_code, candidate.diff)
        elif candidate.type == "prompt_patch":
             # Simple string replacement for now, or regex if marker exists
             # Assuming prompt is in a variable or we append a patch
             return self._apply_code_patch(source_code, candidate.diff)
        
        return source_code

    def _apply_code_patch(self, source: str, patch: str) -> str:
        """
        Applies a code patch. 
        Strategies:
        1. If patch has "# [TYPE] at line N", use line-based injection (Scoped).
        2. If patch has markers (AFE_PATCH:...), replace the block.
        3. If patch is a function def, replace the existing function in AST.
        4. Fallback: Append if not found? (Risky)
        """
        # 1. Line-based Injection (Scoped)
        # Format: # PREPEND at line 45:
        #         code...
        line_match = re.match(r"# (PREPEND|WRAP|REPLACE) at line (\d+|\?):", patch)
        if line_match:
            action = line_match.group(1)
            lineno_str = line_match.group(2)
            if lineno_str != "?":
                lineno = int(lineno_str)
                # Remove the directive line
                clean_patch = "\n".join(patch.split("\n")[1:])
                return self._apply_line_level_patch(source, clean_patch, action, lineno)

        # 2. Marker-based replacement (Fast & Safe)
        # Format: # === AFE_PATCH:NAME === ... # === END AFE_PATCH:NAME ===
        marker_match = re.search(r"# === AFE_PATCH:(\w+) ===", patch)
        if marker_match:
            marker_name = marker_match.group(1)
            start_marker = f"# === AFE_PATCH:{marker_name} ==="
            end_marker = f"# === END AFE_PATCH:{marker_name} ==="
            
            # Check if markers exist in source (Replacement)
            if start_marker in source and end_marker in source:
                # Regex replace everything between markers
                pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
                return re.sub(pattern, patch, source, flags=re.DOTALL)
            
            # If markers don't exist, we might be inserting a NEW block.
            # But where? For now, let's try AST replacement of functions.

        # 2. AST-based Function Replacement
        try:
            source_tree = ast.parse(source)
            patch_tree = ast.parse(patch)
            
            # Find functions defined in the patch
            patch_funcs = [n for n in patch_tree.body if isinstance(n, ast.FunctionDef)]
            
            if not patch_funcs:
                # Maybe it's a top-level statement or import?
                # Fallback: Append to end if it looks like a helper
                return source + "\n\n" + patch

            class FunctionReplacer(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    for pf in patch_funcs:
                        if node.name == pf.name:
                            return pf # Replace with patch version
                    return node

            new_tree = FunctionReplacer().visit(source_tree)
            
            # If we didn't change anything, maybe we need to INSERT the function?
            # Check if function names exist in original source
            source_func_names = {n.name for n in source_tree.body if isinstance(n, ast.FunctionDef)}
            for pf in patch_funcs:
                if pf.name not in source_func_names:
                    # Append new function to body
                    new_tree.body.append(pf)
            
            return ast.unparse(new_tree)

        except Exception as e:
            print(f"⚠️ AST Patching failed: {e}. Falling back to append.")
            return source + "\n\n" + patch

    def _apply_line_level_patch(self, source: str, patch: str, action: str, lineno: int) -> str:
        """Apply patch at specific line number with indentation matching."""
        lines = source.splitlines()
        # lineno is 1-indexed
        idx = lineno - 1
        
        if idx < 0 or idx >= len(lines):
            print(f"⚠️ Line {lineno} out of bounds.")
            return source

        target_line = lines[idx]
        indent = re.match(r"\s*", target_line).group(0)
        
        # Indent the patch
        # Assume patch is already relative-indented (starts at column 0 inside its block)
        # But we need to add the target line's base indentation to it
        patched_lines = []
        for pl in patch.splitlines():
            patched_lines.append(indent + pl)
            
        if action == "PREPEND":
            # Insert before target line
            lines.insert(idx, "\n".join(patched_lines))
        elif action == "REPLACE":
            # Replace target line
            lines[idx] = "\n".join(patched_lines)
        elif action == "WRAP":
            # Wrap is harder: 
            # try:
            #     <target_line>
            # except...
            # The 'target_line' needs to be indented further inside the try block
            # My 'patch' probably looks like:
            # try:
            #     {original_line}
            # except...
            # So 'patch' ALREADY CONTAINS the original line (from generator).
            # So effectively, WRAP is just a REPLACE of that line with a multi-line block.
            lines[idx] = "\n".join(patched_lines)
            
        return "\n".join(lines)

    def _apply_config_change(self, source: str, patch: str) -> str:
        """
        Merges JSON config.
        """
        try:
            original_config = json.loads(source)
            patch_config = json.loads(patch)
            
            # Deep merge or top-level update?
            # Let's do top-level update for now
            original_config.update(patch_config)
            
            return json.dumps(original_config, indent=2)
        except Exception as e:
            print(f"⚠️ Config Patching failed: {e}")
            return source
