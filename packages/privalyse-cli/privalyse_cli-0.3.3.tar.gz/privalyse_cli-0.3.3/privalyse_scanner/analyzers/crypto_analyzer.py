"""
Cryptography Weakness Analyzer - Weak algorithms, insecure configurations
"""

import ast
import re
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from ..models.finding import Finding, Severity, ClassificationResult
from ..utils.helpers import safe_unparse


class CryptoAnalyzer:
    """Analyzes code for cryptographic weaknesses"""
    
    def __init__(self):
        self.findings = []
        
        # Weak hash algorithms
        self.weak_hashes = {
            'md5', 'sha1', 'md4', 'sha', 'md2'
        }
        
        # Weak cipher modes
        self.weak_modes = {
            'ECB': 'Electronic Codebook mode is insecure',
            'CBC': 'CBC without authenticated encryption is vulnerable'
        }
        
        # Insecure random functions
        self.insecure_random = {
            'random.random', 'random.randint', 'random.choice',
            'random.randrange', 'random.uniform'
        }
        
        # Proper crypto random
        self.secure_random = {
            'secrets.', 'os.urandom', 'random.SystemRandom',
            'Crypto.Random'
        }
    
    def analyze_file(self, file_path: Path, code: str) -> List[Finding]:
        """
        Analyze file for cryptographic weaknesses
        
        Args:
            file_path: Path to the file
            code: Source code
            
        Returns:
            List of crypto findings
        """
        self.findings = []
        
        try:
            tree = ast.parse(code, filename=str(file_path))
        except SyntaxError:
            return self.findings
        
        # Create visitor
        visitor = CryptoVisitor(self, file_path, code)
        visitor.visit(tree)
        
        return self.findings


