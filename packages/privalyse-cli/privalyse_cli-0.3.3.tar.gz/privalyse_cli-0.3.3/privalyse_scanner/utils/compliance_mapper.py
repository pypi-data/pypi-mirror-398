"""
Compliance Data Mapper
Maps scanner classification results to normalized database IDs
"""

from typing import List, Dict, Any, Optional, Set
import re


# =====================================================
# GDPR ARTICLE MAPPING
# =====================================================

GDPR_ARTICLE_PATTERNS = {
    # Lawful basis
    'Art. 6(1)(a)': ['consent', 'einwilligung'],
    'Art. 6(1)(b)': ['contract', 'vertrag', 'contractual'],
    'Art. 6(1)(c)': ['legal obligation', 'rechtliche verpflichtung', 'compliance'],
    'Art. 6(1)(d)': ['vital interests', 'lebenswichtige interessen', 'emergency'],
    'Art. 6(1)(e)': ['public task', 'öffentliche aufgabe', 'public interest'],
    'Art. 6(1)(f)': ['legitimate interests', 'berechtigte interessen', 'legitimate'],
    
    # Special categories
    'Art. 9(1)': ['special category', 'besondere kategorie', 'sensitive', 'sensibel'],
    'Art. 9(2)(a)': ['explicit consent', 'ausdrückliche einwilligung'],
    'Art. 9(2)(h)': ['health', 'healthcare', 'gesundheit', 'medical', 'medizin'],
    
    # Transparency
    'Art. 13': ['information provided', 'direct collection', 'informationspflicht'],
    'Art. 14': ['indirect collection', 'indirekte erhebung'],
    
    # Data subject rights
    'Art. 15': ['right of access', 'auskunftsrecht', 'access request'],
    'Art. 16': ['rectification', 'berichtigung', 'correction'],
    'Art. 17': ['erasure', 'deletion', 'löschung', 'right to be forgotten'],
    'Art. 18': ['restriction', 'einschränkung'],
    'Art. 20': ['portability', 'übertragbarkeit', 'data export'],
    'Art. 21': ['object', 'widerspruch', 'opt-out'],
    
    # Security
    'Art. 32': ['security', 'sicherheit', 'encryption', 'verschlüsselung', 'protection'],
    'Art. 33': ['breach notification', 'meldung', 'data breach'],
    'Art. 34': ['breach communication', 'benachrichtigung'],
    
    # Accountability
    'Art. 5(2)': ['accountability', 'rechenschaftspflicht'],
    'Art. 24': ['controller responsibility', 'verantwortung'],
    'Art. 25': ['privacy by design', 'data protection by design', 'privacy by default'],
    'Art. 30': ['records of processing', 'verzeichnis', 'processing records'],
    'Art. 35': ['DPIA', 'impact assessment', 'folgenabschätzung'],
    
    # Criminal records
    'Art. 10': ['criminal', 'vorstrafen', 'conviction'],
}


def map_gdpr_articles(classification: Dict[str, Any], description: str = "") -> List[str]:
    """
    Map classification data to GDPR article references
    
    Args:
        classification: Classification result dict with 'article', 'category', etc.
        description: Additional context (rule description, snippet, etc.)
    
    Returns:
        List of GDPR article references (e.g., ['Art. 6(1)(a)', 'Art. 32'])
    """
    articles = set()
    
    # Direct article from classification
    if classification.get('article'):
        article = classification['article']
        # Normalize format
        if not article.startswith('Art.'):
            article = f'Art. {article}'
        articles.add(article)
    
    # Infer from PII types
    pii_types = classification.get('pii_types', [])
    if isinstance(pii_types, str):
        pii_types = [pii_types]
    
    for pii_type in pii_types:
        pii_lower = pii_type.lower()
        
        # Special categories (Art. 9)
        if any(keyword in pii_lower for keyword in ['health', 'medical', 'biometric', 'genetic', 'racial', 'ethnic', 'political', 'religious', 'sexual', 'trade_union']):
            articles.add('Art. 9(1)')
            if 'health' in pii_lower or 'medical' in pii_lower:
                articles.add('Art. 9(2)(h)')
        
        # Criminal records (Art. 10)
        if 'criminal' in pii_lower or 'conviction' in pii_lower:
            articles.add('Art. 10')
        
        # Security-related (Art. 32)
        if any(keyword in pii_lower for keyword in ['password', 'token', 'api_key', 'secret', 'credential']):
            articles.add('Art. 32')
    
    # Infer from category
    category = classification.get('category', '').lower()
    if 'special' in category:
        articles.add('Art. 9(1)')
    if 'security' in category or 'credential' in category:
        articles.add('Art. 32')
    
    # Pattern matching in description
    combined_text = f"{description} {classification.get('reasoning', '')}".lower()
    for article_ref, patterns in GDPR_ARTICLE_PATTERNS.items():
        if any(pattern in combined_text for pattern in patterns):
            articles.add(article_ref)
    
    # Default fallback: Personal data requires lawful basis (Art. 6)
    if not articles and pii_types:
        articles.add('Art. 6(1)')
    
    return sorted(list(articles))


