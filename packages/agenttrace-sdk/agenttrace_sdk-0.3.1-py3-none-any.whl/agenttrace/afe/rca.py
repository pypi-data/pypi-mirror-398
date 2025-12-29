import re
from typing import Dict, Any, Optional, List
from .models import AFEDetection, RCAResult
from .extractor import ExceptionContext


class RCAEngine:
    """
    Production-grade RCA engine with exception-specific analyzers.
    Uses multi-signal rule matching + weighted scoring + structured variable extraction.
    """
    
    # Exception-specific analyzers
    EXCEPTION_ANALYZERS = {
        "ZeroDivisionError": "_analyze_zero_division",
        "KeyError": "_analyze_key_error",
        "TypeError": "_analyze_type_error",
        "ValueError": "_analyze_value_error",
        "IndexError": "_analyze_index_error",
        "AttributeError": "_analyze_attribute_error",
        "FileNotFoundError": "_analyze_file_not_found",
        "JSONDecodeError": "_analyze_json_error",
        "ConnectionError": "_analyze_network_error",
        "TimeoutError": "_analyze_timeout_error",
        "RuntimeError": "_analyze_runtime_error",
        "RecursionError": "_analyze_runtime_error",
    }

    # ... (analyze method stays same)

    def analyze(self, detection: AFEDetection, error_details: str, ctx: ExceptionContext = None) -> RCAResult:
        """
        Analyze detection and return structured RCA result.
        
        Args:
            detection: AFE detection object
            error_details: Raw error string
            ctx: Optional ExceptionContext for enhanced analysis
        """
        signals = []

        # 1. Check for exception-specific analyzer
        if ctx and ctx.exception_type in self.EXCEPTION_ANALYZERS:
            analyzer_name = self.EXCEPTION_ANALYZERS[ctx.exception_type]
            analyzer = getattr(self, analyzer_name, None)
            if analyzer:
                result = analyzer(ctx, error_details)
                if result:
                    return result

        # 2. Score the declared failure_type
        declared = self._score_declared_failure_type(detection.failure_type)
        if declared:
            signals.append(declared)

        # 3. Add pattern-based inferences
        signals.extend(self._pattern_rules(error_details))

        # 4. Use weighted ranking
        best = self._pick_best_cause(signals)

        return RCAResult(
            root_cause=best["cause"],
            variables=best["variables"],
            confidence=best["score"]
        )

    # =========================================================================
    # EXCEPTION-SPECIFIC ANALYZERS
    # =========================================================================

    def _analyze_zero_division(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze ZeroDivisionError with expression parsing."""
        variables = {
            "fix_strategy": "precondition_check",
            "exception_type": "ZeroDivisionError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(),
        }
        
        # Extract denominator from AST analysis
        if "denominator" in ctx.__dict__ or hasattr(ctx, 'operands'):
            expr_info = ctx.__dict__
            if "denominator" in expr_info:
                variables["denominator"] = expr_info["denominator"]
            elif ctx.operands and len(ctx.operands) >= 2:
                variables["denominator"] = ctx.operands[1]
                variables["numerator"] = ctx.operands[0]
        
        # Try to get actual value from locals
        denom_var = variables.get("denominator", "")
        if denom_var and denom_var in ctx.locals:
            variables["denominator_value"] = ctx.locals[denom_var]
        
        return RCAResult(
            root_cause="division_by_zero",
            variables=variables,
            confidence=0.95
        )
    
    def _analyze_key_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze KeyError with key extraction."""
        variables = {
            "fix_strategy": "key_existence_check",
            "exception_type": "KeyError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(),
        }
        
        # Extract missing key from error message
        key_match = re.search(r"KeyError: ['\"]?([^'\"]+)['\"]?", error)
        if key_match:
            variables["missing_key"] = key_match.group(1)
        
        # Extract from AST analysis
        if hasattr(ctx, 'operands') and ctx.operands:
            if len(ctx.operands) >= 2:
                variables["dict_name"] = ctx.operands[0]
                variables["key"] = ctx.operands[1].strip("'\"")
        
        return RCAResult(
            root_cause="missing_key",
            variables=variables,
            confidence=0.92
        )
    
    def _analyze_type_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze TypeError with operand detection."""
        variables = {
            "fix_strategy": "type_guard",
            "exception_type": "TypeError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(),
        }
        
        # Common patterns
        if "NoneType" in error:
            variables["issue"] = "none_value"
            variables["fix_strategy"] = "none_check"
        elif "unsupported operand" in error.lower():
            variables["issue"] = "operand_mismatch"
            # Extract types from error
            match = re.search(r"'(\w+)' and '(\w+)'", error)
            if match:
                variables["left_type"] = match.group(1)
                variables["right_type"] = match.group(2)
        elif "not callable" in error.lower():
            variables["issue"] = "not_callable"
        
        return RCAResult(
            root_cause="type_mismatch",
            variables=variables,
            confidence=0.88
        )
    
    def _analyze_value_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze ValueError with variable extraction."""
        variables = {
            "fix_strategy": "value_validation",
            "exception_type": "ValueError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(),  # REQUIRED by template
        }
        
        # Common patterns
        if "invalid literal" in error.lower():
            variables["issue"] = "invalid_conversion"
            # Try to extract variable from failing line "int(x)"
            # Regex for int(VAR) or float(VAR)
            match = re.search(r"\b(int|float)\s*\(\s*([a-zA-Z_]\w*)", ctx.failing_line)
            if match:
                variables["target_type"] = match.group(1)
                variables["var_name"] = match.group(2)
                variables["fix_strategy"] = "type_check_or_try_except"

        elif "not enough values" in error.lower():
            variables["issue"] = "unpacking_mismatch"
        elif "too many values" in error.lower():
            variables["issue"] = "unpacking_mismatch"
        
        return RCAResult(
            root_cause="invalid_value",
            variables=variables,
            confidence=0.85
        )

    def _analyze_index_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze IndexError with bounds detection."""
        variables = {
            "fix_strategy": "bounds_check",
            "exception_type": "IndexError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(),
        }
        
        # Extract from AST analysis
        if hasattr(ctx, 'operands') and ctx.operands:
            if len(ctx.operands) >= 2:
                variables["sequence"] = ctx.operands[0]
                variables["index"] = ctx.operands[1]
        
        return RCAResult(
            root_cause="index_out_of_bounds",
            variables=variables,
            confidence=0.90
        )
    
    def _analyze_attribute_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze AttributeError."""
        variables = {
            "fix_strategy": "attribute_check",
            "exception_type": "AttributeError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(),
        }
        
        # Extract attribute name
        match = re.search(r"has no attribute ['\"](\w+)['\"]", error)
        if match:
            variables["missing_attribute"] = match.group(1)
        
        # Check for NoneType
        if "NoneType" in error:
            variables["issue"] = "none_value"
            variables["fix_strategy"] = "none_check"
        
        # Extract from AST
        if hasattr(ctx, 'operands') and ctx.operands:
            if len(ctx.operands) >= 2:
                variables["object"] = ctx.operands[0]
                variables["attribute"] = ctx.operands[1]
        
        return RCAResult(
            root_cause="attribute_error",
            variables=variables,
            confidence=0.87
        )
    
    def _analyze_file_not_found(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze FileNotFoundError."""
        variables = {
            "fix_strategy": "file_existence_check",
            "exception_type": "FileNotFoundError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(),
        }
        
        # Extract filepath
        match = re.search(r"No such file or directory: ['\"]([^'\"]+)['\"]", error)
        if match:
            variables["filepath"] = match.group(1)
        
        return RCAResult(
            root_cause="file_not_found",
            variables=variables,
            confidence=0.93
        )
    
    def _analyze_json_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze JSONDecodeError."""
        variables = {
            "fix_strategy": "json_validation",
            "exception_type": "JSONDecodeError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "original_line": ctx.failing_line.strip(), # REQUIRED by template
        }
        
        return RCAResult(
            root_cause="json_decode_error",
            variables=variables,
            confidence=0.88
        )

    def _analyze_network_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze ConnectionError."""
        variables = {
            "fix_strategy": "retry_with_backoff",
            "exception_type": "ConnectionError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "max_retries": 3,
            "backoff_base": 2,
            "original_line": ctx.failing_line.strip(),
        }
        
        return RCAResult(
            root_cause="network_failure",
            variables=variables,
            confidence=0.85
        )
    
    def _analyze_timeout_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze TimeoutError."""
        variables = {
            "fix_strategy": "retry_with_backoff",
            "exception_type": "TimeoutError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
            "max_retries": 3,
            "backoff_base": 2,
            "original_line": ctx.failing_line.strip(),
        }
        
        # Map to network failure logic in generator
        return RCAResult(
            root_cause="network_failure", # Map to existing template
            variables=variables,
            confidence=0.82
        )

    def _analyze_runtime_error(self, ctx: ExceptionContext, error: str) -> RCAResult:
        """Analyze RuntimeError."""
        variables = {
            "fix_strategy": "error_handling",
            "exception_type": "RuntimeError",
            "lineno": ctx.lineno,
            "failing_line": ctx.failing_line,
            "function": ctx.function,
        }
        
        # Check for recursion
        if "maximum recursion depth exceeded" in error:
            variables["issue"] = "recursion_limit"
            variables["fix_strategy"] = "recursion_guard"
            return RCAResult(
                root_cause="recursion_error",
                variables=variables,
                confidence=0.95
            )
            
        return RCAResult(
            root_cause="runtime_error",
            variables=variables,
            confidence=0.7  # Moderate confidence for generic runtime error
        )

    # =========================================================================
    # LEGACY PATTERN MATCHING (fallback)
    # =========================================================================

    def _score_declared_failure_type(self, failure_type: str):
        mapping = {
            "rate_limit": ("rate_limit_exceeded", 0.7),
            "missing_context": ("context_window_exceeded", 0.6),
            "auth_error": ("invalid_api_key", 0.7),
            "malformed_response": ("json_decode_error", 0.6),
        }

        if failure_type in mapping:
            cause, score = mapping[failure_type]
            return {"cause": cause, "score": score, "variables": {}}

        return None

    def _pattern_rules(self, error: str) -> List[Dict]:
        rules = []

        # Rate limit
        if "rate limit" in error.lower() or "retry after" in error.lower():
            rules.append({
                "cause": "rate_limit_exceeded",
                "score": 0.9,
                "variables": self._extract_rate_limit_vars(error)
            })

        # Context window exceeded
        if "context length" in error.lower() or "context window" in error.lower():
            rules.append({
                "cause": "context_window_exceeded",
                "score": 0.9,
                "variables": self._extract_context_vars(error)
            })

        # JSON decode error
        if "json" in error.lower() and ("decode" in error.lower() or "parse" in error.lower()):
            rules.append({
                "cause": "json_decode_error",
                "score": 0.85,
                "variables": {"fix_type": "retry_with_json_mode"}
            })

        # Tool failures
        if "tool" in error.lower() or "function" in error.lower():
            rules.append({
                "cause": "tool_call_failure",
                "score": 0.8,
                "variables": {}
            })

        # Model refusal
        if "cannot assist" in error.lower() or "violate" in error.lower():
            rules.append({
                "cause": "model_refusal",
                "score": 0.75,
                "variables": {"fix_type": "rewrite_prompt_safely"}
            })

        # Invalid model config
        if "not support" in error.lower():
            rules.append({
                "cause": "invalid_model_config",
                "score": 0.8,
                "variables": {}
            })

        # Timeout
        if "timeout" in error.lower() or "timed out" in error.lower():
            rules.append({
                "cause": "request_timeout",
                "score": 0.7,
                "variables": {"retry": True}
            })

        return rules

    def _extract_rate_limit_vars(self, error: str):
        match = re.search(r"retry after (\d+)", error.lower())
        return {
            "wait_time": int(match.group(1)) if match else 60,
            "strategy": "exponential_backoff"
        }

    def _extract_context_vars(self, error: str):
        limit = 4096
        actual = 0

        limit_match = re.search(r'limit:? (\d+)', error, re.IGNORECASE)
        if limit_match:
            limit = int(limit_match.group(1))

        actual_match = re.search(r'actual:? (\d+)', error, re.IGNORECASE)
        if actual_match:
            actual = int(actual_match.group(1))

        return {
            "limit": limit,
            "actual": actual,
            "suggested_model": "gpt-4-32k" if actual > limit else "gpt-3.5-16k"
        }

    def _pick_best_cause(self, signals: List[Dict]) -> Dict:
        if not signals:
            return {
                "cause": "unknown_error",
                "variables": {},
                "score": 0.5
            }

        # Highest score wins
        return max(signals, key=lambda x: x["score"])