class CryptoVisitor(ast.NodeVisitor):
    """AST visitor for cryptographic weakness detection"""
    
    def __init__(self, analyzer: CryptoAnalyzer, file_path: Path, code: str):
        self.analyzer = analyzer
        self.file_path = file_path
        self.code = code
        self.lines = code.split('\n')
        self.current_function = None  # Track current function context
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function definitions for context"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls to detect crypto weaknesses"""
        
        func_name = self._get_func_name(node)
        
        if func_name:
            self._check_weak_hash(node, func_name)
            self._check_weak_cipher(node, func_name)
            self._check_insecure_random(node, func_name)
            self._check_ssl_context(node, func_name)
            self._check_weak_key_size(node, func_name)
        
        self.generic_visit(node)
    
    def _get_func_name(self, node: ast.Call) -> Optional[str]:
        """Extract full function name"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return None
    
    def _check_weak_hash(self, node: ast.Call, func_name: str):
        """Check for weak hash algorithms"""
        
        func_lower = func_name.lower()
        
        # Check for weak hash usage
        for weak_hash in self.analyzer.weak_hashes:
            if weak_hash in func_lower:
                snippet = self._get_snippet(node)
                
                # Determine context (password hashing is critical, checksums less so)
                is_password_context = self._is_password_context(node)
                severity = Severity.CRITICAL if is_password_context else Severity.HIGH
                
                self.analyzer.findings.append(Finding(
                    rule="CRYPTO_WEAK_HASH",
                    severity=severity,
                    file=self.file_path.as_posix(),
                    line=node.lineno,
                    snippet=snippet,
                    classification=ClassificationResult(
                        pii_types=["password"] if is_password_context else [],
                        sectors=["security", "crypto"],
                        severity=severity.value,
                        article="Art. 32",
                        legal_basis_required=True,
                        category="crypto",
                        confidence=1.0,
                        reasoning=f"Weak hash algorithm {weak_hash.upper()} detected - vulnerable to collisions",
                        gdpr_articles=["Art. 32(1)(a)"]
                    ),
                    metadata={
                        'vulnerability_type': 'Weak Cryptography',
                        'algorithm': weak_hash.upper(),
                        'recommendation': 'Use SHA-256, SHA-512, or bcrypt/argon2 for passwords',
                        'cwe': 'CWE-327'
                    }
                ))
                break
    
    def _check_weak_cipher(self, node: ast.Call, func_name: str):
        """Check for weak cipher modes (ECB, etc.)"""
        
        # Check for AES.new() or similar with mode parameter
        if 'new' in func_name.lower() and ('aes' in func_name.lower() or 'des' in func_name.lower()):
            
            # Check mode parameter (both as keyword argument and positional)
            mode_found = False
            
            # Check keyword arguments
            for kw in node.keywords:
                if kw.arg and 'mode' in kw.arg.lower():
                    mode_value = safe_unparse(kw.value).upper()
                    mode_found = True
                    
                    # Check for ECB mode
                    if 'ECB' in mode_value:
                        snippet = self._get_snippet(node)
                        self.analyzer.findings.append(Finding(
                            rule="CRYPTO_ECB_MODE",
                            severity=Severity.CRITICAL,
                            file=self.file_path.as_posix(),
                            line=node.lineno,
                            snippet=snippet,
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["security", "crypto"],
                                severity="critical",
                                article="Art. 32",
                                legal_basis_required=True,
                                category="crypto",
                                confidence=1.0,
                                reasoning="ECB cipher mode detected - does not provide semantic security",
                                gdpr_articles=["Art. 32(1)(a)"]
                            ),
                            metadata={
                                'vulnerability_type': 'Weak Cipher Mode',
                                'mode': 'ECB',
                                'recommendation': 'Use GCM, CBC with HMAC, or authenticated encryption (AES-GCM)',
                                'cwe': 'CWE-327'
                            }
                        ))
            
            # Check positional arguments (second argument is usually mode)
            if not mode_found and len(node.args) >= 2:
                mode_arg = node.args[1]
                mode_value = safe_unparse(mode_arg).upper()
                
                if 'ECB' in mode_value:
                        snippet = self._get_snippet(node)
                        self.analyzer.findings.append(Finding(
                            rule="CRYPTO_ECB_MODE",
                            severity=Severity.CRITICAL,
                            file=self.file_path.as_posix(),
                            line=node.lineno,
                            snippet=snippet,
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["security", "crypto"],
                                severity="critical",
                                article="Art. 32",
                                legal_basis_required=True,
                                category="crypto",
                                confidence=1.0,
                                reasoning="ECB cipher mode detected - does not provide semantic security",
                                gdpr_articles=["Art. 32(1)(a)"]
                            ),
                            metadata={
                                'vulnerability_type': 'Weak Cipher Mode',
                                'mode': 'ECB',
                                'recommendation': 'Use GCM, CBC with HMAC, or authenticated encryption (AES-GCM)',
                                'cwe': 'CWE-327'
                            }
                        ))
            
            # Check for DES (always weak)
            if 'des' in func_name.lower() and 'tripledes' not in func_name.lower():
                snippet = self._get_snippet(node)
                self.analyzer.findings.append(Finding(
                    rule="CRYPTO_WEAK_CIPHER",
                    severity=Severity.CRITICAL,
                    file=self.file_path.as_posix(),
                    line=node.lineno,
                    snippet=snippet,
                    classification=ClassificationResult(
                        pii_types=[],
                        sectors=["security", "crypto"],
                        severity="critical",
                        article="Art. 32",
                        legal_basis_required=True,
                        category="crypto",
                        confidence=1.0,
                        reasoning="DES cipher detected - key size too small, deprecated",
                        gdpr_articles=["Art. 32(1)(a)"]
                    ),
                    metadata={
                        'vulnerability_type': 'Weak Cipher',
                        'algorithm': 'DES',
                        'recommendation': 'Use AES-256 with GCM mode',
                        'cwe': 'CWE-326'
                    }
                ))
    
    def _check_insecure_random(self, node: ast.Call, func_name: str):
        """Check for insecure random number generation in security contexts"""
        
        # Check if using insecure random
        if any(insecure in func_name for insecure in self.analyzer.insecure_random):
            
            # Check if in security context
            if self._is_security_context(node):
                snippet = self._get_snippet(node)
                self.analyzer.findings.append(Finding(
                    rule="CRYPTO_INSECURE_RANDOM",
                    severity=Severity.HIGH,
                    file=self.file_path.as_posix(),
                    line=node.lineno,
                    snippet=snippet,
                    classification=ClassificationResult(
                        pii_types=["token", "session_token"],
                        sectors=["security", "crypto"],
                        severity="high",
                        article="Art. 32",
                        legal_basis_required=True,
                        category="crypto",
                        confidence=0.85,
                        reasoning="Insecure random number generator used in security context",
                        gdpr_articles=["Art. 32(1)(a)"]
                    ),
                    metadata={
                        'vulnerability_type': 'Weak Randomness',
                        'recommendation': 'Use secrets module: secrets.token_bytes(), secrets.token_hex()',
                        'cwe': 'CWE-338'
                    }
                ))
    
    def _check_ssl_context(self, node: ast.Call, func_name: str):
        """Check for insecure SSL/TLS configuration"""
        
        # Check for SSL context creation
        if 'ssl' in func_name.lower() and 'context' in func_name.lower():
            
            # Check for insecure SSL versions
            for arg in node.args:
                if isinstance(arg, ast.Attribute):
                    version = safe_unparse(arg).upper()
                    if any(weak in version for weak in ['SSLV2', 'SSLV3', 'TLSV1', 'TLS_V1']):
                        snippet = self._get_snippet(node)
                        self.analyzer.findings.append(Finding(
                            rule="CRYPTO_WEAK_TLS",
                            severity=Severity.CRITICAL,
                            file=self.file_path.as_posix(),
                            line=node.lineno,
                            snippet=snippet,
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["security", "crypto"],
                                severity="critical",
                                article="Art. 32",
                                legal_basis_required=True,
                                category="crypto",
                                confidence=1.0,
                                reasoning=f"Weak TLS/SSL version detected: {version}",
                                gdpr_articles=["Art. 32(1)(a)"]
                            ),
                            metadata={
                                'vulnerability_type': 'Weak TLS/SSL',
                                'version': version,
                                'recommendation': 'Use TLS 1.2+ only (ssl.PROTOCOL_TLS_SERVER or TLSv1_2)',
                                'cwe': 'CWE-327'
                            }
                        ))
        
        # Check for verify=False in requests
        if any(http in func_name for http in ['requests.', 'httpx.']):
            for kw in node.keywords:
                if kw.arg == 'verify' and isinstance(kw.value, ast.Constant):
                    if kw.value.value is False:
                        snippet = self._get_snippet(node)
                        self.analyzer.findings.append(Finding(
                            rule="CRYPTO_SSL_VERIFY_DISABLED",
                            severity=Severity.CRITICAL,
                            file=self.file_path.as_posix(),
                            line=node.lineno,
                            snippet=snippet,
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["security", "crypto"],
                                severity="critical",
                                article="Art. 32",
                                legal_basis_required=True,
                                category="crypto",
                                confidence=1.0,
                                reasoning="SSL certificate verification disabled - vulnerable to MITM attacks",
                                gdpr_articles=["Art. 32(1)(a)"]
                            ),
                            metadata={
                                'vulnerability_type': 'SSL Verification Disabled',
                                'recommendation': 'Remove verify=False or provide path to CA bundle',
                                'cwe': 'CWE-295'
                            }
                        ))
    
    def _check_weak_key_size(self, node: ast.Call, func_name: str):
        """Check for weak key sizes in asymmetric crypto"""
        
        # RSA key generation
        if 'rsa' in func_name.lower() and 'generate' in func_name.lower():
            
            # Check key size
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                    key_size = arg.value
                    
                    if key_size < 2048:
                        snippet = self._get_snippet(node)
                        self.analyzer.findings.append(Finding(
                            rule="CRYPTO_WEAK_KEY_SIZE",
                            severity=Severity.HIGH,
                            file=self.file_path.as_posix(),
                            line=node.lineno,
                            snippet=snippet,
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["security", "crypto"],
                                severity="high",
                                article="Art. 32",
                                legal_basis_required=True,
                                category="crypto",
                                confidence=1.0,
                                reasoning=f"RSA key size {key_size} bits is too small - recommend 2048+ bits",
                                gdpr_articles=["Art. 32(1)(a)"]
                            ),
                            metadata={
                                'vulnerability_type': 'Weak Key Size',
                                'key_size': key_size,
                                'recommendation': 'Use 2048-bit RSA minimum (4096-bit for long-term security)',
                                'cwe': 'CWE-326'
                            }
                        ))
    
    # Helper methods
    
    def _is_password_context(self, node: ast.Call) -> bool:
        """Check if hash is being used for passwords"""
        # Look at variable names nearby
        node_str = safe_unparse(node).lower()
        password_keywords = ['password', 'passwd', 'pwd', 'auth', 'credential']
        return any(kw in node_str for kw in password_keywords)
    
    def _is_security_context(self, node: ast.Call) -> bool:
        """Check if random is used in security context"""
        node_str = safe_unparse(node).lower()
        security_keywords = [
            'token', 'secret', 'key', 'session', 'csrf', 'nonce',
            'salt', 'iv', 'password', 'auth', 'otp', 'code'
        ]
        
        # Check the call itself
        if any(kw in node_str for kw in security_keywords):
            return True
        
        # Check current function name
        if self.current_function:
            func_name_lower = self.current_function.lower()
            if any(kw in func_name_lower for kw in security_keywords):
                return True
        
        return False
    
    def _get_snippet(self, node: ast.AST) -> str:
        """Get code snippet for node"""
        if hasattr(node, 'lineno') and 0 < node.lineno <= len(self.lines):
            return self.lines[node.lineno - 1].strip()
        return safe_unparse(node)[:100]
