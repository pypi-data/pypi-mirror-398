from typing import List
from .models import AFECandidate

class PolicyEngine:
    """
    Determines which candidate is the best fix and whether it should be auto-applied.
    """

    # Types that are generally safe to auto-apply if verified
    SAFE_TYPES = {
        "retry_policy",
        "json_mode_retry",
        "context_window_config",
        "model_config_fix"
    }

    def rank_candidates(self, candidates: List[AFECandidate]) -> List[AFECandidate]:
        """
        Ranks candidates based on:
        1. Validation Status (verified > pending > failed)
        2. Confidence (Higher is better)
        3. Source/Type (Templates > LLM, Config > Code) - implicitly handled by confidence usually, 
           but we can add explicit tie-breaking.
        """
        def sort_key(c: AFECandidate):
            # 1. Status Score
            status_score = 0
            if c.status == "verified":
                status_score = 2
            elif c.status == "pending":
                status_score = 1
            
            # 2. Confidence
            conf = c.confidence
            
            # 3. Risk Penalty (Optional, tie-breaker)
            # Prefer config changes over code patches if confidence is equal
            risk_penalty = 0
            if c.type == "code_patch":
                risk_penalty = 0.05
            
            return (status_score, conf - risk_penalty)

        # Sort descending
        return sorted(candidates, key=sort_key, reverse=True)

    def should_auto_apply(self, candidate: AFECandidate) -> bool:
        """
        Determines if a candidate is safe for automated application.
        Policy:
        - Must be VERIFIED.
        - Confidence >= 0.9.
        - Type must be in SAFE_TYPES.
        """
        if candidate.status != "verified":
            return False
        
        if candidate.confidence < 0.9:
            return False
            
        # For now, be conservative with code patches
        if candidate.type not in self.SAFE_TYPES:
            # Exceptions for specific high-confidence templates can be added here
            return False
            
        return True
