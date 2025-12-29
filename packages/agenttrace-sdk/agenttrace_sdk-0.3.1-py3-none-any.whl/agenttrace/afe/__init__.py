"""
AutoFix Engine (AFE) - Core Module v2

Enhanced with:
- Exception-specific analyzers
- Constraint-based templates
- Strict LLM prompts
- Patch ranking
"""

from .detector import AFEDetector
from .classifier import FailureClassifier
from .models import AFEDetection, AFECandidate, RCAResult
from .extractor import ExceptionExtractor, ExceptionContext
from .rca import RCAEngine
from .generator import CandidateGenerator
from .ranker import PatchRanker
from .diff_engine import DiffEngine, AFEPatch

__all__ = [
    "AFEDetector",
    "FailureClassifier",
    "AFEDetection",
    "AFECandidate",
    "RCAResult",
    "ExceptionExtractor",
    "ExceptionContext",
    "RCAEngine",
    "CandidateGenerator",
    "PatchRanker",
    "DiffEngine",
    "AFEPatch",
]
