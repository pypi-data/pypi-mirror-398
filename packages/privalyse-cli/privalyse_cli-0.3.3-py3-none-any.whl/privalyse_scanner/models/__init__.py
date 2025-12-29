"""Data models for scanner findings, configuration, and results"""

from .finding import Finding, Severity, ClassificationResult
from .config import ScanConfig
from .taint import TaintInfo, DataFlowEdge, TaintTracker

__all__ = [
    "Finding",
    "Severity",
    "ClassificationResult",
    "ScanConfig",
    "TaintInfo",
    "DataFlowEdge",
    "TaintTracker",
]
