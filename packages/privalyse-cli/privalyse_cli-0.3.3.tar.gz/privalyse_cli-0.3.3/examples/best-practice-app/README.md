# Best Practice App - Secure & Privacy-Compliant

✅ **This demonstrates GOOD practices** ✅

This application shows how to build secure, privacy-compliant software following OWASP and GDPR guidelines.

## Purpose

- **Reference**: Production-ready security patterns
- **Training**: Learn secure coding practices
- **False Positive Testing**: Verify scanner doesn't flag secure code

## Expected Scan Results

The scanner should find **minimal to zero actual vulnerabilities**, but may trigger some **false positives** for testing:

### Expected False Positives (for testing/tuning)

These patterns are **SECURE** but might trigger scanner detection:

1. **Password Hashing Context**
   - ✅ SECURE: Uses `werkzeug` with pbkdf2 (not MD5/SHA1)
   - ⚠️ May trigger: Contains word "password" and uses hashlib
   - **Expected**: Scanner should differentiate secure from insecure hashing

2. **File Checksum**
   - ✅ SECURE: SHA-256 for file integrity (not passwords)
   - ⚠️ May trigger: Uses hashlib module
   - **Expected**: Scanner should understand context (files vs passwords)

3. **Token Generation**
   - ✅ SECURE: Uses `secrets` module (cryptographically secure)
   - ⚠️ May trigger: Contains words "token", "session", "code"
   - **Expected**: Scanner should recognize `secrets` module as safe

4. **File Operations**
   - ✅ SECURE: Path traversal **prevention** via sanitization
   - ⚠️ May trigger: Works with filenames and paths
   - **Expected**: Scanner should detect prevention, not vulnerability

5. **URL Validation**
   - ✅ SECURE: Whitelist-based URL validation (SSRF prevention)
   - ⚠️ May trigger: Contains URL handling
   - **Expected**: Scanner should recognize validation

6. **SQL Queries**
   - ✅ SECURE: Parameterized queries with `?`
   - ⚠️ May trigger: Contains SQL execute calls
   - **Expected**: Scanner should differentiate parameterized from concatenated

7. **External Requests**
   - ✅ SECURE: Validated URLs with whitelist
   - ⚠️ May trigger: Uses requests.get()
   - **Expected**: Scanner should see validation logic

### Real Findings (Should be Zero)

The scanner should **NOT** find:
- ❌ SQL Injection - uses parameterized queries
- ❌ Command Injection - no subprocess/eval/exec with user input
- ❌ Path Traversal - sanitizes all filenames
- ❌ SSRF - validates and whitelists URLs
- ❌ XSS - uses proper escaping
- ❌ Weak Crypto - uses modern algorithms
- ❌ Hardcoded Secrets - uses environment variables
- ❌ PII in Logs - no sensitive data logged

## Security Best Practices Demonstrated

### Input Validation
```python
def validate_email(email: str) -> bool:
    """Regex-based email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

### Parameterized Queries
```python
cursor.execute(
    "SELECT id, username FROM users WHERE username = ?",
    (username,)  # Safe parameter
)
```

### Secure Password Hashing
```python
from werkzeug.security import generate_password_hash
hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
```

### Cryptographically Secure Random
```python
import secrets
token = secrets.token_urlsafe(32)  # Not random.randint()!
```

### Path Traversal Prevention
```python
def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)  # Remove path
    filename = re.sub(r'[^\w\.-]', '', filename)  # Remove dangerous chars
    return filename
```

### SSRF Prevention
```python
def validate_url(url: str) -> bool:
    allowed_domains = ['api.example.com']
    parsed = urlparse(url)
    return parsed.hostname in allowed_domains and parsed.scheme == 'https'
```

## Privacy Best Practices (GDPR)

### Consent Tracking
```python
consent_marketing = data.get('consent_marketing', False)
consent_analytics = data.get('consent_analytics', False)
```

### Data Minimization
- Only collect necessary fields
- Hash IP addresses instead of storing plaintext
- No excessive tracking

### Encryption at Rest
- Password hashing (pbkdf2)
- IP address hashing
- Sensitive data protection

### Purpose Limitation
- Check consent before analytics
- Separate marketing/analytics consent
- Audit logging

### Right to be Forgotten
- Soft delete with `deleted_at` field
- Anonymization support

## Running the Scan

```bash
# From privalyse root directory
python3 privalyse_v2.py \
  --root privalyse-cli/examples/best-practice-app \
  --out best-practice-report.json

# Generate HTML report
python3 privalyse_v2.py \
  --root privalyse-cli/examples/best-practice-app \
  --out best-practice-report.html \
  --format html
```

## Expected Compliance Score

- **Score**: 90-100/100 (compliant)
- **Critical Findings**: 0
- **High Findings**: 0
- **False Positives**: 0-7 (for tuning)

## False Positive Analysis

If the scanner reports findings, analyze:

1. **Is it a real vulnerability?** (should be NO)
2. **What triggered the detection?**
3. **How can we improve the scanner to avoid this?**

### Common False Positive Patterns

- Using hashlib for non-password purposes (checksums)
- Using `secrets` module (secure!) but detected due to keywords
- Parameterized queries flagged as SQL queries
- Validation logic flagged as vulnerability
- Safe template rendering (render_template vs render_template_string)

## Configuration

All secrets via environment variables:

```bash
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://..."
export API_KEY="your-api-key"
```

## Dependencies

```bash
pip install flask werkzeug
```

## License

MIT - Use freely as reference for production code
