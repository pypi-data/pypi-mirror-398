"""PII classification utilities - DETERMINISTIC VERSION"""

import re
from typing import Dict, Any, Optional, List

# Import deterministic classifier
try:
    from .deterministic_rules import DeterministicClassifier
    USE_DETERMINISTIC = True
except ImportError:
    USE_DETERMINISTIC = False


# Legacy patterns kept for backward compatibility
PII_CLASSIFICATION_PATTERNS = {
    'email': [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\bemail\b', r'\bmail\b', r'\be_mail\b'
    ],
    'password': [
        r'\bpassword\b', r'\bpasswd\b', r'\bpwd\b', r'\bsecret\b'
    ],
    'token': [
        r'\btoken\b', r'\baccess_token\b', r'\brefresh_token\b', r'\bapi_key\b',
        r'\beyJ[A-Za-z0-9._-]{20,}\b'  # JWT pattern
    ],
    'id': [
        r'\buser_id\b', r'\bcustomer_id\b', r'\b(user|customer)_?id\b'
    ],
    'phone': [
        r'\bphone\b', r'\bmobile\b', r'\btel\b', r'\btelephone\b',
        r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
    ],
    'ssn': [
        r'\bssn\b', r'\bsocial_security\b',
        r'\b\d{3}-\d{2}-\d{4}\b'
    ],
    'address': [
        r'\baddress\b', r'\bstreet\b', r'\bcity\b', r'\bzip\b', r'\bpostal\b'
    ],
    'name': [
        r'\b(first|last|full)_?name\b', r'\bgivenname\b', r'\bsurname\b'
    ],
}


def classify_pii_enhanced(snippet: str, context: str, 
                         variable_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Classify PII in a code snippet using DETERMINISTIC rules
    
    Args:
        snippet: Code snippet to analyze
        context: Context description (e.g., "logging call in auth.py")
        variable_names: List of variable names in snippet for precise detection
    
    Returns:
        Dictionary with classification results
    """
    
    # Use deterministic classifier if available
    if USE_DETERMINISTIC:
        return DeterministicClassifier.classify_snippet(
            snippet=snippet,
            context=context,
            variable_names=variable_names or []
        )
    
    # LEGACY FALLBACK (should not be used)
    pii_types = []
    confidence = 0.5
    
    snippet_lower = snippet.lower()
    
    # Check each PII pattern
    for pii_type, patterns in PII_CLASSIFICATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, snippet_lower, re.IGNORECASE):
                pii_types.append(pii_type)
                confidence = max(confidence, 0.7)
                break
    
    # Deduplicate
    pii_types = list(set(pii_types))
    
    # Determine severity
    severity = "info"
    if any(t in pii_types for t in ['password', 'ssn', 'token']):
        severity = "high"
    elif any(t in pii_types for t in ['email', 'phone', 'address']):
        severity = "medium"
    
    # REMOVED: Overly broad Article 9 detection
    # Old code triggered Art. 9 on keywords like "health" in variable names
    # Now requires explicit special category data patterns
    article = None
    
    return {
        "pii_types": pii_types,
        "sectors": [],
        "severity": severity,
        "article": article,
        "legal_basis_required": len(pii_types) > 0,
        "category": "pii" if pii_types else "unknown",
        "confidence": confidence,
        "reasoning": f"Legacy classification: found {len(pii_types)} PII types"
    }
