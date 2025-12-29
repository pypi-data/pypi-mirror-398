# 🔒 Privalyse Security Scan Report

**Generated:** 2025-12-16T16:07:29.957963  
**Folder:** `./examples/bad-practice-app`  
**Scanner Version:** v0.1

## 📊 Executive Summary

🚨 **ACTION REQUIRED**

| Metric | Value |
|--------|-------|
| **Total Findings** | 71 |
| **Critical** | 🔴 20 |
| **High** | 🟠 30 |
| **Medium** | 🟡 10 |
| **Low** | 🔵 0 |
| **Info** | ⚪ 11 |

## 🚨 CRITICAL ISSUES - FIX IMMEDIATELY

Found **20** critical privacy/security issues that need immediate attention:

### 1. HARDCODED_SECRET

**📍 Location:** `./examples/bad-practice-app/app.py:133`

**⚠️ Issue:** Credentials

**🔍 PII Detected:** api_key, credentials

**💻 Code:**
```python
API_KEY = "***"
```

**💡 Why This Matters:**
Hardcoded secrets are a critical security vulnerability:
- **Immediate Access** - Anyone with code access has credentials
- **Version Control Exposure** - Secrets persist in Git history
- **Lateral Movement** - Compromised keys enable broader attacks
- **Compliance Violation** - Fails security audits

**✅ How to Fix:**
- **Move secrets to environment variables**
  - Use `.env` file (add to .gitignore)
  - Use secret management service (AWS Secrets Manager, etc.)
  - Never commit secrets to version control

Example:
```python
# ❌ Before
API_KEY = "sk-proj-abc123..."

# ✅ After
API_KEY = os.getenv("API_KEY")
```

---

### 2. HARDCODED_SECRET

**📍 Location:** `./examples/bad-practice-app/app.py:136`

**⚠️ Issue:** Credentials

**🔍 PII Detected:** token, credentials

**💻 Code:**
```python
STRIPE_SECRET = "***"
```

**💡 Why This Matters:**
Hardcoded secrets are a critical security vulnerability:
- **Immediate Access** - Anyone with code access has credentials
- **Version Control Exposure** - Secrets persist in Git history
- **Lateral Movement** - Compromised keys enable broader attacks
- **Compliance Violation** - Fails security audits

**✅ How to Fix:**
- **Move secrets to environment variables**
  - Use `.env` file (add to .gitignore)
  - Use secret management service (AWS Secrets Manager, etc.)
  - Never commit secrets to version control

Example:
```python
# ❌ Before
API_KEY = "sk-proj-abc123..."

# ✅ After
API_KEY = os.getenv("API_KEY")
```

---

### 3. PRINT_PII

**📍 Location:** `./examples/bad-practice-app/app.py:418`

**⚠️ Issue:** Pii

**🔍 PII Detected:** phone, ssn, birth_date

**💻 Code:**
```python
print(f"User details - SSN: {ssn}, Phone: {phone}, DOB: {date_of_birth}")
```

**💡 Why This Matters:**
This critical severity finding indicates a privacy/security concern that should be addressed to maintain GDPR compliance and protect user data.

**✅ How to Fix:**
- Review this finding and implement appropriate security controls
- Ensure PII is properly encrypted, hashed, or removed
- Follow GDPR best practices for data handling

---

### 4. PRINT_PII

**📍 Location:** `./examples/bad-practice-app/app.py:419`

**⚠️ Issue:** Pii

**🔍 PII Detected:** location, address, credit_card, financial

**💻 Code:**
```python
print(f"Credit Card: {credit_card}, Address: {address}")
```

**💡 Why This Matters:**
This critical severity finding indicates a privacy/security concern that should be addressed to maintain GDPR compliance and protect user data.

**✅ How to Fix:**
- Review this finding and implement appropriate security controls
- Ensure PII is properly encrypted, hashed, or removed
- Follow GDPR best practices for data handling

---

### 5. PRINT_PII_ARTICLE9

**📍 Location:** `./examples/bad-practice-app/app.py:855`

**⚠️ Issue:** Pii

**🔍 PII Detected:** user_id, health, id, health_data

**💻 Code:**
```python
print(f"Health data: User {user_id}, Diagnosis: {diagnosis}, Meds: {medication}")
```

**💡 Why This Matters:**
This critical severity finding indicates a privacy/security concern that should be addressed to maintain GDPR compliance and protect user data.

**✅ How to Fix:**
- Review this finding and implement appropriate security controls
- Ensure PII is properly encrypted, hashed, or removed
- Follow GDPR best practices for data handling

---


*... and 15 more critical issues. See full findings below.*


## 📋 All Findings by Severity

### 🟠 High Severity (30 findings)

