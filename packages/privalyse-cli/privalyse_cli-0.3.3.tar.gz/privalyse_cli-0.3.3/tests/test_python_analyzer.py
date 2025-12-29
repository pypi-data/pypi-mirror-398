import unittest
import ast
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from privalyse_scanner.analyzers.python_analyzer import PythonAnalyzer, is_likely_secret
from privalyse_scanner.models.finding import Severity

class TestPythonAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PythonAnalyzer()
        self.file_path = Path("test_secrets.py")

    def test_hardcoded_secret_detection(self):
        code = """
API_KEY = "sk_live_DUMMY_TEST_KEY_1234567890abcdef"
"""
        findings, _ = self.analyzer.analyze_file(self.file_path, code)
        self.assertTrue(any(f.rule == "HARDCODED_SECRET" for f in findings))

    def test_placeholder_secret_ignored(self):
        code = """
API_KEY = "your_api_key_here"
"""
        findings, _ = self.analyzer.analyze_file(self.file_path, code)
        self.assertFalse(any(f.rule == "HARDCODED_SECRET" for f in findings))

    def test_short_string_ignored(self):
        code = """
API_KEY = "123"
"""
        findings, _ = self.analyzer.analyze_file(self.file_path, code)
        self.assertFalse(any(f.rule == "HARDCODED_SECRET" for f in findings))

    def test_is_likely_secret_function(self):
        # Test the helper function directly
        secret_type, confidence = is_likely_secret("api_key", "sk_live_1234567890")
        self.assertEqual(secret_type, "api_key")
        self.assertEqual(confidence, 0.6)
        
        secret_type, confidence = is_likely_secret("api_key", "todo")
        self.assertIsNone(secret_type)
        
        secret_type, confidence = is_likely_secret("username", "admin")
        self.assertIsNone(secret_type)
        
        # High entropy check
        # The regex is r'^[A-Za-z0-9+/=_-]{32,}$' which matches alphanumeric strings > 32 chars
        secret_type, confidence = is_likely_secret("random_var", "a" * 32)
        self.assertEqual(secret_type, "token")
        self.assertEqual(confidence, 0.9)

if __name__ == '__main__':
    unittest.main()
