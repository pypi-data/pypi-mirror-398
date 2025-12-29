import os
import json
from typing import Optional, Dict, Any
from groq import Groq
from .models import AFECandidate, RCAResult
from .extractor import ExceptionContext


class LLMFixGenerator:
    """
    Generates fix candidates using Groq LLM with strict rules.
    Prohibits generic try/except and requires precise variable-based patches.
    """
    
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            print("Warning: GROQ_API_KEY not set. LLM features disabled.")

    def generate_fix(
        self, 
        rca_result: RCAResult, 
        trace_context: str, 
        error_details: str, 
        detection_id: str,
        ctx: ExceptionContext = None
    ) -> Optional[AFECandidate]:
        """
        Generates a fix candidate by prompting the LLM with structured context.
        """
        if not self.client:
            return None

        prompt = self._construct_prompt(rca_result, trace_context, error_details, ctx)
        print(f"🔍 DEBUG: LLM Prompt:\n{prompt}\n--------------------------------")
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more deterministic output
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            return self._parse_response(response_content, detection_id)
            
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return None

    def _system_prompt(self) -> str:
        return """You are an expert Python debugger. Generate PRECISE code patches.

=== FORBIDDEN PATTERNS (NEVER generate these) ===
❌ except Exception as e: pass
❌ try: ... except: print(e)
❌ Generic catch-all wrappers
❌ Invented variable names not in LOCALS
❌ except Exception without specific handling
❌ Wrapping entire functions in try/except

=== REQUIRED OUTPUT ===
✅ Use ONLY variables from the LOCALS section
✅ Place guards BEFORE the failing line
✅ Use the EXACT variable names shown
✅ Generate minimal, surgical patches

=== EXCEPTION-SPECIFIC STRATEGIES ===
- ZeroDivisionError → if denominator == 0: raise ValueError("...")
- KeyError → if "key" not in dict_name: raise KeyError("...")
- TypeError → if not isinstance(var, expected_type): raise TypeError("...")
- IndexError → if index >= len(sequence): raise IndexError("...")
- AttributeError → if obj is None: raise ValueError("...")
- FileNotFoundError → from pathlib import Path; if not Path(x).exists(): ...

=== OUTPUT JSON SCHEMA ===
{
    "patch_type": "prepend" | "replace" | "wrap",
    "target_lineno": <int>,
    "original_line": "<exact line from trace>",
    "patched_code": "<your precise fix>",
    "confidence": 0.0-1.0,
    "reasoning": "<1-2 sentences>"
}

CRITICAL: If you cannot generate a specific fix, return confidence < 0.3 rather than a generic try/except.
"""

    def _construct_prompt(
        self, 
        rca: RCAResult, 
        trace: str, 
        error: str,
        ctx: ExceptionContext = None
    ) -> str:
        """Construct structured prompt with all available context."""
        
        # Build context section
        context_section = ""
        if ctx:
            context_section = f"""
=== EXCEPTION DETAILS ===
TYPE: {ctx.exception_type}
MESSAGE: {ctx.message}
FILE: {ctx.filename}:{ctx.lineno}
FUNCTION: {ctx.function}

=== FAILING LINE ===
>>> {ctx.failing_line}

=== LOCAL VARIABLES ===
{json.dumps(ctx.locals, indent=2, default=str)}

=== CONTEXT (surrounding lines) ===
{chr(10).join(ctx.context_lines) if ctx.context_lines else 'Not available'}
"""
        else:
            context_section = f"""
=== TRACE CONTEXT ===
{trace}

=== ERROR DETAILS ===
{error}
"""

        return f"""
{context_section}

=== RCA ANALYSIS ===
ROOT CAUSE: {rca.root_cause}
CONFIDENCE: {rca.confidence}
FIX STRATEGY: {rca.variables.get('fix_strategy', 'unknown')}
KEY VARIABLES: {json.dumps({k: v for k, v in rca.variables.items() if k not in ['fix_strategy', 'exception_type']}, default=str)}

Generate a PRECISE patch using ONLY the variables shown in LOCALS.
Do NOT invent new variable names.
"""

    def _parse_response(self, content: str, detection_id: str) -> Optional[AFECandidate]:
        """Parse LLM response and validate against forbidden patterns."""
        try:
            data = json.loads(content)
            
            # Validate: reject if confidence is too low
            confidence = float(data.get("confidence", 0.5))
            if confidence < 0.3:
                print(f"LLM returned low confidence ({confidence}), skipping candidate")
                return None
            
            # Validate: reject forbidden patterns
            patched_code = data.get("patched_code", "") or data.get("diff", "")
            if self._contains_forbidden_pattern(patched_code):
                print("LLM generated forbidden pattern, rejecting")
                return None
            
            # Build diff with metadata
            diff = self._format_diff(data)
            
            return AFECandidate(
                detection_id=detection_id,
                type=self._map_patch_type(data.get("patch_type", "code_patch")),
                summary=data.get("reasoning", "LLM Generated Fix")[:200],
                diff=diff,
                confidence=confidence,
                status="pending",
                validation_results={
                    "reasoning": data.get("reasoning", ""),
                    "patch_type": data.get("patch_type", "unknown"),
                    "target_lineno": data.get("target_lineno", 0),
                }
            )
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return None
    
    def _contains_forbidden_pattern(self, code: str) -> bool:
        """Check if code contains forbidden patterns."""
        forbidden = [
            "except Exception:",
            "except Exception as e:",
            "except:",
            "except Exception as e:\n    pass",
            "except Exception as e:\n        pass",
            'print(f"An error occurred',
            "print(e)",
        ]
        code_lower = code.lower()
        for pattern in forbidden:
            if pattern.lower() in code_lower:
                return True
        return False
    
    def _map_patch_type(self, patch_type: str) -> str:
        """Map LLM patch types to DB-valid types."""
        mapping = {
            "prepend": "code_patch",
            "replace": "code_patch",
            "wrap": "code_patch",
            "append": "code_patch",
        }
        return mapping.get(patch_type, "code_patch")
    
    def _format_diff(self, data: Dict) -> str:
        """Format the patch as a readable diff."""
        patch_type = data.get("patch_type", "prepend")
        original = data.get("original_line", "")
        patched = data.get("patched_code", "") or data.get("diff", "")
        lineno = data.get("target_lineno", 0)
        
        if patch_type == "prepend":
            return f"""# Insert BEFORE line {lineno}:
{patched}
# Original line remains:
# {original}"""
        elif patch_type == "replace":
            return f"""# Replace line {lineno}:
# BEFORE: {original}
# AFTER:
{patched}"""
        elif patch_type == "wrap":
            return f"""# Wrap line {lineno}:
{patched}"""
        else:
            return patched
