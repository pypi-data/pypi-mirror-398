"""
Infrastructure Analyzer - Checks Docker and Configuration files for security issues
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models.finding import Finding, Severity, ClassificationResult
from .base_analyzer import BaseAnalyzer, AnalyzedSymbol, AnalyzedImport


class InfrastructureAnalyzer(BaseAnalyzer):
    """Analyzes infrastructure files (Docker, YAML, Config) for security issues"""
    
    def __init__(self):
        self.findings = []
        
        # Patterns for sensitive keys in config/env files
        self.sensitive_key_pattern = re.compile(r'(password|secret|key|token|auth|credential|pwd)', re.IGNORECASE)
        
        # Patterns for sensitive values (heuristic)
        self.sensitive_value_pattern = re.compile(r'[a-zA-Z0-9]{20,}') # Long random strings
        
        # Known default passwords
        self.default_passwords = ['root', 'admin', 'password', '123456', 'postgres', 'mysql']

    def extract_symbols(self, code: str) -> List[AnalyzedSymbol]:
        """Not applicable for infra files"""
        return []

    def extract_imports(self, code: str) -> List[AnalyzedImport]:
        """Not applicable for infra files"""
        return []

    def analyze_file(self, file_path: Path, code: str, **kwargs) -> List[Finding]:
        """
        Analyze infrastructure file
        """
        self.findings = []
        filename = file_path.name
        
        if filename == 'Dockerfile' or filename.endswith('.dockerfile'):
            self._analyze_dockerfile(file_path, code)
        elif filename in ['docker-compose.yml', 'docker-compose.yaml']:
            self._analyze_docker_compose(file_path, code)
        elif file_path.suffix in ['.env', '.ini', '.toml', '.json', '.yaml', '.yml']:
            self._analyze_generic_config(file_path, code)
            
        return self.findings

    def _analyze_dockerfile(self, file_path: Path, code: str):
        """Analyze Dockerfile for security issues"""
        lines = code.splitlines()
        
        for i, line in enumerate(lines):
            line_num = i + 1
            line_stripped = line.strip()
            
            # 1. Check for ADD/COPY of sensitive files
            if line_stripped.upper().startswith(('ADD', 'COPY')):
                if any(x in line_stripped for x in ['.env', 'id_rsa', 'id_dsa', '.pem', '.key', 'credentials']):
                    self.findings.append(Finding(
                        rule="DOCKER_SENSITIVE_COPY",
                        severity=Severity.HIGH,
                        file=file_path.as_posix(),
                        line=line_num,
                        snippet=line.strip(),
                        classification=ClassificationResult(
                            pii_types=[],
                            category="security_misconfiguration",
                            severity="high",
                            confidence=0.95,
                            reasoning="Sensitive file copied into Docker image",
                            sectors=[],
                            article="Art. 32",
                            legal_basis_required=True
                        )
                    ))

            # 2. Check for ENV with secrets
            if line_stripped.upper().startswith('ENV'):
                # ENV VAR_NAME=value or ENV VAR_NAME value
                parts = line_stripped.split(maxsplit=1)
                if len(parts) > 1:
                    args = parts[1]
                    # Simple check for key=value
                    if '=' in args:
                        key, val = args.split('=', 1)
                        key = key.strip()
                        val = val.strip()
                        
                        if self.sensitive_key_pattern.search(key):
                            # Check if value looks like a hardcoded secret (not a variable reference like $VAR)
                            if not val.startswith('$') and len(val) > 0:
                                self.findings.append(Finding(
                                    rule="DOCKER_ENV_SECRET",
                                    severity=Severity.CRITICAL,
                                    file=file_path.as_posix(),
                                    line=line_num,
                                    snippet=line.strip(),
                                    classification=ClassificationResult(
                                        pii_types=["credentials"],
                                        category="security_misconfiguration",
                                        severity="critical",
                                        confidence=0.9,
                                        reasoning=f"Hardcoded secret '{key}' in Dockerfile ENV",
                                        sectors=[],
                                        article="Art. 32",
                                        legal_basis_required=True
                                    )
                                ))

    def _analyze_docker_compose(self, file_path: Path, code: str):
        """Analyze docker-compose.yml for security issues"""
        lines = code.splitlines()
        
        in_environment_block = False
        in_ports_block = False
        current_service = None
        
        for i, line in enumerate(lines):
            line_num = i + 1
            line_stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Detect service name (top level or under services:)
            # Simplified parsing: assume standard indentation
            
            # Detect blocks
            if line_stripped.startswith('environment:'):
                in_environment_block = True
                in_ports_block = False
                continue
            elif line_stripped.startswith('ports:'):
                in_ports_block = True
                in_environment_block = False
                continue
            elif line_stripped.endswith(':') and not line_stripped.startswith('-'):
                # Likely a new section or service
                in_environment_block = False
                in_ports_block = False
            
            # 1. Check Environment Variables
            if in_environment_block:
                # - KEY=VALUE or KEY: VALUE
                if '=' in line_stripped:
                    key, val = line_stripped.lstrip('- ').split('=', 1)
                elif ':' in line_stripped:
                    key, val = line_stripped.lstrip('- ').split(':', 1)
                else:
                    continue
                
                key = key.strip()
                val = val.strip()
                
                if self.sensitive_key_pattern.search(key):
                    # Check for weak passwords
                    if val in self.default_passwords:
                        self.findings.append(Finding(
                            rule="DOCKER_WEAK_PASSWORD",
                            severity=Severity.HIGH,
                            file=file_path.as_posix(),
                            line=line_num,
                            snippet=line.strip(),
                            classification=ClassificationResult(
                                pii_types=["credentials"],
                                category="security_misconfiguration",
                                severity="high",
                                confidence=0.95,
                                reasoning=f"Weak default password '{val}' used for '{key}'",
                                sectors=[],
                                article="Art. 32",
                                legal_basis_required=True
                            )
                        ))
                    elif not val.startswith(('$', '{')) and len(val) > 0:
                         self.findings.append(Finding(
                            rule="DOCKER_COMPOSE_SECRET",
                            severity=Severity.HIGH,
                            file=file_path.as_posix(),
                            line=line_num,
                            snippet=line.strip(),
                            classification=ClassificationResult(
                                pii_types=["credentials"],
                                category="security_misconfiguration",
                                severity="high",
                                confidence=0.8,
                                reasoning=f"Hardcoded secret '{key}' in docker-compose",
                                sectors=[],
                                article="Art. 32",
                                legal_basis_required=True
                            )
                        ))

            # 2. Check Exposed Ports
            if in_ports_block and '-' in line_stripped:
                # - "8080:80" or - 8080:80
                port_def = line_stripped.lstrip('- ').strip('"\'')
                if ':' in port_def:
                    host_part = port_def.split(':')[0]
                    
                    # Check for sensitive ports exposed globally
                    sensitive_ports = ['5432', '3306', '6379', '27017', '9200']
                    for port in sensitive_ports:
                        if port in host_part:
                            # Check if bound to localhost
                            if '127.0.0.1' not in host_part and 'localhost' not in host_part:
                                self.findings.append(Finding(
                                    rule="DOCKER_EXPOSED_DB_PORT",
                                    severity=Severity.HIGH,
                                    file=file_path.as_posix(),
                                    line=line_num,
                                    snippet=line.strip(),
                                    classification=ClassificationResult(
                                        pii_types=[],
                                        category="security_misconfiguration",
                                        severity="high",
                                        confidence=0.9,
                                        reasoning=f"Database port {port} exposed to all interfaces (0.0.0.0)",
                                        sectors=[],
                                        article="Art. 32",
                                        legal_basis_required=True
                                    )
                                ))

    def _analyze_generic_config(self, file_path: Path, code: str):
        """Analyze generic config files for secrets"""
        lines = code.splitlines()
        
        for i, line in enumerate(lines):
            line_num = i + 1
            line_stripped = line.strip()
            
            # Skip comments
            if line_stripped.startswith(('#', '//', ';')):
                continue
                
            # Simple key-value detection
            if '=' in line_stripped:
                key, val = line_stripped.split('=', 1)
            elif ':' in line_stripped:
                key, val = line_stripped.split(':', 1)
            else:
                continue
                
            key = key.strip().strip('"\'')
            val = val.strip().strip('"\'')
            
            if self.sensitive_key_pattern.search(key):
                if not val.startswith(('$', '{', '%')) and len(val) > 0:
                     # Check for placeholders
                    if val.lower() in ['changeme', 'password', 'secret', 'todo', 'example']:
                        continue
                        
                    self.findings.append(Finding(
                        rule="CONFIG_HARDCODED_SECRET",
                        severity=Severity.HIGH,
                        file=file_path.as_posix(),
                        line=line_num,
                        snippet=line.strip(),
                        classification=ClassificationResult(
                            pii_types=["credentials"],
                            category="security_misconfiguration",
                            severity="high",
                            confidence=0.8,
                            reasoning=f"Potential hardcoded secret '{key}' in config file",
                            sectors=[],
                            article="Art. 32",
                            legal_basis_required=True
                        )
                    ))
