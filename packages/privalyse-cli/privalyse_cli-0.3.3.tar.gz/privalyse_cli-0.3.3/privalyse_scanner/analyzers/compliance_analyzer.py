"""
GDPR Compliance Analyzer - Detects compliance and data governance issues
"""

import ast
import re
from typing import List, Dict, Any
from pathlib import Path

from ..models.finding import Finding, Severity, ClassificationResult


class ComplianceAnalyzer:
    """Analyzes code for GDPR compliance issues"""
    
    def __init__(self):
        self.findings = []
    
    def analyze_file(self, file_path: Path, code: str) -> List[Finding]:
        """
        Analyze file for GDPR compliance issues
        
        Returns:
            List of compliance findings
        """
        self.findings = []
        
        try:
            tree = ast.parse(code, filename=str(file_path))
        except SyntaxError:
            return self.findings
        
        # Run compliance checks
        self._check_consent_management(tree, file_path, code)
        self._check_data_retention(tree, file_path, code)
        self._check_data_minimization(tree, file_path, code)
        self._check_legal_basis(tree, file_path, code)
        
        return self.findings
    
    # ============================================================================
    # CONSENT MANAGEMENT
    # ============================================================================
    
    def _check_consent_management(self, tree: ast.AST, file_path: Path, code: str):
        """Check for consent-related compliance issues"""
        
        # Check for data collection without consent checks
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Look for data collection patterns
                if self._is_data_collection_call(node):
                    # Check if there's a consent check nearby
                    if not self._has_consent_check_in_context(tree, node):
                        self.findings.append(Finding(
                            rule="GDPR_CONSENT_MISSING",
                            severity=Severity.HIGH,
                            file=file_path.as_posix(),
                            line=node.lineno,
                            snippet=self._get_line(code, node.lineno),
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["compliance"],
                                severity="high",
                                article="Art. 6",
                                legal_basis_required=True,
                                category="compliance",
                                confidence=0.8,
                                reasoning="Data collection without visible consent check",
                                gdpr_articles=["Art. 6", "Art. 7"]
                            )
                        ))
    
    # ============================================================================
    # DATA RETENTION
    # ============================================================================
    
    def _check_data_retention(self, tree: ast.AST, file_path: Path, code: str):
        """Check for data retention policy implementation"""
        
        # Look for database models/tables without retention fields
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_data_model_class(node):
                    has_retention_field = self._has_retention_or_expiry_field(node)
                    has_deletion_method = self._has_deletion_method(node)
                    
                    if not (has_retention_field or has_deletion_method):
                        self.findings.append(Finding(
                            rule="GDPR_RETENTION_UNDEFINED",
                            severity=Severity.MEDIUM,
                            file=file_path.as_posix(),
                            line=node.lineno,
                            snippet=self._get_line(code, node.lineno),
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["compliance"],
                                severity="medium",
                                article="Art. 5",
                                legal_basis_required=True,
                                category="compliance",
                                confidence=0.7,
                                reasoning="Data model without retention policy",
                                gdpr_articles=["Art. 5(1)(e)"]
                            )
                        ))
    
    # ============================================================================
    # DATA MINIMIZATION
    # ============================================================================
    
    def _check_data_minimization(self, tree: ast.AST, file_path: Path, code: str):
        """Check for data minimization principle violations"""
        
        # Look for excessive data collection
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check functions that collect user data
                if self._is_data_collection_function(node):
                    collected_fields = self._extract_collected_fields(node)
                    
                    # Flag if collecting many fields without purpose limitation
                    if len(collected_fields) > 10:
                        self.findings.append(Finding(
                            rule="GDPR_DATA_EXCESSIVE",
                            severity=Severity.MEDIUM,
                            file=file_path.as_posix(),
                            line=node.lineno,
                            snippet=self._get_line(code, node.lineno),
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["compliance"],
                                severity="medium",
                                article="Art. 5",
                                legal_basis_required=True,
                                category="compliance",
                                confidence=0.6,
                                reasoning="Collecting excessive amount of data fields",
                                gdpr_articles=["Art. 5(1)(c)"]
                            )
                        ))
    
    # ============================================================================
    # LEGAL BASIS
    # ============================================================================
    
    def _check_legal_basis(self, tree: ast.AST, file_path: Path, code: str):
        """Check for legal basis documentation"""
        
        # Look for data processing without legal basis tracking
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Functions that process sensitive data
                if self._processes_sensitive_data(node):
                    # Check for legal_basis parameter or field
                    if not self._has_legal_basis_tracking(node):
                        self.findings.append(Finding(
                            rule="GDPR_LEGAL_BASIS_MISSING",
                            severity=Severity.HIGH,
                            file=file_path.as_posix(),
                            line=node.lineno,
                            snippet=self._get_line(code, node.lineno),
                            classification=ClassificationResult(
                                pii_types=[],
                                sectors=["compliance"],
                                severity="high",
                                article="Art. 6",
                                legal_basis_required=True,
                                category="compliance",
                                confidence=0.7,
                                reasoning="Sensitive data processing without legal basis tracking",
                                gdpr_articles=["Art. 6", "Art. 9"]
                            )
                        ))
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _get_line(self, code: str, line_no: int) -> str:
        """Extract specific line from code"""
        lines = code.split('\n')
        if 0 < line_no <= len(lines):
            return lines[line_no - 1].strip()
        return ""
    
    def _is_data_collection_call(self, node: ast.Call) -> bool:
        """Check if this is a data collection call"""
        collection_keywords = ['collect', 'gather', 'fetch_user', 'get_user', 'create_user', 'save_user']
        
        if isinstance(node.func, ast.Attribute):
            if any(kw in node.func.attr.lower() for kw in collection_keywords):
                return True
        if isinstance(node.func, ast.Name):
            if any(kw in node.func.id.lower() for kw in collection_keywords):
                return True
        return False
    
    def _has_consent_check_in_context(self, tree: ast.AST, target_node: ast.AST) -> bool:
        """Check if there's a consent check near the target node"""
        # Simple check: look for consent-related variable names in the same function
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if 'consent' in node.id.lower() or 'agree' in node.id.lower():
                    return True
        return False
    
    def _is_data_model_class(self, node: ast.ClassDef) -> bool:
        """Check if this is a data model class"""
        # Check for common ORM base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ['Model', 'Base', 'Document']:
                    return True
            if isinstance(base, ast.Attribute):
                if base.attr in ['Model', 'Base', 'Document']:
                    return True
        
        # Check for table/collection name indicators
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id in ['__tablename__', '__collection__']:
                            return True
        return False
    
    def _has_retention_or_expiry_field(self, node: ast.ClassDef) -> bool:
        """Check if model has retention/expiry field"""
        retention_keywords = ['expires_at', 'deleted_at', 'retention_date', 'expiry', 'ttl', 'created_at']
        
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    if any(kw in item.target.id.lower() for kw in retention_keywords):
                        return True
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if any(kw in target.id.lower() for kw in retention_keywords):
                            return True
        return False
    
    def _has_deletion_method(self, node: ast.ClassDef) -> bool:
        """Check if model has deletion/cleanup method"""
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if 'delete' in item.name.lower() or 'cleanup' in item.name.lower():
                    return True
        return False
    
    def _is_data_collection_function(self, node: ast.FunctionDef) -> bool:
        """Check if function collects user data"""
        collection_keywords = ['collect', 'gather', 'create_user', 'register', 'signup']
        return any(kw in node.name.lower() for kw in collection_keywords)
    
    def _extract_collected_fields(self, node: ast.FunctionDef) -> List[str]:
        """Extract field names being collected in function"""
        fields = []
        
        for child in ast.walk(node):
            # Look for dictionary creation or object assignment
            if isinstance(child, ast.Dict):
                for key in child.keys:
                    if isinstance(key, ast.Constant):
                        fields.append(key.value)
        
        return fields
    
    def _processes_sensitive_data(self, node: ast.FunctionDef) -> bool:
        """Check if function processes sensitive data"""
        sensitive_keywords = ['password', 'ssn', 'health', 'medical', 'biometric', 'genetic']
        
        # Check function name
        if any(kw in node.name.lower() for kw in sensitive_keywords):
            return True
        
        # Check parameters
        for arg in node.args.args:
            if any(kw in arg.arg.lower() for kw in sensitive_keywords):
                return True
        
        return False
    
    def _has_legal_basis_tracking(self, node: ast.FunctionDef) -> bool:
        """Check if function tracks legal basis"""
        # Check for legal_basis parameter
        for arg in node.args.args:
            if 'legal_basis' in arg.arg.lower():
                return True
        
        # Check for legal_basis variable usage
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if 'legal_basis' in child.id.lower():
                    return True
        
        return False
