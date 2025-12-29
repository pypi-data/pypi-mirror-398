import unittest
import os
import shutil
import tempfile
from agenttrace.afe.validator import SandboxValidator
from agenttrace.afe.models import AFECandidate
from agenttrace.afe.patcher import ApplyEngine

class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = SandboxValidator()
        self.patcher = ApplyEngine()

    def test_patch_application(self):
        source = """
def hello():
    print("Hello World")
"""
        patch = """
def hello():
    print("Hello Patched")
"""
        candidate = AFECandidate(
            detection_id="1",
            type="code_patch",
            summary="Fix hello",
            diff=patch,
            confidence=1.0
        )
        
        new_source = self.patcher.apply_patch(source, candidate)
        self.assertIn("Hello Patched", new_source)
        self.assertNotIn("Hello World", new_source)

    def test_validator_execution(self):
        # A script that fails by default
        script_fail = """
import sys
def main():
    raise Exception("Original Error")

if __name__ == "__main__":
    main()
"""
        # A patch that fixes it
        patch_fix = """
def main():
    print("Fixed!")
    sys.exit(0)
"""
        candidate = AFECandidate(
            detection_id="2",
            type="code_patch",
            summary="Fix main",
            diff=patch_fix,
            confidence=1.0
        )
        
        # Validate
        result = self.validator.validate(candidate, "trace_1", script_fail)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("Fixed!", result["stdout"])

if __name__ == '__main__':
    unittest.main()
