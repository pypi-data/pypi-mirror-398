"""
Deterministic Privacy Scanner Rules
Eliminates false positives through precise pattern matching and context analysis
"""

import re
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass


@dataclass
class PIIPattern:
    """Deterministic PII detection pattern"""
    code: str  # PII type code (e.g., 'email', 'user_id')
    display_name: str
    patterns: List[str]  # Regex patterns
    variable_names: List[str]  # Variable name patterns
    excluded_contexts: List[str]  # Contexts where this is NOT PII
    gdpr_article: Optional[str] = None
    severity: str = "medium"


# ==================================================================================
# DETERMINISTIC PII PATTERNS
# ==================================================================================

DETERMINISTIC_PII_PATTERNS = [
    # IDENTIFIERS (Low risk - technical IDs)
    PIIPattern(
        code="user_id",
        display_name="User ID",
        patterns=[r'\buser_id\b', r'\buserid\b', r'\buser\.id\b'],
        variable_names=['user_id', 'userId', 'userid', 'user.id'],
        excluded_contexts=['correlation', 'task_id', 'scan_id', 'trace_id', 'event_type'],
        severity="info"
    ),
    PIIPattern(
        code="correlation_id",
        display_name="Correlation ID",
        patterns=[r'\bcorrelation_id\b', r'\btrace_id\b', r'\brequest_id\b'],
        variable_names=['correlation_id', 'trace_id', 'request_id', 'tracking_id'],
        excluded_contexts=[],
        severity="info"
    ),
    
    # PERSONAL IDENTIFIERS (Medium risk)
    PIIPattern(
        code="email",
        display_name="Email Address",
        patterns=[
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\bemail\b(?!\.com|\.de)',  # email variable, not domain
            r'\bemailAddress\b',  # React camelCase
            r'\buserEmail\b',
            r'\bmail\b(?!\.)',
            r'\be_mail\b'
        ],
        variable_names=['email', 'user_email', 'userEmail', 'email_address', 'emailAddress', 'mail', 'e_mail', 'contactEmail'],
        excluded_contexts=['email_sent', 'emailSent', 'email_verified', 'emailVerified', 'email_enabled', 'emailEnabled'],  # Flags, not actual emails
        severity="medium"
    ),
    PIIPattern(
        code="name",
        display_name="Personal Name",
        patterns=[
            r'\b(first|last|full)_?name\b',
            r'\b(first|last|full)Name\b',  # React camelCase
            r'\bgivenname\b',
            r'\bgivenName\b',
            r'\bsurname\b',
            r'\bvorname\b',
            r'\bnachname\b'
        ],
        variable_names=['name', 'first_name', 'firstName', 'last_name', 'lastName', 'full_name', 'fullName', 'username', 'givenName', 'familyName'],
        excluded_contexts=['project_name', 'projectName', 'file_name', 'fileName', 'organization_name', 'organizationName', 'role_name', 'roleName'],
        severity="medium"
    ),
    PIIPattern(
        code="phone",
        display_name="Phone Number",
        patterns=[
            r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            r'\bphone\b',
            r'\bphoneNumber\b',  # React camelCase
            r'\bmobile\b',
            r'\bmobileNumber\b',
            r'\btel\b',
            r'\btelephone\b'
        ],
        variable_names=['phone', 'phone_number', 'phoneNumber', 'mobile', 'mobileNumber', 'telephone', 'tel'],
        excluded_contexts=[],
        severity="medium"
    ),
    PIIPattern(
        code="address",
        display_name="Physical Address",
        patterns=[
            r'\b(street|postal|mailing)_?address\b',
            r'\b(street|postal|mailing)Address\b',  # React camelCase
            r'\bstreet\b.*\baddress\b',
            r'\bcity\b',
            r'\bzip_?code\b',
            r'\bzipCode\b',
            r'\bpostal_?code\b',
            r'\bpostalCode\b'
        ],
        variable_names=['address', 'street_address', 'streetAddress', 'postal_address', 'postalAddress', 'city', 'zipcode', 'zipCode', 'postalCode'],
        excluded_contexts=['ip_address', 'ipAddress', 'mac_address', 'macAddress', 'email_address', 'emailAddress'],
        severity="medium"
    ),
    PIIPattern(
        code="organization",
        display_name="Organization / Company Name",
        patterns=[
            r'\borganization_?name\b',
            r'\borganizationName\b',  # React camelCase
            r'\bcompany_?name\b',
            r'\bcompanyName\b',
            r'\borg_?name\b',
            r'\borgName\b'
        ],
        variable_names=['organization_name', 'organizationName', 'company_name', 'companyName', 'org_name', 'orgName', 'company', 'organization'],
        excluded_contexts=['project_name', 'projectName'],
        severity="low"
    ),
    
    # HIGH-RISK DATA
    PIIPattern(
        code="password",
        display_name="Password / Credential",
        patterns=[
            r'\bpassword\b',
            r'\bpasswd\b',
            r'\bpwd\b',
            r'\bnewPassword\b',  # React camelCase
            r'\boldPassword\b',
            r'\bconfirmPassword\b',
            r'\bcredential\b'
        ],
        variable_names=['password', 'passwd', 'pwd', 'newPassword', 'oldPassword', 'confirmPassword', 'password_hash', 'hashed_password', 'passwordHash', 'hashedPassword'],
        excluded_contexts=['password_reset', 'passwordReset', 'password_changed', 'passwordChanged', 'password_verified', 'passwordVerified'],  # Events
        gdpr_article="Art. 32",
        severity="high"
    ),
    PIIPattern(
        code="api_key",
        display_name="API Key / Token",
        patterns=[
            r'\bapi_key\b',
            r'\baccess_token\b',
            r'\brefresh_token\b',
            r'\bauth_token\b',
            r'\bbearer\s+[A-Za-z0-9._-]{20,}',
            r'\beyJ[A-Za-z0-9._-]{20,}\b'  # JWT pattern
        ],
        variable_names=['api_key', 'access_token', 'refresh_token', 'auth_token', 'bearer_token'],
        excluded_contexts=['token_expired', 'token_verified'],
        gdpr_article="Art. 32",
        severity="high"
    ),
    PIIPattern(
        code="ssn",
        display_name="Social Security Number",
        patterns=[
            r'\bssn\b',
            r'\bsocial_security\b',
            r'\b\d{3}-\d{2}-\d{4}\b'
        ],
        variable_names=['ssn', 'social_security_number'],
        excluded_contexts=[],
        severity="critical"
    ),
    PIIPattern(
        code="credit_card",
        display_name="Credit Card Number",
        patterns=[
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            r'\bcredit_card\b',
            r'\bcard_number\b',
            r'\bpan\b'  # Primary Account Number
        ],
        variable_names=['credit_card', 'card_number', 'pan', 'cc_number'],
        excluded_contexts=[],
        severity="critical"
    ),
]


