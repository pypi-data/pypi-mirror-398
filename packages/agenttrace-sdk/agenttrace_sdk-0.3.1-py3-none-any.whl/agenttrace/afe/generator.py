import os
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from typing import List, Optional
from .models import AFECandidate, RCAResult
from .llm import LLMFixGenerator
from .extractor import ExceptionContext
from .ranker import PatchRanker


# ==========================================================================
# CONSTRAINT-BASED PATCH TEMPLATES
# ==========================================================================

PATCH_TEMPLATES = {
    "division_by_zero": {
        "patch_type": "prepend",
        "template": """if {denominator} == 0:
    raise ValueError("{denominator} cannot be zero")""",
        "requirements": ["denominator"],
    },
    "missing_key": {
        "patch_type": "prepend", 
        "template": """if "{key}" not in {dict_name}:
    raise KeyError("Missing required key: {key}")""",
        "requirements": ["key", "dict_name"],
    },
    "type_mismatch": {
        "patch_type": "prepend",
        "template": """if {var_name} is None:
    raise TypeError("{var_name} cannot be None")""",
        "requirements": ["var_name"],
    },
    "index_out_of_bounds": {
        "patch_type": "prepend",
        "template": """if {index} >= len({sequence}):
    raise IndexError(f"Index {{index}} out of bounds for {sequence} with length {{len({sequence})}}")""",
        "requirements": ["index", "sequence"],
    },
    "attribute_error": {
        "patch_type": "prepend",
        "template": """if {object} is None:
    raise ValueError("{object} is None, cannot access .{attribute}")""",
        "requirements": ["object", "attribute"],
    },
    "file_not_found": {
        "patch_type": "prepend",
        "template": """from pathlib import Path
if not Path({filepath}).exists():
    raise FileNotFoundError(f"File not found: {filepath}")""",
        "requirements": ["filepath"],
    },
    "network_failure": {
        "patch_type": "wrap",
        "template": """for _retry in range({max_retries}):
    try:
        {original_line}
        break
    except (ConnectionError, TimeoutError) as e:
        if _retry == {max_retries} - 1:
            raise
        import time
        time.sleep({backoff_base} ** _retry)""",
        "requirements": ["max_retries", "backoff_base", "original_line"],
    },
    "recursion_error": {
        "patch_type": "prepend",
        "template": """import sys
if sys.getrecursionlimit() < 3000:
    sys.setrecursionlimit(3000)""",
        "requirements": [],
    },
    "invalid_value": {
        "patch_type": "wrap",
        "template": """try:
    {original_line}
except ValueError as e:
    # Auto-generated validation wrap
    raise ValueError(f"Value Error details: {{e}}")""",
        "requirements": ["original_line"],
    },
    "json_decode_error": {
        "patch_type": "wrap",
        "template": """try:
    {original_line}
except Exception: # Handle JSONDecodeError safely 
    # Fallback to empty dict or raw string
    pass""",
        "requirements": ["original_line"],
    },
}


