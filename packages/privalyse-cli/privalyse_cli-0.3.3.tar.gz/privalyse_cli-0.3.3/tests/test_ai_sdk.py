import unittest
import ast
from pathlib import Path
from privalyse_scanner.analyzers.python_analyzer import PythonAnalyzer
from privalyse_scanner.models.finding import Finding

class TestAISDKDetection(unittest.TestCase):
    def setUp(self):
        self.analyzer = PythonAnalyzer()

    def test_openai_leak(self):
        code = """
import openai

def chat(user_email):
    # user_email is PII
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"User {user_email} asked..."}]
    )
"""
        # We need to simulate taint tracking context
        # Since analyze_file does everything, we can use it directly but we need to ensure
        # user_email is treated as tainted.
        # In a real scan, this comes from sources. Here we can mock it or use a known source pattern.
        
        # Let's use a known source pattern to trigger taint
        code_with_source = """
from flask import request
import openai

@app.route('/chat')
def chat():
    user_email = request.json['email'] # Source
    # Sink
    openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_email}]
    )
"""
        findings, _ = self.analyzer.analyze_file(Path("test.py"), code_with_source)
        
        ai_leaks = [f for f in findings if f.rule == "AI_PII_LEAK"]
        self.assertTrue(len(ai_leaks) > 0)
        self.assertEqual(ai_leaks[0].classification.reasoning, "Unsanitized PII (email) sent to AI Sink (openai)")

    def test_langchain_leak(self):
        code = """
from flask import request
from langchain.llms import OpenAI

def process():
    secret = request.json['api_key'] # Source: password/token
    llm = OpenAI()
    llm.predict(f"The key is {secret}")
"""
        findings, _ = self.analyzer.analyze_file(Path("test.py"), code)
        ai_leaks = [f for f in findings if f.rule == "AI_PII_LEAK"]
        self.assertTrue(len(ai_leaks) > 0)
        self.assertIn("langchain", ai_leaks[0].classification.reasoning.lower())

    def test_sanitized_ai_call(self):
        code = """
from flask import request
import openai
from utils import anonymize

def chat():
    email = request.json['email']
    safe_email = anonymize(email) # Sanitizer
    
    openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": safe_email}]
    )
"""
        findings, _ = self.analyzer.analyze_file(Path("test.py"), code)
        ai_leaks = [f for f in findings if f.rule == "AI_PII_LEAK"]
        self.assertEqual(len(ai_leaks), 0, "Should not report leak if sanitized")

if __name__ == '__main__':
    unittest.main()