# ==================================================================================
# ARTICLE 9 GDPR - SPECIAL CATEGORIES (Strict Detection)
# ==================================================================================

ARTICLE9_SPECIAL_CATEGORIES = {
    'health_data': {
        'display_name': 'Health / Medical Data',
        'patterns': [
            r'\b(health|medical)_data\b',  # Explicit variable names
            r'\b(diagnosis|prescription|treatment|medication)\b',
            r'\bpatient_record\b',
            r'\bmedical_history\b'
        ],
        'required_context': ['patient', 'medical', 'health', 'doctor', 'hospital', 'clinic'],
        'excluded_context': ['health_check', 'health_status', 'healthy'],  # System health checks
    },
    'biometric': {
        'display_name': 'Biometric Data',
        'patterns': [
            r'\bfingerprint\b',
            r'\bfacial_recognition\b',
            r'\biris_scan\b',
            r'\bvoice_print\b',
            r'\bbiometric_data\b'
        ],
        'required_context': ['biometric', 'scan', 'recognition'],
        'excluded_context': [],
    },
    'genetic': {
        'display_name': 'Genetic Data',
        'patterns': [
            r'\bgenetic_data\b',
            r'\bdna\b',
            r'\bgenome\b',
            r'\bgenetic_test\b'
        ],
        'required_context': ['genetic', 'dna', 'genome'],
        'excluded_context': [],
    },
    'racial_ethnic': {
        'display_name': 'Racial / Ethnic Origin',
        'patterns': [
            r'\b(race|ethnicity|ethnic_origin)\b'
        ],
        'required_context': ['race', 'ethnicity', 'ethnic', 'origin'],
        'excluded_context': [],
    },
    'political_opinion': {
        'display_name': 'Political Opinion',
        'patterns': [
            r'\bpolitical_(opinion|affiliation|party)\b'
        ],
        'required_context': ['political', 'party', 'affiliation'],
        'excluded_context': [],
    },
    'religious_belief': {
        'display_name': 'Religious / Philosophical Belief',
        'patterns': [
            r'\breligious_(belief|affiliation)\b',
            r'\breligion\b'
        ],
        'required_context': ['religion', 'belief', 'faith'],
        'excluded_context': [],
    },
    'sexual_orientation': {
        'display_name': 'Sexual Orientation',
        'patterns': [
            r'\bsexual_orientation\b'
        ],
        'required_context': ['sexual', 'orientation'],
        'excluded_context': [],
    },
    'trade_union': {
        'display_name': 'Trade Union Membership',
        'patterns': [
            r'\btrade_union\b',
            r'\bunion_member\b'
        ],
        'required_context': ['union', 'membership'],
        'excluded_context': [],
    },
}


