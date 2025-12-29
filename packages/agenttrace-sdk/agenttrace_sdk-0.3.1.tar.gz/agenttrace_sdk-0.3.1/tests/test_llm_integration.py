import unittest
from unittest.mock import MagicMock, patch
import json
import os
from agenttrace.afe.detector import AFEDetector
from agenttrace.afe.models import RCAResult, AFECandidate

class TestLLMIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_supabase = MagicMock()
        self.detector = AFEDetector(self.mock_supabase)
        
        # Mock Groq client inside generator
        self.detector.generator.llm.client = MagicMock()
        
        # Mock Supabase insert responses
        self.mock_supabase.table().insert().execute().data = [{"id": "det_123"}]

    @patch("agenttrace.afe.detector.os.path.exists")
    @patch("builtins.open")
    def test_llm_fallback(self, mock_open, mock_exists):
        # 1. Setup Mock Trace
        mock_exists.return_value = True
        trace_content = json.dumps({"type": "step", "name": "step1", "status": "failed", "error": "Unknown logic error"})
        mock_open.return_value.__enter__.return_value = [trace_content]
        
        # 2. Setup LLM Response
        llm_response = {
            "type": "code_patch",
            "summary": "Fix logic error",
            "diff": "def fix(): pass",
            "confidence": 0.85,
            "reasoning": "Logic error detected"
        }
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = json.dumps(llm_response)
        self.detector.generator.llm.client.chat.completions.create.return_value = mock_completion

        # 3. Trigger Detection with Unknown Error
        self.detector.detect_failure("job_1", "trace_1", "Unknown logic error")
        
        # 4. Verify RCA (should be unknown_error or similar)
        # 5. Verify LLM Call
        self.detector.generator.llm.client.chat.completions.create.assert_called_once()
        
        # 6. Verify Candidate Storage
        # Check that afe_candidates insert was called
        # We need to get the mock object for table("afe_candidates").insert
        # Since table() is called with an arg, we need to inspect the return value of that specific call
        
        # Get the mock that was returned by table("afe_candidates")
        table_mock = self.mock_supabase.table.return_value
        insert_mock = table_mock.insert
        
        self.assertTrue(insert_mock.called)
        call_args = insert_mock.call_args
        inserted_candidate = call_args[0][0]
        
        self.assertEqual(inserted_candidate["summary"], "Fix logic error")
        self.assertEqual(inserted_candidate["type"], "code_patch")

if __name__ == '__main__':
    unittest.main()