| Rule | Location | PII Types |
|------|----------|-----------|
| HARDCODED_SECRET | `./examples/bad-practice-app/app.py:134` | password, credentials |
| HARDCODED_SECRET | `./examples/bad-practice-app/app.py:135` | jwt, credentials |
| PRINT_PII | `./examples/bad-practice-app/app.py:417` | email |
| PRINT_PII | `./examples/bad-practice-app/app.py:420` | password, unknown |
| PRINT_PII | `./examples/bad-practice-app/app.py:659` | email, phone |
| PRINT_PII | `./examples/bad-practice-app/app.py:945` | email, phone, unknown |
| SQL_INJECTION | `./examples/bad-practice-app/app.py:180` | database |
| SQL_INJECTION | `./examples/bad-practice-app/app.py:198` | database |
| PATH_TRAVERSAL | `./examples/bad-practice-app/app.py:254` | - |
| PATH_TRAVERSAL | `./examples/bad-practice-app/app.py:266` | - |

*... and 20 more high findings*

### 🟡 Medium Severity (10 findings)

| Rule | Location | PII Types |
|------|----------|-----------|
| COOKIE_NO_HTTPONLY | `./examples/bad-practice-app/app.py:763` | session_token |
| COOKIE_NO_HTTPONLY | `./examples/bad-practice-app/app.py:764` | session_token |
| COOKIE_TRACKING_CONSENT | `./examples/bad-practice-app/app.py:764` | tracking_data |
| COOKIE_NO_HTTPONLY | `./examples/bad-practice-app/app.py:765` | session_token |
| COOKIE_TRACKING_CONSENT | `./examples/bad-practice-app/app.py:765` | tracking_data |
| FORM_FIELD_EMAIL | `./examples/bad-practice-app/frontend/RegisterForm.jsx:14` | email |
| FORM_FIELD_LOCATION | `./examples/bad-practice-app/frontend/RegisterForm.jsx:14` | location |
| FORM_FIELD_PHONE | `./examples/bad-practice-app/frontend/RegisterForm.jsx:52` | phone |
| FORM_FIELD_BIRTH_DATE | `./examples/bad-practice-app/frontend/RegisterForm.jsx:61` | birth_date |
| FORM_FIELD_LOCATION | `./examples/bad-practice-app/frontend/RegisterForm.jsx:67` | location |
### ⚪ Info Severity (11 findings)

| Rule | Location | PII Types |
|------|----------|-----------|
| PRINT_PII | `./examples/bad-practice-app/app.py:471` | user_id, id |
| PRINT_PII | `./examples/bad-practice-app/app.py:472` | birth_date |
| PRINT_PII | `./examples/bad-practice-app/app.py:568` | unknown |
| PRINT_PII | `./examples/bad-practice-app/app.py:634` | unknown |
| PRINT_PII | `./examples/bad-practice-app/app.py:684` | user_id, id |
| PRINT_PII | `./examples/bad-practice-app/app.py:710` | id |
| PRINT_PII | `./examples/bad-practice-app/app.py:771` | user_id, id |
| PRINT_PII | `./examples/bad-practice-app/app.py:798` | location, user_id, unknown, id |
| PRINT_PII | `./examples/bad-practice-app/app.py:826` | user_id, id |
| PRINT_PII | `./examples/bad-practice-app/app.py:911` | unknown, birth_date, name |

*... and 1 more info findings*


## 🔗 Data Flow Analysis

Critical data paths detected in your application:


## ⚖️ GDPR Compliance

| Article | Violations | Description |
|---------|------------|-------------|
| **Art. 6** | 21 | Lawfulness of processing |
| **Art. 9** | 2 | Special categories of data |
| **Art. 32** | 43 | Security of processing |


**⚠️ Compliance Risk:** Your application has GDPR compliance issues that should be addressed.

## 📈 Scan Statistics

- **Files Scanned:** 0
- **Findings:** 71
- **Unique PII Types:** 25
- **Scan Duration:** 0.00s
- **Analysis Rate:** 0 lines/sec

---

## 💡 Next Steps

1. **Fix Critical Issues** - Address all critical findings immediately
2. **Review High/Medium** - Plan fixes for high and medium severity items
3. **Update Documentation** - Document security decisions
4. **Re-scan** - Run Privalyse again after fixes to verify

## 🔗 Resources

- [Privalyse Documentation](https://docs.privalyse.com)
- [GDPR Compliance Guide](https://gdpr.eu/)
- [OWASP Security Guidelines](https://owasp.org/)

---

**Generated by [Privalyse](https://privalyse.com)** - Privacy scanner for modern code  
*Report any issues or false positives: [GitHub Issues](https://github.com/privalyse/privalyse/issues)*