# ==================================================================================
# DETERMINISTIC CLASSIFIER
# ==================================================================================

class DeterministicClassifier:
    """Precise, reproducible PII classification without AI ambiguity"""
    
    @staticmethod
    def classify_snippet(snippet: str, context: str = "", 
                        variable_names: List[str] = None) -> Dict[str, Any]:
        """
        Classify PII in code snippet with deterministic rules
        
        Args:
            snippet: Code snippet (e.g., "logger.info(f'User {user_id} logged in')")
            context: Context description (e.g., "logging in auth.py")
            variable_names: List of variable names found in snippet
        
        Returns:
            Classification dict with pii_types, severity, article, confidence
        """
        snippet_lower = snippet.lower()
        context_lower = context.lower()
        variable_names = variable_names or []
        
        detected_pii: Set[str] = set()
        max_severity = "info"
        gdpr_articles: Set[str] = set()
        reasoning_parts = []
        
        # Check standard PII patterns
        for pii_pattern in DETERMINISTIC_PII_PATTERNS:
            if DeterministicClassifier._matches_pii_pattern(
                snippet_lower, context_lower, variable_names, pii_pattern
            ):
                detected_pii.add(pii_pattern.code)
                max_severity = DeterministicClassifier._highest_severity(max_severity, pii_pattern.severity)
                if pii_pattern.gdpr_article:
                    gdpr_articles.add(pii_pattern.gdpr_article)
                reasoning_parts.append(f"Found {pii_pattern.code}")
        
        # Check Article 9 special categories (strict)
        article9_found = DeterministicClassifier._check_article9(
            snippet_lower, context_lower, variable_names
        )
        if article9_found:
            detected_pii.update(article9_found)
            gdpr_articles.add("Art. 9")
            max_severity = "critical"
            reasoning_parts.append(f"Special category: {', '.join(article9_found)}")
        
        # Default GDPR article for any PII
        if detected_pii and not gdpr_articles:
            gdpr_articles.add("Art. 6(1)")  # Lawful basis required
        
        return {
            "pii_types": sorted(list(detected_pii)),
            "sectors": [],  # Required by ClassificationResult
            "severity": max_severity,
            "article": list(gdpr_articles)[0] if gdpr_articles else None,
            "gdpr_articles": sorted(list(gdpr_articles)),
            "legal_basis_required": len(detected_pii) > 0,  # Required by ClassificationResult
            "confidence": 1.0 if detected_pii else 0.0,  # Deterministic = 100% confidence
            "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "No PII detected",
            "category": "pii" if detected_pii else "technical",
        }
    
    @staticmethod
    def _matches_pii_pattern(snippet: str, context: str, 
                            variable_names: List[str], 
                            pattern: PIIPattern) -> bool:
        """Check if snippet matches PII pattern with exclusions"""
        
        # Check excluded contexts first
        for excluded in pattern.excluded_contexts:
            if excluded in snippet or excluded in context:
                return False
        
        # Check regex patterns
        for regex_pattern in pattern.patterns:
            if re.search(regex_pattern, snippet, re.IGNORECASE):
                return True
        
        # Check variable names
        for var_name in variable_names:
            if var_name.lower() in [vn.lower() for vn in pattern.variable_names]:
                return True
        
        return False
    
    @staticmethod
    def _check_article9(snippet: str, context: str, 
                       variable_names: List[str]) -> Set[str]:
        """
        Strictly check for Article 9 special category data
        Requires BOTH pattern match AND required context
        """
        detected = set()
        
        for category_code, category_info in ARTICLE9_SPECIAL_CATEGORIES.items():
            # Must match pattern
            pattern_match = False
            for pattern in category_info['patterns']:
                if re.search(pattern, snippet, re.IGNORECASE):
                    pattern_match = True
                    break
            
            if not pattern_match:
                continue
            
            # Check excluded context
            for excluded in category_info.get('excluded_context', []):
                if excluded in snippet or excluded in context:
                    pattern_match = False
                    break
            
            if not pattern_match:
                continue
            
            # STRICT: Must have required context
            required_context = category_info.get('required_context', [])
            if required_context:
                has_context = any(
                    req_ctx in snippet or req_ctx in context
                    for req_ctx in required_context
                )
                if has_context:
                    detected.add(category_code)
            else:
                detected.add(category_code)
        
        return detected
    
    @staticmethod
    def _highest_severity(current: str, new: str) -> str:
        """Return highest severity level"""
        severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        return new if severity_order.get(new, 0) > severity_order.get(current, 0) else current

