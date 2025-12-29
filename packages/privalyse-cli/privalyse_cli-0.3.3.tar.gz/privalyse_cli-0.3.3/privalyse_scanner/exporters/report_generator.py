from typing import List, Dict, Any, Union, Optional
from collections import defaultdict
from pathlib import Path
from privalyse_scanner.models.finding import Finding, Severity

class ReportGenerator:
    """
    Service to process raw findings into structured report data.
    Used by all exporters (JSON, Markdown, HTML) to ensure consistency.
    """

    def __init__(self, findings: List[Union[Finding, Dict[str, Any]]], metadata: Dict[str, Any] = None):
        self.findings = findings
        self.metadata = metadata or {}
        self.processed_data = self._process_data()

    def _get_attr(self, finding: Union[Finding, Dict[str, Any]], attr: str, default: Any = None) -> Any:
        """Helper to get attribute from object or dict"""
        if isinstance(finding, dict):
            return finding.get(attr, default)
        return getattr(finding, attr, default)

    def _to_dict(self, finding: Union[Finding, Dict[str, Any]]) -> Dict[str, Any]:
        """Helper to convert finding to dict"""
        if isinstance(finding, dict):
            return finding
        return finding.to_dict()

    def _process_data(self) -> Dict[str, Any]:
        """Process all data once"""
        return {
            "summary": self._generate_summary(),
            "compliance": self._group_by_compliance(),
            "files": self._group_by_file(),
            "findings": [self._to_dict(f) for f in self.findings],
            "metadata": self.metadata
        }

    def _generate_summary(self) -> Dict[str, int]:
        """Count findings by severity"""
        summary = {
            "total": len(self.findings),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        for f in self.findings:
            sev = self._get_attr(f, 'severity')
            if hasattr(sev, 'value'):
                sev = sev.value
            
            if sev in summary:
                summary[sev] += 1
        return summary

    def _group_by_compliance(self) -> Dict[str, Dict[str, Any]]:
        """Group findings by GDPR Article"""
        compliance_map = defaultdict(lambda: {"description": "", "findings": [], "count": 0})
        
        # Article descriptions
        descriptions = {
            "GDPR-5": "Principles relating to processing of personal data",
            "GDPR-6": "Lawfulness of processing",
            "GDPR-9": "Processing of special categories of personal data",
            "GDPR-32": "Security of processing",
        }

        for f in self.findings:
            # Check classification for GDPR articles
            classification = self._get_attr(f, 'classification')
            articles = []
            
            if classification:
                if isinstance(classification, dict):
                    articles = classification.get('gdpr_articles', []) or [classification.get('article')]
                else:
                    articles = getattr(classification, 'gdpr_articles', []) or [getattr(classification, 'article', None)]
            
            # Filter out None
            articles = [a for a in articles if a]

            for art in articles:
                # Normalize article string if needed
                key = art.upper()
                if "ART" in key and "GDPR" not in key:
                     key = key.replace("ART", "GDPR")
                
                compliance_map[key]["findings"].append(self._to_dict(f))
                compliance_map[key]["count"] += 1
                if key in descriptions:
                    compliance_map[key]["description"] = descriptions[key]
                elif not compliance_map[key]["description"]:
                     compliance_map[key]["description"] = f"Violation of {key}"

        return dict(compliance_map)

    def _group_by_file(self) -> Dict[str, Dict[str, Any]]:
        """Group findings by file and calculate risk score"""
        file_map = defaultdict(lambda: {"score": 0, "findings_count": 0, "findings": [], "critical_count": 0})
        
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1,
            "info": 0
        }

        for f in self.findings:
            file_val = self._get_attr(f, 'file')
            file_path = file_val.as_posix() if isinstance(file_val, Path) else str(file_val)
            sev = self._get_attr(f, 'severity')
            if hasattr(sev, 'value'):
                sev = sev.value
            
            file_map[file_path]["findings"].append(self._to_dict(f))
            file_map[file_path]["findings_count"] += 1
            file_map[file_path]["score"] += severity_weights.get(sev, 0)
            if sev == "critical":
                file_map[file_path]["critical_count"] += 1

        # Sort files by score (descending)
        sorted_files = dict(sorted(file_map.items(), key=lambda item: item[1]['score'], reverse=True))
        return sorted_files

    def get_data(self) -> Dict[str, Any]:
        """Return the structured data"""
        return self.processed_data