class CandidateGenerator:
    """
    Generates fix candidates based on RCA results.
    Uses constraint-based templates for Python exceptions.
    Falls back to LLM for complex cases.
    """

    def __init__(self, templates_dir: str = None, groq_api_key: str = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), "templates")

        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.llm = LLMFixGenerator(api_key=groq_api_key)
        self.ranker = PatchRanker()

    # -------------------------------------------------------------------
    # Main entry point: return *one or many* candidates
    # -------------------------------------------------------------------

    def generate(
        self, 
        rca_result: RCAResult, 
        detection_id: str, 
        trace_context: str = "", 
        error_details: str = "",
        ctx: ExceptionContext = None
    ) -> List[AFECandidate]:
        """Generate fix candidates with constraint-based templates and LLM fallback."""
        root = rca_result.root_cause
        candidates = []

        # 1. Try constraint-based template first
        if root in PATCH_TEMPLATES:
            # Candidate A: Constraint (Prepend/Precheck)
            template_candidate = self._generate_from_template(root, rca_result, detection_id)
            if template_candidate:
                template_candidate.summary += " (Constraint)"
                candidates.append(template_candidate)
            
            # Candidate B: Defensive Wrap (Try/Except)
            # Only for supported types where we have original_line and a known Exception class
            wrap_candidate = self._generate_defensive_wrap(root, rca_result, detection_id)
            if wrap_candidate:
                candidates.append(wrap_candidate)

        # 2. Try legacy Jinja2 handlers for API-specific issues
        legacy_handlers = {
            "rate_limit_exceeded": self._generate_rate_limit_fixes,
            "context_window_exceeded": self._generate_context_fixes,
            "json_decode_error": self._generate_json_fix,
            "invalid_model_config": self._generate_model_config_fix,
            "tool_call_failure": self._generate_tool_fix,
            "model_refusal": self._generate_refusal_fix,
            "request_timeout": self._generate_timeout_fix,
        }

        if root in legacy_handlers:
            legacy_candidates = legacy_handlers[root](rca_result, detection_id)
            candidates.extend(legacy_candidates)

        # 3. Try LLM for unknown/complex errors
        if not candidates and self.llm and (trace_context or ctx):
            print(f"🤖 AFE: Attempting LLM fix generation for {root}...")
            llm_candidate = self.llm.generate_fix(
                rca_result, trace_context, error_details, detection_id, ctx
            )
            if llm_candidate:
                candidates.append(llm_candidate)

        # 4. Rank and return candidates
        if candidates:
            return self.ranker.rank(candidates)

        # 5. Last resort: manual intervention
        return self._generate_manual_intervention(root, rca_result, detection_id)

    def _generate_from_template(
        self, 
        root_cause: str, 
        rca: RCAResult, 
        detection_id: str
    ) -> Optional[AFECandidate]:
        """Generate candidate from constraint-based template."""
        template = PATCH_TEMPLATES.get(root_cause)
        if not template:
            return None
        
        # Check requirements
        variables = rca.variables
        missing = [r for r in template["requirements"] if r not in variables]
        if missing:
            print(f"⚠️ AFE: Missing template vars for {root_cause}: {missing}")
            return None
        
        # Fill template
        try:
            patch_code = template["template"].format(**variables)
            
            summary = self._generate_summary(root_cause, variables)
            
            return AFECandidate(
                detection_id=detection_id,
                type="code_patch",
                summary=summary,
                diff=f"""# {template["patch_type"].upper()} at line {variables.get('lineno', '?')}:
{patch_code}""",
                confidence=rca.confidence,
                status="pending",
                validation_results={
                    "patch_type": template["patch_type"],
                    "target_lineno": variables.get("lineno", 0),
                    "template_based": True,
                    "strategy": "constraint"
                }
            )
        except KeyError as e:
            print(f"⚠️ AFE: Template key error: {e}")
            return None

    def _generate_defensive_wrap(
        self,
        root_cause: str,
        rca: RCAResult,
        detection_id: str
    ) -> Optional[AFECandidate]:
        """Generate a generic try/except defensive wrap."""
        vars = rca.variables
        if "original_line" not in vars or "exception_type" not in vars:
            return None

        # Map root cause to Exception class if not already in vars
        # (Though exception_type should be there from RCA)
        exc_type = vars.get("exception_type", "Exception")
        
        # Avoid wrapping if template IS ALREADY a wrap (e.g. network failure)
        tpl = PATCH_TEMPLATES.get(root_cause)
        if tpl and tpl.get("patch_type") == "wrap":
            return None
        
        patch_code = f"""try:
    {vars['original_line']}
except {exc_type} as e:
    # Auto-generated defensive wrap
    raise {exc_type}(f"Rescued {{e}} in safe block")"""
    
        return AFECandidate(
            detection_id=detection_id,
            type="code_patch",
            summary=f"Wrap operation in try/except {exc_type}",
            diff=f"""# WRAP at line {vars.get('lineno', '?')}:
{patch_code}""",
            confidence=0.8, # Slightly lower confidence than specific constraint
            status="pending",
            validation_results={
                "patch_type": "wrap",
                "target_lineno": vars.get("lineno", 0),
                "template_based": True,
                "strategy": "defensive"
            }
        )

    def _generate_summary(self, root_cause: str, variables: dict) -> str:
        """Generate human-readable summary for the fix."""
        summaries = {
            "division_by_zero": f"Add zero-check for `{variables.get('denominator', 'divisor')}`",
            "missing_key": f"Add key existence check for `{variables.get('key', 'key')}`",
            "type_mismatch": f"Add None check for `{variables.get('var_name', 'variable')}`",
            "index_out_of_bounds": f"Add bounds check for `{variables.get('sequence', 'list')}`",
            "attribute_error": f"Add None check before accessing `.{variables.get('attribute', 'attr')}`",
            "file_not_found": f"Add file existence check for `{variables.get('filepath', 'path')}`",
            "network_failure": "Add retry with exponential backoff",
        }
        return summaries.get(root_cause, f"Fix for {root_cause}")

    def _generate_manual_intervention(
        self, 
        root: str, 
        rca: RCAResult, 
        detection_id: str
    ) -> List[AFECandidate]:
        """Generate manual intervention fallback."""
        tpl = self.env.get_template("manual_intervention.md.j2")
        context = rca.variables.copy()
        if "root_cause" not in context:
            context["root_cause"] = root
            
        diff = tpl.render(**context)
        
        return [
            AFECandidate(
                detection_id=detection_id,
                type="code_patch",
                summary=f"Manual fix required for root cause: {root}",
                diff=diff,
                confidence=0.4,
                status="pending",
            )
        ]

    # -------------------------------------------------------------------
    # Timeout Fix
    # -------------------------------------------------------------------

    def _generate_timeout_fix(self, rca: RCAResult, detection_id: str):
        tpl = self.env.get_template("retry_policy.json.j2")
        diff = tpl.render(**rca.variables)

        return [
            AFECandidate(
                detection_id=detection_id,
                type="retry_policy",
                summary="Update retry policy for timeouts",
                diff=diff,
                confidence=rca.confidence,
                status="pending",
            )
        ]

    # -------------------------------------------------------------------
    # Rate Limit Fixes
    # -------------------------------------------------------------------

    def _generate_rate_limit_fixes(self, rca: RCAResult, detection_id: str):
        tpl = self.env.get_template("rate_limit.py.j2")
        # Ensure function_name is present for StrictUndefined
        context = rca.variables.copy()
        if "function_name" not in context:
            context["function_name"] = "api_call"
            
        diff = tpl.render(**context)

        return [
            AFECandidate(
                detection_id=detection_id,
                type="code_patch",
                summary="Add exponential backoff retry logic",
                diff=diff,
                confidence=rca.confidence,
                status="pending",
            )
        ]

    # -------------------------------------------------------------------
    # Context Window Fixes
    # -------------------------------------------------------------------

    def _generate_context_fixes(self, rca: RCAResult, detection_id: str):
        fixes = []

        # Fix 1: Model upgrade + truncate
        tpl = self.env.get_template("missing_context.json.j2")
        conf = tpl.render(**rca.variables)

        fixes.append(
            AFECandidate(
                detection_id=detection_id,
                type="config_change",
                summary=f"Upgrade model to {rca.variables.get('suggested_model')}",
                diff=conf,
                confidence=rca.confidence,
                status="pending",
            )
        )

        # Fix 2: Add summarization strategy
        tpl2 = self.env.get_template("context_summarize.py.j2")
        diff2 = tpl2.render(limit=rca.variables.get("limit"))

        fixes.append(
            AFECandidate(
                detection_id=detection_id,
                type="code_patch",
                summary="Insert summarization step before model call",
                diff=diff2,
                confidence=rca.confidence * 0.85,
                status="pending",
            )
        )

        return fixes

    # -------------------------------------------------------------------
    # JSON Fix
    # -------------------------------------------------------------------

    def _generate_json_fix(self, rca: RCAResult, detection_id: str):
        tpl = self.env.get_template("json_retry.py.j2")
        diff = tpl.render()

        return [
            AFECandidate(
                detection_id=detection_id,
                type="code_patch",
                summary="Retry with JSON mode enabled",
                diff=diff,
                confidence=0.8,
                status="pending",
            )
        ]

    # -------------------------------------------------------------------
    # Bad Model Config Fix
    # -------------------------------------------------------------------

    def _generate_model_config_fix(self, rca: RCAResult, detection_id: str):
        tpl = self.env.get_template("invalid_model_config.json.j2")
        diff = tpl.render(**rca.variables)

        return [
            AFECandidate(
                detection_id=detection_id,
                type="config_change",
                summary="Correct invalid model capabilities",
                diff=diff,
                confidence=rca.confidence,
                status="pending",
            )
        ]

    # -------------------------------------------------------------------
    # Tool Call Fix
    # -------------------------------------------------------------------

    def _generate_tool_fix(self, rca: RCAResult, detection_id: str):
        tpl = self.env.get_template("tool_fix.py.j2")
        diff = tpl.render()

        return [
            AFECandidate(
                detection_id=detection_id,
                type="code_patch",
                summary="Fix malformed tool call payload",
                diff=diff,
                confidence=0.75,
                status="pending",
            )
        ]

    # -------------------------------------------------------------------
    # Model Refusal Fix
    # -------------------------------------------------------------------

    def _generate_refusal_fix(self, rca: RCAResult, detection_id: str):
        tpl = self.env.get_template("refusal_prompt_patch.j2")
        diff = tpl.render()

        return [
            AFECandidate(
                detection_id=detection_id,
                type="prompt_patch",
                summary="Rewrite prompt to avoid safety refusal",
                diff=diff,
                confidence=0.7,
                status="pending",
            )
        ]
