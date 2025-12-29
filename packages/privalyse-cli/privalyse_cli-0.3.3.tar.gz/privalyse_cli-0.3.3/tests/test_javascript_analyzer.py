import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from privalyse_scanner.analyzers.javascript_analyzer import JavaScriptAnalyzer

class TestJavaScriptAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = JavaScriptAnalyzer()
        self.file_path = Path("test_app.js")

    def test_hardcoded_secret_detection(self):
        code = """
const apiKey = "sk_live_DUMMY_TEST_KEY_1234567890abcdef";
let password = "superSecretPassword123";
"""
        findings, _ = self.analyzer.analyze_file(self.file_path, code)
        
        self.assertTrue(any(f.rule == "HARDCODED_SECRET" for f in findings))
        
        # Check for specific secrets
        # Filter by rule to avoid confusion with FORM_FIELD_PASSWORD findings
        api_key_finding = next((f for f in findings if "apiKey" in f.snippet and f.rule == "HARDCODED_SECRET"), None)
        self.assertIsNotNone(api_key_finding)
        self.assertEqual(api_key_finding.classification.confidence, 1.0) # High entropy

        password_finding = next((f for f in findings if "password" in f.snippet and f.rule == "HARDCODED_SECRET"), None)
        self.assertIsNotNone(password_finding)
        # The password "superSecretPassword123" is > 8 chars and matches name pattern.
        # It is NOT high entropy (len < 32).
        # So it should be 0.6.
        self.assertEqual(password_finding.classification.confidence, 0.6)

    def test_ignore_placeholders(self):
        code = """
const apiKey = "your_api_key_here";
"""
        findings, _ = self.analyzer.analyze_file(self.file_path, code)
        self.assertFalse(any(f.rule == "HARDCODED_SECRET" for f in findings))

if __name__ == '__main__':
    unittest.main()
