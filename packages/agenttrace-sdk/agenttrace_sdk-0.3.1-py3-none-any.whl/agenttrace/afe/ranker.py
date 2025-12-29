"""
Patch Ranking Engine for AFE v2

Ranks candidates using multi-factor scoring:
- Confidence from RCA/LLM
- Edit distance (prefer minimal changes)
- Validation success
- Pattern match (prefer template over fallback)
- Quality (no forbidden patterns)
"""

from typing import List
from .models import AFECandidate


class PatchRanker:
    """
    Ranks AFE candidates using multi-factor weighted scoring.
    """
    
    # Scoring weights
    WEIGHTS = {
        "confidence": 0.30,
        "edit_distance": 0.15,
        "validation_success": 0.25,
        "pattern_match": 0.15,
        "no_forbidden": 0.10,
        "specificity": 0.05,
    }
    
    # Forbidden patterns that indicate low quality
    FORBIDDEN_PATTERNS = [
        "except Exception:",
        "except Exception as e:",
        "except:",
        "print(e)",
        'print(f"An error occurred',
        "pass  # TODO",
    ]
    
    def rank(self, candidates: List[AFECandidate]) -> List[AFECandidate]:
        """
        Rank candidates by quality score.
        
        Args:
            candidates: List of AFE candidates
            
        Returns:
            Sorted list with highest quality first
        """
        if not candidates:
            return []
        
        scored = []
        for candidate in candidates:
            score = self._compute_score(candidate)
            scored.append((score, candidate))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Update candidates with their rank scores
        for i, (score, candidate) in enumerate(scored):
            if candidate.validation_results is None:
                candidate.validation_results = {}
            candidate.validation_results["rank_score"] = round(score, 3)
            candidate.validation_results["rank"] = i + 1
        
        return [c for _, c in scored]
    
    def _compute_score(self, candidate: AFECandidate) -> float:
        """Compute weighted quality score for a candidate."""
        scores = {
            "confidence": self._score_confidence(candidate),
            "edit_distance": self._score_edit_distance(candidate),
            "validation_success": self._score_validation(candidate),
            "pattern_match": self._score_pattern_match(candidate),
            "no_forbidden": self._score_no_forbidden(candidate),
            "specificity": self._score_specificity(candidate),
        }
        
        total = sum(self.WEIGHTS[k] * scores[k] for k in self.WEIGHTS)
        return total
    
    def _score_confidence(self, candidate: AFECandidate) -> float:
        """Score based on RCA/LLM confidence."""
        return min(candidate.confidence, 1.0)
    
    def _score_edit_distance(self, candidate: AFECandidate) -> float:
        """Score inversely proportional to patch size (prefer minimal edits)."""
        diff_len = len(candidate.diff) if candidate.diff else 0
        # Normalize: 0-100 chars = 1.0, 500+ chars = 0.0
        if diff_len <= 100:
            return 1.0
        elif diff_len >= 500:
            return 0.0
        else:
            return 1.0 - (diff_len - 100) / 400
    
    def _score_validation(self, candidate: AFECandidate) -> float:
        """Score based on validation results."""
        if not candidate.validation_results:
            return 0.5  # Unknown
        
        success = candidate.validation_results.get("success", None)
        if success is True:
            return 1.0
        elif success is False:
            return 0.0
        else:
            return 0.5
    
    def _score_pattern_match(self, candidate: AFECandidate) -> float:
        """Score based on whether this came from a known pattern."""
        # Template-based fixes are more reliable than LLM fallback
        if candidate.type == "code_patch":
            # Check if it has structured metadata from template
            if candidate.validation_results:
                if candidate.validation_results.get("patch_type") in ["prepend", "replace", "wrap"]:
                    return 1.0
        
        # Manual intervention = lowest
        if candidate.type == "manual_intervention":
            return 0.0
        
        return 0.7
    
    def _score_no_forbidden(self, candidate: AFECandidate) -> float:
        """Score 0 if contains forbidden patterns, 1 otherwise."""
        if not candidate.diff:
            return 0.5
        
        diff_lower = candidate.diff.lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern.lower() in diff_lower:
                return 0.0
        
        return 1.0
    
    def _score_specificity(self, candidate: AFECandidate) -> float:
        """Score based on how specific the fix is."""
        if not candidate.diff:
            return 0.0
        
        # Look for specific variable names (not generic placeholders)
        specific_indicators = [
            "if ", "elif ", "raise ", "isinstance(", 
            ".get(", " not in ", " in ", "len(",
        ]
        
        count = sum(1 for ind in specific_indicators if ind in candidate.diff)
        return min(count / 3, 1.0)  # Normalize to 0-1
    
    def get_best_candidate(self, candidates: List[AFECandidate]) -> AFECandidate | None:
        """Get the highest-ranked candidate."""
        ranked = self.rank(candidates)
        return ranked[0] if ranked else None
    
    def filter_low_quality(self, candidates: List[AFECandidate], min_score: float = 0.3) -> List[AFECandidate]:
        """Filter out candidates below a quality threshold."""
        ranked = self.rank(candidates)
        return [c for c in ranked if c.validation_results.get("rank_score", 0) >= min_score]
