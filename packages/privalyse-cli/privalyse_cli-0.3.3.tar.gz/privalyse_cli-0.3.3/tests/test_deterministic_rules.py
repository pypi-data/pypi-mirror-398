import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from privalyse_scanner.utils.deterministic_rules import DeterministicClassifier

class TestDeterministicRules(unittest.TestCase):
    def setUp(self):
        self.classifier = DeterministicClassifier()
        self.test_cases = [
            {
                "snippet": 'user_email = "test@example.com"',
                "context": "user registration",
                "expected_pii": "email"
            },
            {
                "snippet": 'password = request.form.get("password")',
                "context": "login handler",
                "expected_pii": "password"
            },
            {
                "snippet": 'logger.info("Health check passed")',
                "context": "system monitoring",
                "expected_pii": None
            }
        ]

    def test_classification(self):
        for test in self.test_cases:
            result = self.classifier.classify_snippet(test["snippet"], test["context"])
            if test["expected_pii"]:
                self.assertIn(test["expected_pii"], result["pii_types"], 
                             f"Failed to detect {test['expected_pii']} in '{test['snippet']}'")
            else:
                self.assertEqual(len(result["pii_types"]), 0, 
                                f"False positive in '{test['snippet']}'")

if __name__ == '__main__':
    unittest.main()
