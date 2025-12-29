import json
from typing import Dict, Any, List, Union
from pathlib import Path
from privalyse_scanner.models.finding import Finding
from privalyse_scanner.exporters.report_generator import ReportGenerator

class JSONExporter:
    """
    Export scan results to a structured JSON file.
    """

    def export(self, findings: List[Union[Finding, Dict[str, Any]]], metadata: Dict[str, Any]) -> str:
        """
        Generate structured JSON report.
        
        Args:
            findings: List of Finding objects
            metadata: Scan metadata
            
        Returns:
            JSON string
        """
        generator = ReportGenerator(findings, metadata)
        data = generator.get_data()
        
        return json.dumps(data, indent=2, default=str)
