import unittest
import ast
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from privalyse_scanner.analyzers.security_analyzer import SecurityAnalyzer
from privalyse_scanner.models.finding import Severity

class TestSecurityAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SecurityAnalyzer()
        self.file_path = Path("test_app.py")

    def test_http_plain_detection(self):
        code = """
def connect():
    url = "http://example.com/api"
    requests.get(url)
"""
        findings = self.analyzer.analyze_file(self.file_path, code)
        
        self.assertTrue(any(f.rule == "HTTP_PLAIN" for f in findings))
        finding = next(f for f in findings if f.rule == "HTTP_PLAIN")
        self.assertEqual(finding.severity, Severity.MEDIUM)
        self.assertIn("http://example.com/api", finding.snippet)

    def test_https_ignored(self):
        code = """
def connect():
    url = "https://example.com/api"
    requests.get(url)
"""
        findings = self.analyzer.analyze_file(self.file_path, code)
        self.assertFalse(any(f.rule == "HTTP_PLAIN" for f in findings))

    def test_localhost_ignored(self):
        code = """
def connect():
    url = "http://localhost:8080"
    requests.get(url)
"""
        findings = self.analyzer.analyze_file(self.file_path, code)
        self.assertFalse(any(f.rule == "HTTP_PLAIN" for f in findings))

    def test_missing_security_headers(self):
        code = """
@app.route('/')
def index():
    response = make_response("Hello")
    # Missing headers
    return response
"""
        # Note: The analyzer looks for specific patterns of header setting.
        # If the code doesn't explicitly set headers, it might not trigger unless it sees a response object being manipulated.
        # Let's try a case where headers ARE set but security ones are missing.
        code_with_headers = """
@app.route('/')
def index():
    response = make_response("Hello")
    response.headers['Content-Type'] = 'text/html'
    return response
"""
        findings = self.analyzer.analyze_file(self.file_path, code_with_headers)
        # We expect findings for missing X-Frame-Options, etc.
        self.assertTrue(any(f.rule == "HEADER_XFRAME_MISSING" for f in findings))
        self.assertTrue(any(f.rule == "HEADER_CSP_MISSING" for f in findings))

    def test_insecure_cookie(self):
        code = """
def set_cookie(resp):
    resp.set_cookie('session', '123', httponly=False, secure=False)
"""
        findings = self.analyzer.analyze_file(self.file_path, code)
        self.assertTrue(any(f.rule == "COOKIE_INSECURE" for f in findings))
        self.assertTrue(any(f.rule == "COOKIE_NO_HTTPONLY" for f in findings))

    def test_secure_cookie(self):
        code = """
def set_cookie(resp):
    resp.set_cookie('session', '123', httponly=True, secure=True)
"""
        findings = self.analyzer.analyze_file(self.file_path, code)
        self.assertFalse(any(f.rule == "COOKIE_INSECURE" for f in findings))
        self.assertFalse(any(f.rule == "COOKIE_NO_HTTPONLY" for f in findings))

    def test_cors_wildcard(self):
        code = """
CORS(app, resources={r"/*": {"origins": "*"}})
"""
        findings = self.analyzer.analyze_file(self.file_path, code)
        self.assertTrue(any(f.rule == "CORS_WILDCARD" for f in findings))

if __name__ == '__main__':
    unittest.main()
