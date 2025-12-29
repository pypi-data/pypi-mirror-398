# Privalyse Scanner - Example Applications

This directory contains reference applications for testing and demonstrating Privalyse Scanner v2.0 capabilities.

## 📁 Example Projects

### 1. bad-practice-app/ 
**Intentionally Vulnerable Application** 🔴

A comprehensive demonstration of security and privacy anti-patterns.

- **Purpose**: Testing, training, validation
- **Findings**: 22 vulnerabilities (12 critical, 10 high)
- **Types**: SQL injection, XSS, SSRF, weak crypto, hardcoded secrets, etc.
- **Score**: 5/100 (severe)

[View Details →](bad-practice-app/README.md)

### 2. best-practice-app/
**Secure & GDPR-Compliant Application** ✅

Production-ready security patterns and privacy compliance.

- **Purpose**: Reference implementation, false positive testing
- **Findings**: 0 vulnerabilities
- **Features**: Parameterized queries, secure hashing, input validation, consent tracking
- **Score**: 100/100 (compliant)

[View Details →](best-practice-app/README.md)

## 🎯 Quick Start

### Scan Bad Practice App
```bash
cd /path/to/privalyse
python3 privalyse_v2.py \
  --root privalyse-cli/examples/bad-practice-app \
  --out bad-practice-report.html \
  --format html
```

**Expected Results:**
- 🔴 22 findings
- 🔴 12 critical issues
- 🟠 10 high severity
- Compliance: 5/100

### Scan Best Practice App
```bash
python3 privalyse_v2.py \
  --root privalyse-cli/examples/best-practice-app \
  --out best-practice-report.html \
  --format html
```

**Expected Results:**
- ✅ 0 findings
- ✅ 0 false positives
- Compliance: 100/100

## 📊 Comparison

| Metric | Bad Practice | Best Practice |
|--------|-------------|---------------|
| **Compliance Score** | 5/100 | 100/100 |
| **Total Findings** | 22 | 0 |
| **Critical Issues** | 12 | 0 |
| **High Severity** | 10 | 0 |
| **Vulnerability Types** | 13 | 0 |

[View Detailed Comparison →](SCAN_COMPARISON.md)

## �� Testing Use Cases

### 1. Feature Validation
Test scanner detects all vulnerability types:
```bash
# Should find 22 vulnerabilities
python3 privalyse_v2.py --root privalyse-cli/examples/bad-practice-app
```

### 2. False Positive Testing
Verify scanner doesn't flag secure code:
```bash
# Should find 0 vulnerabilities
python3 privalyse_v2.py --root privalyse-cli/examples/best-practice-app
```

### 3. Accuracy Benchmarking
Track scanner improvements over time:
```bash
# Generate reports
python3 privalyse_v2.py --root privalyse-cli/examples/bad-practice-app --out bad-v1.json
python3 privalyse_v2.py --root privalyse-cli/examples/best-practice-app --out good-v1.json

# Compare after scanner updates
python3 privalyse_v2.py --root privalyse-cli/examples/bad-practice-app --out bad-v2.json
python3 privalyse_v2.py --root privalyse-cli/examples/best-practice-app --out good-v2.json
```

## 📚 What Each Example Demonstrates

### Bad Practice App Vulnerabilities

**Injection Attacks:**
- SQL Injection (2x) - string concatenation, % formatting
- Command Injection (1x) - subprocess shell=True
- Code Injection (2x) - eval(), exec()
- Template Injection (2x) - render_template_string()
- XSS (1x) - unescaped HTML

**Cryptography Weaknesses:**
- Weak hashing (2x) - MD5, SHA1 for passwords
- Weak cipher mode (1x) - AES ECB
- Insecure random (2x) - random.randint() for tokens
- Hardcoded secrets (3x) - API keys, passwords

**Data Security:**
- Path Traversal (2x) - no sanitization
- SSRF (2x) - user-controlled URLs
- Deserialization (2x) - pickle, YAML unsafe

### Best Practice App Features

**Security:**
- ✅ Parameterized SQL queries
- ✅ Input validation & sanitization
- ✅ Secure password hashing (pbkdf2)
- ✅ Cryptographically secure random (secrets module)
- ✅ Environment variables for secrets
- ✅ Path traversal prevention
- ✅ SSRF prevention (URL whitelisting)
- ✅ Safe serialization (JSON only)

**Privacy (GDPR):**
- ✅ Consent tracking
- ✅ Data minimization
- ✅ Purpose limitation
- ✅ Encryption at rest
- ✅ Anonymization (hashed IPs)
- ✅ Audit logging (no PII)
- ✅ Right to be forgotten support

## 🔍 Vulnerability Coverage

### Currently Detected (13 types)
1. SQL Injection ✅
2. Command Injection ✅
3. Code Injection (eval/exec) ✅
4. Path Traversal ✅
5. SSRF ✅
6. XSS ✅
7. Template Injection (SSTI) ✅
8. Insecure Deserialization (Pickle, YAML) ✅
9. Weak Hash Algorithms ✅
10. Weak Cipher Modes ✅
11. Insecure Random ✅
12. Hardcoded Secrets ✅
13. XXE (XML External Entity) ⚠️ *Partial*

### Planned Additions
- CSRF
- Open Redirect
- Authentication Bypass
- Authorization Flaws (IDOR)
- Race Conditions
- Mass Assignment

## 📖 Documentation

- [Bad Practice App](bad-practice-app/README.md) - Complete vulnerability list
- [Best Practice App](best-practice-app/README.md) - Security patterns explained
- [Scan Comparison](SCAN_COMPARISON.md) - Detailed analysis & metrics

## ⚠️ Important Notes

**DO NOT:**
- Use bad-practice-app patterns in production
- Deploy bad-practice-app anywhere
- Copy vulnerable code

**DO:**
- Use best-practice-app as reference
- Test scanner with both apps
- Learn from the comparisons
- Report false positives/negatives

## 🤝 Contributing

Found a missing vulnerability type? Spotted a false positive?

1. Add example to bad-practice-app
2. Add secure pattern to best-practice-app
3. Run scans and document results
4. Submit PR with findings

## 📜 License

MIT License - Use freely for testing and education