# =====================================================
# PII TYPE MAPPING
# =====================================================

PII_TYPE_NORMALIZATION = {
    # Identifiers
    'email': 'email',
    'e-mail': 'email',
    'email_address': 'email',
    'phone': 'phone',
    'phone_number': 'phone',
    'telephone': 'phone',
    'name': 'name',
    'full_name': 'name',
    'first_name': 'name',
    'last_name': 'name',
    'username': 'user_id',
    'user_id': 'user_id',
    'userid': 'user_id',
    
    # Location
    'address': 'address',
    'street_address': 'address',
    'postal_address': 'address',
    'ip_address': 'ip_address',
    'ip': 'ip_address',
    'geolocation': 'geolocation',
    'location': 'geolocation',
    'gps': 'geolocation',
    
    # Financial
    'credit_card': 'credit_card',
    'creditcard': 'credit_card',
    'card_number': 'credit_card',
    'iban': 'iban',
    'bank_account': 'iban',
    
    # Identification documents
    'ssn': 'ssn',
    'social_security': 'ssn',
    'passport': 'passport',
    'passport_number': 'passport',
    'drivers_license': 'drivers_license',
    'license': 'drivers_license',
    
    # Special categories (Art. 9)
    'health': 'health_data',
    'health_data': 'health_data',
    'medical': 'health_data',
    'medical_data': 'health_data',
    'biometric': 'biometric',
    'biometric_data': 'biometric',
    'fingerprint': 'biometric',
    'facial': 'biometric',
    'genetic': 'genetic',
    'genetic_data': 'genetic',
    'dna': 'genetic',
    
    'racial': 'racial_ethnic',
    'ethnic': 'racial_ethnic',
    'race': 'racial_ethnic',
    'ethnicity': 'racial_ethnic',
    'political': 'political_opinion',
    'political_opinion': 'political_opinion',
    'religious': 'religious_belief',
    'religion': 'religious_belief',
    'religious_belief': 'religious_belief',
    'trade_union': 'trade_union',
    'union': 'trade_union',
    'sexual': 'sexual_orientation',
    'sexual_orientation': 'sexual_orientation',
    
    # Criminal records (Art. 10)
    'criminal': 'criminal_record',
    'criminal_record': 'criminal_record',
    'conviction': 'criminal_record',
    
    # Security
    'password': 'password',
    'pwd': 'password',
    'credential': 'password',
    'token': 'api_key',
    'api_key': 'api_key',
    'apikey': 'api_key',
    'secret': 'api_key',
    
    # Devices
    'device_id': 'device_id',
    'deviceid': 'device_id',
    'cookie': 'cookie_id',
    'cookie_id': 'cookie_id',
}


def normalize_pii_types(pii_types: List[str]) -> List[str]:
    """
    Normalize PII type names to match database catalog
    
    Args:
        pii_types: List of PII type strings from classification
    
    Returns:
        List of normalized PII type codes that exist in pii_types_catalog
    """
    if isinstance(pii_types, str):
        pii_types = [pii_types]
    
    normalized = set()
    for pii_type in pii_types:
        pii_lower = pii_type.lower().strip().replace(' ', '_').replace('-', '_')
        
        # Direct lookup
        if pii_lower in PII_TYPE_NORMALIZATION:
            normalized.add(PII_TYPE_NORMALIZATION[pii_lower])
        else:
            # Partial match
            for key, value in PII_TYPE_NORMALIZATION.items():
                if key in pii_lower or pii_lower in key:
                    normalized.add(value)
                    break
            else:
                # Keep original if no mapping found (will be filtered later)
                normalized.add(pii_lower)
    
    return sorted(list(normalized))


# =====================================================
# TOM RECOMMENDATIONS
# =====================================================

TOM_CATALOG = {
    'ENC-001': 'Encryption of data at rest',
    'ENC-002': 'Encryption of data in transit (TLS/SSL)',
    'ACC-001': 'Role-Based Access Control (RBAC)',
    'ACC-002': 'Multi-Factor Authentication (MFA)',
    'ACC-003': 'Access Logging & Monitoring',
    'ACC-004': 'Principle of Least Privilege',
    'PSC-001': 'Pseudonymization of personal data',
    'BAK-001': 'Regular data backups',
    'BAK-002': 'Encryption of backups',
    'LOG-001': 'Comprehensive audit logging',
    'LOG-002': 'Defined log retention policy',
    'PRI-001': 'Privacy by Design & Default implementation',
    'PRI-002': 'Data Protection Impact Assessment (DPIA)',
    'PRI-003': 'Data Minimization strategies',
    'POL-001': 'Comprehensive Data Protection Policy',
    'POL-003': 'Incident Response Plan',
    'TRN-001': 'Regular Staff Data Protection Training'
}

