"""Data models for scan findings and classifications"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    """Finding severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ClassificationResult:
    """Structured result for PII classification"""
    pii_types: List[str]
    sectors: List[str]
    severity: str
    article: Optional[str]
    legal_basis_required: bool
    category: str
    confidence: float
    reasoning: str = ""
    gdpr_articles: List[str] = field(default_factory=list)  # NEW: Support multiple GDPR articles
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "pii_types": self.pii_types,
            "sectors": self.sectors,
            "severity": self.severity,
            "article": self.article,
            "gdpr_articles": self.gdpr_articles,
            "legal_basis_required": self.legal_basis_required,
            "category": self.category,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass
class Finding:
    """Represents a single scan finding"""
    rule: str
    severity: Severity
    file: str
    line: int
    snippet: str
    classification: ClassificationResult
    
    # Optional metadata
    data_flow_type: Optional[str] = None
    tainted_variables: List[str] = field(default_factory=list)
    taint_sources: List[str] = field(default_factory=list)
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # New fields for Semantic Data Flow Graph
    source_node: Optional[str] = None
    sink_node: Optional[str] = None
    flow_path: List[str] = field(default_factory=list)

    # AI Agent Context
    suggested_fix: Optional[str] = None
    confidence_score: float = 1.0
    context_start_line: Optional[int] = None
    context_end_line: Optional[int] = None
    code_context: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        file_path = self.file
        if isinstance(file_path, Path):
            file_path = file_path.as_posix()
        elif isinstance(file_path, str):
            # Ensure even string paths are normalized to forward slashes
            file_path = file_path.replace('\\', '/')

        result = {
            "rule": self.rule,
            "severity": self.severity.value if isinstance(self.severity, Severity) else self.severity,
            "file": file_path,
            "line": self.line,
            "snippet": self.snippet,
            "classification": self.classification.to_dict() if hasattr(self.classification, 'to_dict') else self.classification,
        }
        
        # Add optional fields if present
        if self.data_flow_type:
            result["data_flow_type"] = self.data_flow_type
        if self.tainted_variables:
            result["tainted_variables"] = self.tainted_variables
        if self.taint_sources:
            result["taint_sources"] = self.taint_sources
        if self.url:
            result["url"] = self.url
        if self.metadata:
            result["metadata"] = self.metadata
            
        # Add graph fields
        if self.source_node:
            result["source_node"] = self.source_node
        if self.sink_node:
            result["sink_node"] = self.sink_node
        if self.flow_path:
            result["flow_path"] = self.flow_path
        
        # Add AI Agent fields
        if self.suggested_fix:
            result["suggested_fix"] = self.suggested_fix
        result["confidence_score"] = self.confidence_score
        if self.context_start_line:
            result["context_start_line"] = self.context_start_line
        if self.context_end_line:
            result["context_end_line"] = self.context_end_line
        if self.code_context:
            result["code_context"] = self.code_context

        return result
