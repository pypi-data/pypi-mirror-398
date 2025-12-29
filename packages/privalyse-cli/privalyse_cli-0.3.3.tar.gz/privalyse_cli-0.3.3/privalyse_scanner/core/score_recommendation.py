"""
Score-based recommendations for compliance improvement
"""
from typing import Tuple


def get_score_recommendation(score: float, critical_count: int, high_count: int) -> str:
    """
    Provide actionable recommendation based on compliance score
    
    Args:
        score: Compliance score (0-100)
        critical_count: Number of critical findings
        high_count: Number of high severity findings
    
    Returns:
        Actionable recommendation string
    """
    if score >= 90:
        return "✅ Excellent! Minor improvements possible."
    
    elif score >= 75:
        if high_count > 0:
            return f"🟢 Good standing. Address {high_count} high-priority item(s) to reach 90+."
        return "🟢 Good compliance. Review medium-priority items."
    
    elif score >= 60:
        if critical_count > 0:
            return f"🟡 Needs attention. Fix {critical_count} critical issue(s) first."
        return f"🟡 Moderate risk. Address {high_count} high-priority findings."
    
    elif score >= 40:
        action_items = []
        if critical_count > 0:
            action_items.append(f"{critical_count} critical")
        if high_count > 0:
            action_items.append(f"{high_count} high")
        
        items = " + ".join(action_items)
        return f"🔴 Critical: Immediate action required on {items} priority items."
    
    else:
        # Severe situation
        total_urgent = critical_count + high_count
        return (
            f"❌ Severe risk: {total_urgent} urgent items require immediate attention. "
            f"Start with {min(3, critical_count)} critical findings."
        )
