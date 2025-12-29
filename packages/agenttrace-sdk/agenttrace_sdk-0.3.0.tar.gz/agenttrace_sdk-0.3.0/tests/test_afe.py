import unittest
from unittest.mock import MagicMock
from agenttrace.afe.classifier import FailureClassifier
from agenttrace.afe.detector import AFEDetector

class TestAFE(unittest.TestCase):
    def test_classifier_rate_limit(self):
        error = "Error: 429 Too Many Requests"
        ftype, conf = FailureClassifier.classify(error)
        self.assertEqual(ftype, "rate_limit")
        self.assertEqual(conf, 1.0)

    def test_classifier_missing_context(self):
        error = "openai.error.InvalidRequestError: This model's maximum context length is 4097 tokens"
        ftype, conf = FailureClassifier.classify(error)
        self.assertEqual(ftype, "missing_context")

    def test_classifier_unknown(self):
        error = "Some random error occurred"
        ftype, conf = FailureClassifier.classify(error)
        self.assertEqual(ftype, "unknown_error")
        self.assertEqual(conf, 0.5)

    def test_detector_integration(self):
        mock_supabase = MagicMock()
        detector = AFEDetector(mock_supabase)
        
        detector.detect_failure("job-123", "trace-456", "Connection refused")
        
        # Verify insert was called on correct table
        mock_supabase.table.assert_called_with("afe_detections")
        mock_supabase.table().insert.assert_called()
        
        # Check args
        args = mock_supabase.table().insert.call_args[0][0]
        self.assertEqual(args['job_id'], "job-123")
        self.assertEqual(args['failure_type'], "external_api_failure")

if __name__ == '__main__':
    unittest.main()
