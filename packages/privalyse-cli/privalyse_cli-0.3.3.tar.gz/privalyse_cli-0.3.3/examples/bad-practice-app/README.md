# Bad Practice App - Intentionally Vulnerable

⚠️ **DO NOT USE IN PRODUCTION** ⚠️

This application intentionally demonstrates **every type of security and privacy vulnerability** that Privalyse Scanner v2.0 can detect.

## Purpose

- **Testing**: Comprehensive test suite for scanner capabilities
- **Training**: Learn what NOT to do in real applications
- **Validation**: Verify scanner detects all vulnerability types

## Expected Scan Results

The scanner should detect approximately **60+ findings** including:

### Infrastructure Security (New in v2.0)

1. **Docker Security**
   - `COPY .env` (Sensitive file copy)
   - `ENV POSTGRES_PASSWORD` (Hardcoded secret)
   - `0.0.0.0:5432` (Exposed database port)
   - Weak/Default passwords in `docker-compose.yml`

2. **Frontend Privacy (React/JSX)**
   - PII in `placeholder` attributes (Email, Credit Card)
   - PII in `aria-label` (Password)
   - PII in `label` attributes (SSN, Address)
   - `type="tel"` detection

### Security Vulnerabilities (Critical/High)

1. **SQL Injection** (3 instances)
   - String concatenation in queries
   - % formatting
   - No parameterization

2. **Command Injection** (3 instances)
   - subprocess with shell=True
   - eval() with user input
   - exec() with user input

3. **Path Traversal** (2 instances)
   - No filename sanitization
   - Direct user input in paths

4. **SSRF** (2 instances)
   - requests.get() with user URLs
   - requests.post() with user URLs

5. **Insecure Deserialization** (2 instances)
   - pickle.loads() with user data
   - yaml.load() without SafeLoader

6. **Template Injection (SSTI)** (2 instances)
   - render_template_string() with user input
   - Dynamic template strings

7. **XSS** (2 instances)
   - Unescaped HTML in responses
   - Unescaped JSON data

8. **XXE** (2 instances)
   - ElementTree without entity protection
   - ET.parse without security config

9. **Code Injection** (2 instances)
   - eval() and exec()

### Crypto Weaknesses (Critical/High)

10. **Weak Hash Algorithms** (2 instances)
    - MD5 for passwords
    - SHA1 for checksums

11. **Weak Cipher Mode** (1 instance)
    - AES ECB mode

12. **Insecure Random** (2 instances)
    - random.randint() for tokens
    - random.random() for session IDs

13. **Hardcoded Secrets** (4 instances)
    - API keys
    - Database passwords
    - JWT secrets
    - Payment processor keys

### Privacy Violations (High/Medium)

14. **PII in Logs**
    - Email, SSN, credit cards logged

15. **Unencrypted PII Storage**
    - Sensitive data stored plaintext

16. **No Consent Tracking**
    - Missing GDPR consent mechanisms

17. **Excessive Data Collection**
    - Tracking without user knowledge

### Infrastructure Vulnerabilities (New in v2.0)

1. **Docker Security**
   - Sensitive files (`.env`, `id_rsa`) copied into image
   - Hardcoded secrets in `ENV` instructions
   - Weak default passwords in `docker-compose.yml`
   - Database ports (5432, 6379) exposed to public interface

## Running the Scan

```bash
# From privalyse root directory
python3 privalyse_v2.py \
  --root privalyse-cli/examples/bad-practice-app \
  --out bad-practice-report.json

# Generate HTML report
python3 privalyse_v2.py \
  --root privalyse-cli/examples/bad-practice-app \
  --out bad-practice-report.html \
  --format html
```

## Expected Compliance Score

- **Score**: 0-10/100 (severe)
- **Critical Findings**: 15+
- **High Findings**: 10+
- **Total Findings**: 30+

## Anti-Patterns Demonstrated

### Security
- No input validation
- String concatenation in queries
- Direct execution of user input
- No sanitization
- Weak cryptography
- Secrets in source code

### Privacy
- PII in logs (plaintext)
- No encryption at rest
- No consent mechanisms
- No purpose limitation
- Excessive data collection
- No data minimization

## DO NOT

- Deploy this code
- Use as reference for production
- Copy any patterns from this app

## DO

- Use for testing scanner accuracy
- Learn from the mistakes
- Compare with best-practice-app
