"""
Enhanced Injection Analyzer - Track variable assignments for SQL injection
"""

import ast
import re
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from ..models.finding import Finding, Severity, ClassificationResult
from ..utils.helpers import safe_unparse


class InjectionAnalyzer:
    """Analyzes code for injection vulnerabilities with variable tracking"""
    
    def __init__(self):
        self.findings = []
        
        # SQL injection patterns
        self.sql_keywords = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
            'ALTER', 'EXEC', 'EXECUTE', 'UNION', 'WHERE', 'FROM'
        }
        
        # Command execution functions
        self.command_funcs = {
            'os.system', 'subprocess.call', 'subprocess.run', 'subprocess.Popen',
            'os.popen', 'os.exec', 'commands.getoutput', 'eval', 'exec'
        }
        
        # File path functions
        self.file_funcs = {
            'open', 'os.path.join', 'pathlib.Path', 'os.remove', 'os.unlink',
            'shutil.rmtree', 'os.rmdir', 'os.rename', 'os.makedirs'
        }
        
        # Template rendering
        self.template_funcs = {
            'render_template', 'render_template_string', 'Markup', 'jinja2.Template'
        }
        
        # HTTP response functions (XSS)
        self.response_funcs = {
            'return', 'send', 'jsonify', 'make_response', 'Response',
            'HttpResponse', 'render', 'redirect'
        }
        
        # HTML output functions
        self.html_funcs = {
            'write', 'writeln', 'innerHTML', 'outerHTML', 'insertAdjacentHTML'
        }
        
        # HTTP functions (SSRF)
        self.http_funcs = {
            'requests.get', 'requests.post', 'requests.put', 'requests.delete',
            'urllib.request.urlopen', 'httpx.get', 'httpx.post'
        }
        
        # Deserialization
        self.deserialize_funcs = {
            'pickle.loads', 'pickle.load', 'yaml.load', 'marshal.loads',
            'shelve.open', 'eval', 'exec', 'compile'
        }
        
        # XML parsing functions (XXE)
        self.xml_funcs = {
            'xml.etree.ElementTree.parse', 'xml.etree.ElementTree.fromstring',
            'xml.etree.ElementTree.XML', 'xml.dom.minidom.parse',
            'xml.dom.minidom.parseString', 'xml.sax.parse', 'xml.sax.parseString',
            'lxml.etree.parse', 'lxml.etree.fromstring', 'lxml.etree.XML'
        }
    
    def analyze_file(self, file_path: Path, code: str, taint_tracker=None) -> List[Finding]:
        """Analyze file for injection vulnerabilities"""
        self.findings = []
        self.taint_tracker = taint_tracker
        
        try:
            tree = ast.parse(code, filename=str(file_path))
        except SyntaxError:
            return self.findings
        
        # Create visitor with variable tracking
        visitor = InjectionVisitor(self, file_path, code)
        visitor.visit(tree)
        
        return self.findings