def recommend_toms(classification: Dict[str, Any], rule_id: str) -> List[Dict[str, Any]]:
    """
    Recommend technical and organizational measures (TOMs) for a finding
    
    Args:
        classification: Classification result
        rule_id: Rule that triggered the finding
    
    Returns:
        List of TOM recommendations with code, description, and priority
    """
    toms = []
    
    pii_types = classification.get('pii_types', [])
    if isinstance(pii_types, str):
        pii_types = [pii_types]
    
    severity = classification.get('severity', 'medium')
    category = classification.get('category', '')
    
    # Security credentials detected
    if any(t in ['password', 'api_key', 'token', 'secret', 'credential'] for t in normalize_pii_types(pii_types)):
        toms.append({'code': 'ENC-001', 'priority': 'required'})  # Encryption at rest
        toms.append({'code': 'ENC-002', 'priority': 'required'})  # Encryption in transit
        toms.append({'code': 'ACC-002', 'priority': 'required'})  # MFA
        toms.append({'code': 'ACC-003', 'priority': 'recommended'})  # Access logging
    
    # Special categories (Art. 9)
    if 'special' in category.lower() or any(t in ['health_data', 'biometric', 'genetic', 'racial_ethnic'] for t in normalize_pii_types(pii_types)):
        toms.append({'code': 'ENC-001', 'priority': 'required'})  # Encryption
        toms.append({'code': 'PSC-001', 'priority': 'required'})  # Pseudonymization
        toms.append({'code': 'ACC-001', 'priority': 'required'})  # RBAC
        toms.append({'code': 'PRI-002', 'priority': 'required'})  # DPIA
    
    # Logging detected (rule type)
    if 'LOG' in rule_id:
        toms.append({'code': 'LOG-001', 'priority': 'required'})  # Audit logging
        toms.append({'code': 'LOG-002', 'priority': 'recommended'})  # Log retention policy
        toms.append({'code': 'PRI-003', 'priority': 'recommended'})  # Data minimization
    
    # HTTP transmission (rule type)
    if 'HTTP' in rule_id:
        toms.append({'code': 'ENC-002', 'priority': 'required'})  # TLS/SSL
        toms.append({'code': 'ACC-003', 'priority': 'recommended'})  # Access logging
    
    # Database storage (rule type)
    if 'DB' in rule_id:
        toms.append({'code': 'ENC-001', 'priority': 'required'})  # Encryption at rest
        toms.append({'code': 'BAK-001', 'priority': 'required'})  # Regular backups
        toms.append({'code': 'BAK-002', 'priority': 'required'})  # Backup encryption
        toms.append({'code': 'ACC-001', 'priority': 'recommended'})  # RBAC
    
    # High severity - always recommend comprehensive measures
    if severity in ['critical', 'high']:
        toms.append({'code': 'TRN-001', 'priority': 'recommended'})  # GDPR training
        toms.append({'code': 'POL-003', 'priority': 'recommended'})  # Incident response
        toms.append({'code': 'PRI-001', 'priority': 'recommended'})  # Privacy by design
    
    # Default recommendations for any PII
    if pii_types and not toms:
        toms.append({'code': 'ACC-001', 'priority': 'recommended'})  # RBAC
        toms.append({'code': 'ACC-004', 'priority': 'recommended'})  # Least privilege
        toms.append({'code': 'POL-001', 'priority': 'recommended'})  # Data protection policy
    
    # Remove duplicates while preserving order and adding descriptions
    seen = set()
    unique_toms = []
    for tom in toms:
        if tom['code'] not in seen:
            seen.add(tom['code'])
            # Add description from catalog
            tom['description'] = TOM_CATALOG.get(tom['code'], 'Technical measure')
            unique_toms.append(tom)
    
    return unique_toms


# =====================================================
# COMPLETE MAPPING FUNCTION
# =====================================================

def map_finding_to_compliance(
    finding: Dict[str, Any],
    rule_id: str
) -> Dict[str, Any]:
    """
    Map a scanner finding to normalized compliance data
    
    Args:
        finding: Finding dict with classification
        rule_id: Rule ID that triggered finding
    
    Returns:
        Dict with:
        - gdpr_articles: List of article references
        - pii_types: List of normalized PII type codes
        - tom_recommendations: List of TOM recommendation dicts
    """
    classification = finding.get('classification', {})
    description = finding.get('snippet', '')
    
    return {
        'gdpr_articles': map_gdpr_articles(classification, description),
        'pii_types': normalize_pii_types(classification.get('pii_types', [])),
        'tom_recommendations': recommend_toms(classification, rule_id),
        'confidence': classification.get('confidence', 0.5),
        'severity': classification.get('severity', 'medium'),
    }


# =====================================================
# EXPORT
# =====================================================

__all__ = [
    'map_gdpr_articles',
    'normalize_pii_types',
    'recommend_toms',
    'map_finding_to_compliance',
]
