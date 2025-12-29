import unittest
from agenttrace.afe.models import AFEDetection, RCAResult, AFECandidate
from agenttrace.afe.rca import RCAEngine
from agenttrace.afe.generator import CandidateGenerator

class TestRCA(unittest.TestCase):
    def setUp(self):
        self.rca_engine = RCAEngine()
        self.generator = CandidateGenerator()

    def test_rate_limit_analysis(self):
        detection = AFEDetection(
            id="det_123",
            job_id="job_123",
            trace_id="trace_123",
            failure_type="rate_limit"
        )
        error_details = "Error: 429 Too Many Requests. Retry after 30 seconds."
        
        # 1. RCA Analysis
        result = self.rca_engine.analyze(detection, error_details)
        
        self.assertEqual(result.root_cause, "rate_limit_exceeded")
        self.assertEqual(result.variables["wait_time"], 30)
        self.assertEqual(result.confidence, 0.9)
        
        # 2. Candidate Generation
        candidates = self.generator.generate(result, detection.id)
        
        self.assertTrue(len(candidates) > 0)
        candidate = candidates[0]
        
        self.assertEqual(candidate.type, "code_patch")
        self.assertIn("time.sleep", candidate.diff)
        self.assertIn("base_delay = 30", candidate.diff)

    def test_missing_context_analysis(self):
        detection = AFEDetection(
            id="det_456",
            job_id="job_456",
            trace_id="trace_456",
            failure_type="missing_context"
        )
        error_details = "context length exceeded. Limit: 4096, Actual: 5000"
        
        # 1. RCA Analysis
        result = self.rca_engine.analyze(detection, error_details)
        
        self.assertEqual(result.root_cause, "context_window_exceeded")
        self.assertEqual(result.variables["limit"], 4096)
        self.assertEqual(result.variables["actual"], 5000)
        self.assertEqual(result.variables["suggested_model"], "gpt-4-32k")
        
        # 2. Candidate Generation
        candidates = self.generator.generate(result, detection.id)
        
        # Expecting 2 candidates (Config change + Summarization)
        self.assertEqual(len(candidates), 2)
        
        # Check Config Change
        config_candidate = next(c for c in candidates if c.type == "config_change")
        self.assertIn('"model": "gpt-4-32k"', config_candidate.diff)
        
        # Check Summarization Code Patch
        code_candidate = next(c for c in candidates if c.type == "code_patch")
        self.assertIn("def summarize_context", code_candidate.diff)

    def test_timeout_analysis(self):
        detection = AFEDetection(
            id="det_789",
            job_id="job_789",
            trace_id="trace_789",
            failure_type="timeout"
        )
        error_details = "Request timed out after 60000ms"
        
        # 1. RCA Analysis
        result = self.rca_engine.analyze(detection, error_details)
        
        self.assertEqual(result.root_cause, "request_timeout")
        
        # 2. Candidate Generation
        candidates = self.generator.generate(result, detection.id)
        
        self.assertTrue(len(candidates) > 0)
        candidate = candidates[0]
        
        self.assertEqual(candidate.type, "retry_policy")
        self.assertIn('"mode": "exponential_backoff"', candidate.diff)

if __name__ == '__main__':
    unittest.main()