class InjectionVisitor(ast.NodeVisitor):
    """AST visitor with variable assignment tracking"""
    
    def __init__(self, analyzer: InjectionAnalyzer, file_path: Path, code: str):
        self.analyzer = analyzer
        self.file_path = file_path
        self.code = code
        self.lines = code.split('\n')
        
        # Track variable assignments: var_name -> (is_dynamic, has_sql_keywords, has_path, has_url, node)
        self.tracked_vars: Dict[str, tuple] = {}
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments for later analysis"""
        # Check if RHS is a dynamic string
        if isinstance(node.value, (ast.JoinedStr, ast.BinOp, ast.Call)):
            content = self._extract_string_content(node.value)
            has_sql = self._contains_sql_keywords(content)
            has_path = '/' in content or '\\\\' in content  # Path indicators
            has_url = 'http' in content.lower() or 'url' in content.lower()
            
            # Store info about each target variable
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tracked_vars[target.id] = (True, has_sql, has_path, has_url, node)
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls"""
        func_name = self._get_func_name(node)
        
        if func_name:
            self._check_sql_injection(node, func_name)
            self._check_command_injection(node, func_name)
            self._check_path_traversal(node, func_name)
            self._check_ssrf(node, func_name)
            self._check_deserialization(node, func_name)
            self._check_template_injection(node, func_name)
            self._check_xss(node, func_name)
            self._check_xxe(node, func_name)
        
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
    
    def _check_sql_injection(self, node: ast.Call, func_name: str):
        """Check for SQL injection"""
        
        # Check if this is a SQL execution function
        if not any(db in func_name.lower() for db in ['execute', 'raw', 'query', 'sql']):
            return
        
        # Check all arguments
        for arg in node.args:
            # Direct unsafe construction
            if self._is_unsafe_sql_construction(arg):
                self._report_sql_injection(node, True)
                return
            
            # Variable with dynamic SQL
            if isinstance(arg, ast.Name) and arg.id in self.tracked_vars:
                var_info = self.tracked_vars[arg.id]
                is_dynamic = var_info[0]
                has_sql = var_info[1]
                if is_dynamic and has_sql:
                    self._report_sql_injection(node, False)
                    return
    
    def _report_sql_injection(self, node: ast.Call, has_user_input: bool):
        """Report SQL injection finding"""
        snippet = self._get_snippet(node)
        severity = Severity.CRITICAL if has_user_input else Severity.HIGH
        
        self.analyzer.findings.append(Finding(
            rule="SQL_INJECTION",
            severity=severity,
            file=self.file_path.as_posix(),
            line=node.lineno,
            snippet=snippet,
            classification=ClassificationResult(
                pii_types=["database"],
                sectors=["security"],
                severity=severity.value,
                article="Art. 32",
                legal_basis_required=True,
                category="injection",
                confidence=0.9 if has_user_input else 0.75,
                reasoning="SQL query constructed via string concatenation/formatting - potential SQL injection",
                gdpr_articles=["Art. 32", "Art. 5(1)(f)"]
            ),
            metadata={
                'vulnerability_type': 'SQL Injection',
                'recommendation': 'Use parameterized queries or ORM methods',
                'cwe': 'CWE-89'
            }
        ))
    
    def _is_unsafe_sql_construction(self, node: ast.expr) -> bool:
        """Check if node contains unsafe SQL string construction"""
        if isinstance(node, ast.JoinedStr):
            string_content = self._extract_string_content(node)
            if self._contains_sql_keywords(string_content):
                return True
        
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
            left_str = self._extract_string_content(node.left)
            right_str = self._extract_string_content(node.right)
            if self._contains_sql_keywords(left_str + right_str):
                return True
        
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in ['format', 'join']:
                if isinstance(node.func.value, ast.Constant):
                    if self._contains_sql_keywords(str(node.func.value.value)):
                        return True
        
        return False
    
    def _contains_sql_keywords(self, text: str) -> bool:
        """Check if text contains SQL keywords"""
        upper_text = text.upper()
        return any(keyword in upper_text for keyword in self.analyzer.sql_keywords)
    
    def _extract_string_content(self, node: ast.expr) -> str:
        """Extract string content from AST node"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
            return ''.join(parts)
        elif isinstance(node, ast.BinOp):
            left = self._extract_string_content(node.left)
            right = self._extract_string_content(node.right)
            return left + right
        return ""
    
    def _check_command_injection(self, node: ast.Call, func_name: str):
        """Check for command injection"""
        
        if not any(cmd in func_name for cmd in self.analyzer.command_funcs):
            return
        
        # eval/exec always dangerous
        if func_name in ['eval', 'exec']:
            snippet = self._get_snippet(node)
            self.analyzer.findings.append(Finding(
                rule="CODE_INJECTION",
                severity=Severity.CRITICAL,
                file=self.file_path.as_posix(),
                line=node.lineno,
                snippet=snippet,
                classification=ClassificationResult(
                    pii_types=[],
                    sectors=["security"],
                    severity="critical",
                    article="Art. 32",
                    legal_basis_required=True,
                    category="injection",
                    confidence=1.0,
                    reasoning=f"Dangerous {func_name}() allows arbitrary code execution",
                    gdpr_articles=["Art. 32"]
                ),
                metadata={
                    'vulnerability_type': 'Code Injection',
                    'recommendation': 'Avoid eval/exec - use ast.literal_eval or safer alternatives',
                    'cwe': 'CWE-94'
                }
            ))
            return
        
        # shell=True with dynamic input
        has_shell_true = any(
            isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in node.keywords if kw.arg == 'shell'
        )
        
        if has_shell_true:
            for arg in node.args:
                if self._contains_user_input(arg) or self._is_dynamic_string(arg):
                    snippet = self._get_snippet(node)
                    self.analyzer.findings.append(Finding(
                        rule="COMMAND_INJECTION",
                        severity=Severity.CRITICAL,
                        file=self.file_path.as_posix(),
                        line=node.lineno,
                        snippet=snippet,
                        classification=ClassificationResult(
                            pii_types=[],
                            sectors=["security"],
                            severity="critical",
                            article="Art. 32",
                            legal_basis_required=True,
                            category="injection",
                            confidence=0.95,
                            reasoning="Command execution with shell=True and dynamic input - potential command injection",
                            gdpr_articles=["Art. 32", "Art. 5(1)(f)"]
                        ),
                        metadata={
                            'vulnerability_type': 'Command Injection',
                            'recommendation': 'Use shell=False and pass arguments as list, or validate/sanitize input',
                            'cwe': 'CWE-78'
                        }
                    ))
    
    def _check_path_traversal(self, node: ast.Call, func_name: str):
        """Check for path traversal"""
        
        if not any(file_func in func_name for file_func in self.analyzer.file_funcs):
            return
        
        for arg in node.args:
            # Check for user input OR dynamic path construction (f-strings, concatenation)
            is_vulnerable = (
                self._contains_user_input(arg) or 
                self._is_path_concatenation(arg) or
                isinstance(arg, ast.JoinedStr) or  # f-string paths
                (isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add))  # string + var
            )
            
            # Also check if arg is a tracked variable with path indicators
            if isinstance(arg, ast.Name) and arg.id in self.tracked_vars:
                var_info = self.tracked_vars[arg.id]
                if len(var_info) >= 3 and var_info[2]:  # has_path is True
                    is_vulnerable = True
            
            if is_vulnerable:
                snippet = self._get_snippet(node)
                has_sanitization = self._has_path_sanitization(node)
                severity = Severity.MEDIUM if has_sanitization else Severity.HIGH
                
                self.analyzer.findings.append(Finding(
                    rule="PATH_TRAVERSAL",
                    severity=severity,
                    file=self.file_path.as_posix(),
                    line=node.lineno,
                    snippet=snippet,
                    classification=ClassificationResult(
                        pii_types=[],
                        sectors=["security"],
                        severity=severity.value,
                        article="Art. 32",
                        legal_basis_required=True,
                        category="injection",
                        confidence=0.8 if not has_sanitization else 0.5,
                        reasoning="File path constructed from user input - potential path traversal",
                        gdpr_articles=["Art. 32", "Art. 5(1)(f)"]
                    ),
                    metadata={
                        'vulnerability_type': 'Path Traversal',
                        'recommendation': 'Validate and sanitize file paths, use os.path.basename(), check against whitelist',
                        'cwe': 'CWE-22'
                    }
                ))
    
    def _check_ssrf(self, node: ast.Call, func_name: str):
        """Check for SSRF"""
        
        if not any(http in func_name for http in self.analyzer.http_funcs):
            return
        
        # Check all args - if it's a variable or dynamic construction, it's potentially vulnerable
        for arg in node.args:
            is_vulnerable = (
                self._contains_user_input(arg) or 
                self._is_dynamic_url(arg) or
                isinstance(arg, ast.Name) or  # Variable could contain user input
                isinstance(arg, ast.JoinedStr)  # f-string URL
            )
            
            # Also check if arg is a tracked variable with URL indicators
            if isinstance(arg, ast.Name) and arg.id in self.tracked_vars:
                var_info = self.tracked_vars[arg.id]
                if len(var_info) >= 4 and var_info[3]:  # has_url is True
                    is_vulnerable = True
            
            if is_vulnerable:
                snippet = self._get_snippet(node)
                self.analyzer.findings.append(Finding(
                    rule="SSRF",
                    severity=Severity.HIGH,
                    file=self.file_path.as_posix(),
                    line=node.lineno,
                    snippet=snippet,
                    classification=ClassificationResult(
                        pii_types=[],
                        sectors=["security"],
                        severity="high",
                        article="Art. 32",
                        legal_basis_required=True,
                        category="injection",
                        confidence=0.85,
                        reasoning="HTTP request with user-controlled URL - potential SSRF",
                        gdpr_articles=["Art. 32", "Art. 44"]
                    ),
                    metadata={
                        'vulnerability_type': 'Server-Side Request Forgery (SSRF)',
                        'recommendation': 'Validate URLs against whitelist, block internal IPs, use URL parsing',
                        'cwe': 'CWE-918'
                    }
                ))
    
    def _check_deserialization(self, node: ast.Call, func_name: str):
        """Check for insecure deserialization"""
        
        if not any(deser in func_name for deser in self.analyzer.deserialize_funcs):
            return
        
        # yaml.load without SafeLoader
        if 'yaml.load' in func_name:
            has_safe_loader = any(
                kw.arg == 'Loader' and 'Safe' in safe_unparse(kw.value)
                for kw in node.keywords
            )
            if not has_safe_loader:
                snippet = self._get_snippet(node)
                self.analyzer.findings.append(Finding(
                    rule="YAML_UNSAFE_LOAD",
                    severity=Severity.CRITICAL,
                    file=self.file_path.as_posix(),
                    line=node.lineno,
                    snippet=snippet,
                    classification=ClassificationResult(
                        pii_types=[],
                        sectors=["security"],
                        severity="critical",
                        article="Art. 32",
                        legal_basis_required=True,
                        category="deserialization",
                        confidence=1.0,
                        reasoning="yaml.load() without SafeLoader allows arbitrary code execution",
                        gdpr_articles=["Art. 32"]
                    ),
                    metadata={
                        'vulnerability_type': 'Insecure Deserialization',
                        'recommendation': 'Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)',
                        'cwe': 'CWE-502'
                    }
                ))
        
        # pickle with untrusted data
        elif 'pickle' in func_name:
            for arg in node.args:
                if self._contains_user_input(arg):
                    snippet = self._get_snippet(node)
                    self.analyzer.findings.append(Finding(
                        rule="PICKLE_UNTRUSTED",
                        severity=Severity.CRITICAL,
                        file=self.file_path.as_posix(),
                        line=node.lineno,
                        snippet=snippet,
                        classification=ClassificationResult(
                            pii_types=[],
                            sectors=["security"],
                            severity="critical",
                            article="Art. 32",
                            legal_basis_required=True,
                            category="deserialization",
                            confidence=0.95,
                            reasoning="pickle deserialization of untrusted data allows code execution",
                            gdpr_articles=["Art. 32"]
                        ),
                        metadata={
                            'vulnerability_type': 'Insecure Deserialization',
                            'recommendation': 'Never unpickle untrusted data - use JSON or other safe formats',
                            'cwe': 'CWE-502'
                        }
                    ))
    
    def _check_template_injection(self, node: ast.Call, func_name: str):
        """Check for SSTI"""
        
        if not any(tmpl in func_name for tmpl in self.analyzer.template_funcs):
            return
        
        if 'render_template_string' in func_name:
            for arg in node.args:
                # render_template_string is ALWAYS dangerous with any non-static content
                is_vulnerable = (
                    isinstance(arg, ast.Name) or  # Variable
                    self._contains_user_input(arg) or 
                    self._is_dynamic_string(arg) or
                    not isinstance(arg, ast.Constant)  # Not a static string
                )
                
                if is_vulnerable:
                    snippet = self._get_snippet(node)
                    self.analyzer.findings.append(Finding(
                        rule="TEMPLATE_INJECTION",
                        severity=Severity.CRITICAL,
                        file=self.file_path.as_posix(),
                        line=node.lineno,
                        snippet=snippet,
                        classification=ClassificationResult(
                            pii_types=[],
                            sectors=["security"],
                            severity="critical",
                            article="Art. 32",
                            legal_basis_required=True,
                            category="injection",
                            confidence=0.9,
                            reasoning="Template rendering with user input - potential SSTI",
                            gdpr_articles=["Art. 32"]
                        ),
                        metadata={
                            'vulnerability_type': 'Server-Side Template Injection (SSTI)',
                            'recommendation': 'Use render_template() with separate template files, sanitize template variables',
                            'cwe': 'CWE-94'
                        }
                    ))
    
    def _check_xss(self, node: ast.Call, func_name: str):
        """Check for Cross-Site Scripting (XSS) vulnerabilities"""
        
        # Check Flask/Django response functions with unescaped user input
        if any(resp in func_name for resp in ['jsonify', 'make_response', 'Response', 'HttpResponse']):
            for arg in node.args:
                # Check if argument contains unescaped user input
                if self._contains_user_input(arg) or isinstance(arg, ast.Name):
                    # Check if there's HTML content or no explicit escaping
                    arg_str = safe_unparse(arg).lower()
                    has_html = any(tag in arg_str for tag in ['<', '>', 'html', 'script', 'div', 'span'])
                    
                    # Only report if HTML content is present
                    if has_html or self._is_dynamic_string(arg):
                        snippet = self._get_snippet(node)
                        self.analyzer.findings.append(Finding(
                            rule="XSS_REFLECTED",
                            severity=Severity.HIGH,
                            file=self.file_path.as_posix(),
                            line=node.lineno,
                            snippet=snippet,
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["security", "web"],
                                severity="high",
                                article="Art. 32",
                                legal_basis_required=True,
                                category="injection",
                                confidence=0.75,
                                reasoning="Potentially unescaped user input in HTTP response - XSS risk",
                                gdpr_articles=["Art. 32", "Art. 5(1)(f)"]
                            ),
                            metadata={
                                'vulnerability_type': 'Cross-Site Scripting (XSS)',
                                'xss_type': 'Reflected XSS',
                                'recommendation': 'Use template engine auto-escaping, sanitize user input, Content-Security-Policy headers',
                                'cwe': 'CWE-79'
                            }
                        ))
                        return  # Only report once per call
    
    def _check_xxe(self, node: ast.Call, func_name: str):
        """Check for XML External Entity (XXE) vulnerabilities"""
        
        # Check if using insecure XML parsing
        if any(xml_func in func_name for xml_func in self.analyzer.xml_funcs):
            # By default, most XML parsers are vulnerable to XXE
            # Check if there's explicit entity processing disabled
            has_safe_config = False
            
            # Look for defusedxml usage (safe alternative)
            if 'defusedxml' in func_name:
                has_safe_config = True
            
            # Check for explicit entity processing configuration
            for kw in node.keywords:
                if kw.arg in ['resolve_entities', 'no_network']:
                    kw_value = safe_unparse(kw.value)
                    if 'False' in kw_value:
                        has_safe_config = True
            
            if not has_safe_config:
                snippet = self._get_snippet(node)
                self.analyzer.findings.append(Finding(
                    rule="XXE_VULNERABILITY",
                    severity=Severity.HIGH,
                    file=self.file_path.as_posix(),
                    line=node.lineno,
                    snippet=snippet,
                    classification=ClassificationResult(
                        pii_types=[],
                        sectors=["security", "web"],
                        severity="high",
                        article="Art. 32",
                        legal_basis_required=True,
                        category="injection",
                        confidence=0.85,
                        reasoning="XML parser may be vulnerable to XXE - entity processing not disabled",
                        gdpr_articles=["Art. 32", "Art. 5(1)(f)"]
                    ),
                    metadata={
                        'vulnerability_type': 'XML External Entity (XXE)',
                        'recommendation': 'Use defusedxml library, disable entity processing, DTD processing',
                        'cwe': 'CWE-611'
                    }
                ))
    
    # Helper methods
    
    def _contains_user_input(self, node: ast.expr) -> bool:
        """Check if node contains user input variables"""
        user_input_patterns = [
            'request.', 'input(', 'argv', 'stdin', 'get(', 'post(',
            'params', 'query', 'form', 'json', 'data'
        ]
        node_str = safe_unparse(node).lower()
        return any(pattern in node_str for pattern in user_input_patterns)
    
    def _is_dynamic_string(self, node: ast.expr) -> bool:
        """Check if node is dynamically constructed"""
        return isinstance(node, (ast.JoinedStr, ast.BinOp, ast.Call))
    
    def _is_path_concatenation(self, node: ast.expr) -> bool:
        """Check if node is path concatenation"""
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return True
        if isinstance(node, ast.JoinedStr):
            return '/' in safe_unparse(node) or '\\' in safe_unparse(node)
        return False
    
    def _is_dynamic_url(self, node: ast.expr) -> bool:
        """Check if node is dynamic URL"""
        if self._is_dynamic_string(node):
            node_str = safe_unparse(node).lower()
            return 'http' in node_str or 'url' in node_str
        return False
    
    def _has_path_sanitization(self, node: ast.Call) -> bool:
        """Check for path sanitization"""
        node_str = safe_unparse(node).lower()
        return 'basename' in node_str or 'abspath' in node_str or 'realpath' in node_str
    
    def _get_snippet(self, node: ast.AST) -> str:
        """Get code snippet"""
        if hasattr(node, 'lineno') and 0 < node.lineno <= len(self.lines):
            return self.lines[node.lineno - 1].strip()
        return safe_unparse(node)[:100]
