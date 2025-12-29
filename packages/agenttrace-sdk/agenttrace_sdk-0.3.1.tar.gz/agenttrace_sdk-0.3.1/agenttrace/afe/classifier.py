import re
from typing import Tuple

class FailureClassifier:
    """
    Classifies failure events based on error messages and exception traces.
    """

    PATTERNS = [
        (r"Rate limit exceeded", "rate_limit"),
        (r"429 Too Many Requests", "rate_limit"),
        (r"context length exceeded", "missing_context"),
        (r"maximum context length", "missing_context"),
        (r"Authentication failed", "auth_error"),
        (r"401 Unauthorized", "auth_error"),
        (r"403 Forbidden", "auth_error"),
        (r"JSONDecodeError", "malformed_response"),
        (r"Expecting value", "malformed_response"),
        (r"Connection refused", "external_api_failure"),
        (r"Timeout", "external_api_failure"),
    ]

    @classmethod
    def classify(cls, error_details: str) -> Tuple[str, float]:
        """
        Returns (failure_type, confidence)
        """
        for pattern, failure_type in cls.PATTERNS:
            if re.search(pattern, error_details, re.IGNORECASE):
                return failure_type, 1.0
        
        return "unknown_error", 0.5
