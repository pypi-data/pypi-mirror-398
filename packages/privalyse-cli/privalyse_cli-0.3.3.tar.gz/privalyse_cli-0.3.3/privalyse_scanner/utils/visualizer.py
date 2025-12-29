"""
Visualization utilities for Privalyse CLI
"""

from typing import List, Dict, Any, Optional
import sys

class FlowVisualizer:
    """Generates ASCII visualizations for data flows"""
    
    @staticmethod
    def visualize_flow(finding: Dict[str, Any]) -> str:
        """
        Generate an ASCII tree representation of a data flow finding.
        
        Format:
        [HIGH] PII Leak Detected
        └── 📧 User Email (input.py:12)
            ⬇️
            📝 Formatted String (utils.py:45)
            ⬇️
            ☁️ External API (client.py:88)
        """
        lines = []
        
        # Header
        severity = finding.get('severity', 'UNKNOWN').upper()
        rule = finding.get('rule', 'UNKNOWN')
        lines.append(f"[{severity}] {rule}")
        
        # Flow Path
        # We expect finding to have 'flow_path' or 'tainted_variables'
        # For now, we'll construct a simplified view based on available data
        
        # 1. Source
        source_node = finding.get('source_node') or "Unknown Source"
        # Try to find source details in taint_sources
        taint_sources = finding.get('taint_sources', [])
        if taint_sources:
            source_node = taint_sources[0]
            
        lines.append(f"└── 🟢 {source_node}")
        
        # 2. Intermediate Steps (if available in flow_path)
        flow_path = finding.get('flow_path', [])
        # If flow_path is just a list of strings (vars), show them
        if flow_path:
            for step in flow_path:
                if step != source_node and step != finding.get('sink_node'):
                    lines.append("    ⬇️")
                    lines.append(f"    🔄 {step}")
        
        # 3. Sink (The finding location)
        sink_node = finding.get('sink_node') or "Sink"
        file_loc = f"({finding.get('file')}:{finding.get('line')})"
        
        lines.append("    ⬇️")
        lines.append(f"    🔴 {sink_node} {file_loc}")
        
        return "\n".join(lines)

    @staticmethod
    def print_summary(results: Dict[str, Any]):
        """Print a visual summary of findings"""
        findings = results.get('findings', [])
        if not findings:
            return

        print("\n🔍 Top Data Flow Risks:\n")
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_findings = sorted(
            findings, 
            key=lambda x: severity_order.get(x.get('severity', 'info'), 5)
        )
        
        # Show top 3 critical/high/medium/low/info findings with flow visualization
        count = 0
        for finding in sorted_findings:
            if finding.get('severity') in ('critical', 'high', 'medium', 'low', 'info'):
                print(FlowVisualizer.visualize_flow(finding))
                print("") # Empty line
                count += 1
                if count >= 3:
                    break
        
        if count == 0:
            print("No critical data flows detected. Good job! 🛡️")
        elif len(findings) > count:
            print(f"... and {len(findings) - count} more findings in the report.")
