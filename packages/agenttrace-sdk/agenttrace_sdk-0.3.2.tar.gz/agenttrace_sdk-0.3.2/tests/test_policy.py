import unittest
from agenttrace.afe.policy import PolicyEngine
from agenttrace.afe.models import AFECandidate

class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyEngine()

    def test_ranking(self):
        c1 = AFECandidate(id="1", detection_id="d1", type="code_patch", summary="Fix 1", diff="", confidence=0.8, status="pending")
        c2 = AFECandidate(id="2", detection_id="d1", type="retry_policy", summary="Fix 2", diff="", confidence=0.95, status="verified")
        c3 = AFECandidate(id="3", detection_id="d1", type="manual", summary="Fix 3", diff="", confidence=0.5, status="failed")
        c4 = AFECandidate(id="4", detection_id="d1", type="code_patch", summary="Fix 4", diff="", confidence=0.95, status="verified")

        # Expected order:
        # 1. c2 (Verified, 0.95, Safe/Config)
        # 2. c4 (Verified, 0.95, Code Patch - slightly lower due to risk penalty)
        # 3. c1 (Pending, 0.8)
        # 4. c3 (Failed)

        ranked = self.engine.rank_candidates([c1, c2, c3, c4])
        
        self.assertEqual(ranked[0].id, "2")
        self.assertEqual(ranked[1].id, "4")
        self.assertEqual(ranked[2].id, "1")
        self.assertEqual(ranked[3].id, "3")

    def test_auto_apply(self):
        # Safe and Verified
        c1 = AFECandidate(id="1", detection_id="d1", type="retry_policy", summary="Fix 1", diff="", confidence=0.95, status="verified")
        self.assertTrue(self.engine.should_auto_apply(c1))

        # Verified but Low Confidence
        c2 = AFECandidate(id="2", detection_id="d1", type="retry_policy", summary="Fix 2", diff="", confidence=0.8, status="verified")
        self.assertFalse(self.engine.should_auto_apply(c2))

        # Verified, High Confidence, but Unsafe Type (Code Patch)
        c3 = AFECandidate(id="3", detection_id="d1", type="code_patch", summary="Fix 3", diff="", confidence=0.95, status="verified")
        self.assertFalse(self.engine.should_auto_apply(c3))

        # Pending
        c4 = AFECandidate(id="4", detection_id="d1", type="retry_policy", summary="Fix 4", diff="", confidence=0.95, status="pending")
        self.assertFalse(self.engine.should_auto_apply(c4))

if __name__ == '__main__':
    unittest.main()
