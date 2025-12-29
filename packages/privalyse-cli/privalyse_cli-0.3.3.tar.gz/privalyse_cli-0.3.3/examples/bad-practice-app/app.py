"""
BAD PRACTICE APP - Comprehensive Security & Privacy Anti-Patterns
==========================================

⚠️  DEMONSTRATION ONLY - DO NOT USE IN PRODUCTION! ⚠️

This application intentionally demonstrates EVERY type of vulnerability that
Privalyse Scanner v2.0 can detect. Total: 44+ violations across 3 categories.

📊 SCAN RESULTS: 44 Findings | Compliance Score: 5.0/100 (severe)

═══════════════════════════════════════════════════════════════════════════

🔴 PRIVACY VIOLATIONS (19 findings) - GDPR Non-Compliance
═══════════════════════════════════════════════════════════════════════════

✅ PII in Application Logs (17x PRINT_PII):
   - Email addresses in plaintext
   - Passwords in logs (CRITICAL)
   - SSN (Social Security Numbers)
   - Credit card numbers
   - Phone numbers
   - Birth dates
   - Physical addresses
   - User IDs and tracking data

✅ Art. 9 GDPR Special Category Data (2x PRINT_PII_ARTICLE9):
   - Biometric data (fingerprints, facial recognition)
   - Health data (diagnoses, medications, blood type)
   - Racial/ethnic origin
   - Religious beliefs

✅ Other Privacy Anti-Patterns (demonstrated but not all auto-detected):
   - PII in URL query parameters (logged in server access logs)
   - Unencrypted PII storage in database
   - No consent tracking mechanisms
   - Excessive data collection without justification
   - Missing purpose limitation
   - No data retention policies
   - No anonymization/pseudonymization
   - Cross-border data transfers without safeguards
   - Third-party data sharing without consent
   - Children's data without parental consent
   - Geolocation tracking without explicit consent
   - Cookie tracking without consent
   - No privacy policy
   - Automated profiling without transparency (Art. 22)
   - Web scraping personal data
   - No right to deletion support
   - No data portability
   - Broad employee data access without audit logs

═══════════════════════════════════════════════════════════════════════════

🔴 SECURITY VULNERABILITIES (15 findings) - Injection & Execution
═══════════════════════════════════════════════════════════════════════════

✅ Injection Attacks:
   - 4x SSRF (Server-Side Request Forgery)
   - 2x SQL Injection (multiple patterns)
   - 2x Code Injection (eval, exec)
   - 2x Path Traversal
   - 2x Template Injection (SSTI)
   - 2x XSS (Cross-Site Scripting)
   - 1x Command Injection

✅ Deserialization:
   - 1x Pickle Untrusted Data
   - 1x YAML Unsafe Load

═══════════════════════════════════════════════════════════════════════════

🔴 CRYPTOGRAPHY WEAKNESSES (5 findings) - Art. 32 GDPR
═══════════════════════════════════════════════════════════════════════════

✅ Weak Cryptography:
   - 2x Weak Hash Functions (MD5, SHA1 for passwords)
   - 2x Insecure Random (for security-critical operations)
   - 1x ECB Mode (block cipher weakness)

✅ Secrets Management:
   - 3x Hardcoded Secrets (API keys, passwords, tokens)

═══════════════════════════════════════════════════════════════════════════

📋 GDPR ARTICLES VIOLATED
═══════════════════════════════════════════════════════════════════════════

- Art. 5 (Principles): No purpose limitation, excessive collection
- Art. 6 (Lawfulness): No legal basis for processing
- Art. 9 (Special Categories): Biometric, health data without safeguards
- Art. 17 (Right to Erasure): No deletion mechanism
- Art. 22 (Automated Decision-Making): Profiling without transparency
- Art. 25 (Data Protection by Design): No privacy-by-default
- Art. 32 (Security): Weak encryption, hardcoded secrets, plaintext storage

═══════════════════════════════════════════════════════════════════════════

Usage:
    python privalyse_v2.py --root examples/bad-practice-app --out results.json
    
Expected Output:
    🔴 Compliance Score: 5.0/100 (severe)
    📊 Findings: 44 total
    🔴 Critical: 16
    🟠 High: 17

Compare with best-practice-app:
    🟢 Compliance Score: 100.0/100 (compliant)
    📊 Findings: 0 total
"""

import os
import sqlite3
import subprocess
import pickle
import hashlib
import random
import yaml
import xml.etree.ElementTree as ET
import uuid
import re
from flask import Flask, request, render_template_string, jsonify, make_response
import requests
from Crypto.Cipher import AES

app = Flask(__name__)

# ============================================================================
# CRITICAL: Hardcoded Secrets
# ============================================================================

API_KEY = "sk_live_DUMMY_51MZqKPQR7x8HpN9K3vX2yT4cW6fG8hJ"
DB_PASSWORD = "SuperSecret123!"
JWT_SECRET = "my-super-secret-jwt-key-123"
STRIPE_SECRET = "sk_test_DUMMY_4eC39HqLyjWDarjtT1zdp7dc"

# ============================================================================
# CRITICAL: Weak Cryptography
# ============================================================================

def hash_password(password):
    """VULN: Using MD5 for password hashing"""
    return hashlib.md5(password.encode()).hexdigest()

def hash_file_checksum(data):
    """VULN: Using SHA1 for checksums (legacy, but still weak)"""
    return hashlib.sha1(data.encode()).hexdigest()

def generate_token():
    """VULN: Insecure random for security tokens"""
    return random.randint(100000, 999999)

def generate_session_id():
    """VULN: Insecure random for session IDs"""
    return str(random.random() * 1000000)

def encrypt_data(data):
    """VULN: ECB cipher mode - not semantically secure"""
    key = b'sixteen_byte_key'
    cipher = AES.new(key, AES.MODE_ECB)
    # Pad data to 16 bytes
    padded = data + b' ' * (16 - len(data) % 16)
    return cipher.encrypt(padded)

# ============================================================================
# CRITICAL: SQL Injection Vulnerabilities
# ============================================================================

@app.route('/search')
def search_users():
    """VULN: SQL Injection via string concatenation"""
    username = request.args.get('username', '')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # SQL Injection: Direct string formatting
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({'results': results})

@app.route('/login')
def login():
    """VULN: SQL Injection via % formatting"""
    username = request.args.get('user', '')
    password = request.args.get('pass', '')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # SQL Injection: String interpolation
    query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password)
    cursor.execute(query)
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({'status': 'success', 'token': generate_token()})
    return jsonify({'status': 'failed'})

# ============================================================================
# CRITICAL: Command Injection
# ============================================================================

@app.route('/ping')
def ping_host():
    """VULN: Command Injection via subprocess with shell=True"""
    host = request.args.get('host', 'localhost')
    
    # Command injection: shell=True with user input
    result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True)
    
    return jsonify({'output': result.stdout.decode()})

@app.route('/execute')
def execute_command():
    """VULN: Code injection via eval()"""
    code = request.args.get('code', '1+1')
    
    # Code injection: Direct eval of user input
    result = eval(code)
    
    return jsonify({'result': result})

@app.route('/run')
def run_code():
    """VULN: Code injection via exec()"""
    script = request.args.get('script', 'print("hello")')
    
    # Code injection: Direct exec of user input
    exec(script)
    
    return jsonify({'status': 'executed'})

# ============================================================================
# CRITICAL: Path Traversal
# ============================================================================

@app.route('/download')
def download_file():
    """VULN: Path Traversal - no sanitization"""
    filename = request.args.get('file', '')
    
    # Path traversal: User-controlled path with no validation
    filepath = f"/var/www/uploads/{filename}"
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return jsonify({'content': content})
    except:
        return jsonify({'error': 'File not found'})

@app.route('/read')
def read_file():
    """VULN: Path Traversal via os.path.join"""
    filename = request.args.get('name', '')
    
    # Path traversal: os.path.join doesn't prevent ../
    filepath = os.path.join('/var/data', filename)
    
    with open(filepath, 'r') as f:
        data = f.read()
    
    return jsonify({'data': data})

# ============================================================================
# CRITICAL: Server-Side Request Forgery (SSRF)
# ============================================================================

@app.route('/fetch')
def fetch_url():
    """VULN: SSRF - user-controlled URL"""
    url = request.args.get('url', '')
    
    # SSRF: No URL validation or whitelist
    response = requests.get(url)
    
    return jsonify({'data': response.text})

@app.route('/proxy')
def proxy_request():
    """VULN: SSRF via requests.post"""
    target = request.args.get('target', '')
    
    # SSRF: User controls destination
    response = requests.post(target, json={'data': 'test'})
    
    return response.text

# ============================================================================
# CRITICAL: Insecure Deserialization
# ============================================================================

@app.route('/load-session')
def load_session():
    """VULN: Pickle deserialization of untrusted data"""
    session_data = request.args.get('data', '')
    
    # Insecure deserialization: Pickle can execute arbitrary code
    try:
        session = pickle.loads(session_data.encode('latin1'))
        return jsonify({'session': session})
    except:
        return jsonify({'error': 'Invalid session'})

@app.route('/load-config')
def load_config():
    """VULN: YAML unsafe load - allows code execution"""
    config_yaml = request.args.get('config', '')
    
    # Insecure deserialization: yaml.load without SafeLoader
    config = yaml.load(config_yaml, Loader=yaml.Loader)
    
    return jsonify({'config': config})

# ============================================================================
# CRITICAL: Template Injection (SSTI)
# ============================================================================

@app.route('/render')
def render_template():
    """VULN: Server-Side Template Injection"""
    template = request.args.get('template', 'Hello')
    
    # SSTI: Rendering user input as template
    return render_template_string(template)

@app.route('/preview')
def preview_template():
    """VULN: SSTI with user data"""
    name = request.args.get('name', 'World')
    template = f"<h1>Hello {name}</h1>"
    
    # SSTI: Dynamic template string
    return render_template_string(template)

# ============================================================================
# HIGH: Cross-Site Scripting (XSS)
# ============================================================================

@app.route('/comment')
def show_comment():
    """VULN: Reflected XSS"""
    comment = request.args.get('text', '')
    
    # XSS: Unescaped user input in response
    html = f"<div>Comment: {comment}</div>"
    return make_response(html)

@app.route('/profile')
def show_profile():
    """VULN: XSS in JSON response (if rendered in browser)"""
    username = request.args.get('user', 'Guest')
    
    # XSS: Unescaped data in response
    return jsonify({'profile': f'<script>alert("XSS")</script>{username}'})

# ============================================================================
# HIGH: XML External Entity (XXE)
# ============================================================================

@app.route('/parse-xml')
def parse_xml():
    """VULN: XXE - unsafe XML parser"""
    xml_data = request.args.get('xml', '<root></root>')
    
    # XXE: Default parser allows entity expansion
    tree = ET.fromstring(xml_data)
    
    return jsonify({'parsed': tree.tag})

@app.route('/process-xml')
def process_xml():
    """VULN: XXE via ET.parse"""
    xml_file = request.args.get('file', 'data.xml')
    
    # XXE: No entity processing disabled
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    return jsonify({'root': root.tag})

# ============================================================================
# CRITICAL: Privacy Violations - Comprehensive GDPR Non-Compliance
# ============================================================================

@app.route('/register')
def register_user():
    """
    PRIVACY VIOLATIONS (Multiple):
    1. PII in logs (plaintext)
    2. PII in URL query parameters
    3. No encryption at rest
    4. No consent tracking
    5. Weak password hashing
    6. Excessive data collection
    7. No legal basis documented
    8. No purpose limitation
    """
    # PRIVACY VULN 1: Sensitive data in URL query parameters (logged in access logs)
    email = request.args.get('email', '')
    password = request.args.get('password', '')
    ssn = request.args.get('ssn', '')
    credit_card = request.args.get('cc', '')
    phone = request.args.get('phone', '')
    address = request.args.get('address', '')
    date_of_birth = request.args.get('dob', '')
    
    # PRIVACY VULN 2: PII in application logs (plaintext)
    print(f"New user registration: {email}")
    print(f"User details - SSN: {ssn}, Phone: {phone}, DOB: {date_of_birth}")
    print(f"Credit Card: {credit_card}, Address: {address}")
    print(f"Password: {password}")  # CRITICAL: Password in logs!
    
    # PRIVACY VULN 3: Weak password hashing (MD5 - see above)
    hashed_pw = hash_password(password)
    
    # PRIVACY VULN 4: No encryption at rest for sensitive data
    # Storing SSN, credit card, etc. in plaintext
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (
            email, password_hash, ssn, credit_card, phone, 
            address, date_of_birth, ip_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email, hashed_pw, ssn, credit_card, phone,
        address, date_of_birth, request.remote_addr
    ))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN 5: No consent tracking whatsoever
    # No record of user consent for data processing
    
    # PRIVACY VULN 6: No legal basis documented
    # Not tracking GDPR Article 6 legal basis
    
    # PRIVACY VULN 7: No purpose limitation
    # Data can be used for any purpose
    
    return jsonify({'status': 'registered', 'user_email': email})

@app.route('/track')
def track_user():
    """
    PRIVACY VIOLATIONS:
    1. Excessive data collection
    2. No consent check
    3. Permanent storage without retention policy
    4. IP address stored in plaintext
    5. No anonymization/pseudonymization
    """
    user_id = request.args.get('user_id')
    
    # PRIVACY VULN 1: Collect excessive data
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    referrer = request.headers.get('Referer', '')
    accept_language = request.headers.get('Accept-Language', '')
    
    # PRIVACY VULN 2: PII in logs
    print(f"Tracking: User {user_id} from {ip_address}")
    print(f"User-Agent: {user_agent}, Referrer: {referrer}")
    
    # PRIVACY VULN 3: No consent check - track everyone
    
    # PRIVACY VULN 4: Store data permanently without retention policy
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tracking (
            user_id, ip, user_agent, referrer, 
            language, timestamp
        ) VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (user_id, ip_address, user_agent, referrer, accept_language))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'tracked'})

@app.route('/profile/<user_id>')
def get_profile(user_id):
    """
    PRIVACY VIOLATIONS:
    1. No access control (anyone can view any profile)
    2. Returns all PII without masking
    3. No audit log
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # PRIVACY VULN: Return ALL user data including sensitive fields
    cursor.execute("""
        SELECT email, ssn, credit_card, phone, address, date_of_birth
        FROM users WHERE id = ?
    """, (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # PRIVACY VULN: Expose all sensitive data in response
        return jsonify({
            'email': user[0],
            'ssn': user[1],           # Should be masked!
            'credit_card': user[2],   # Should be masked!
            'phone': user[3],
            'address': user[4],
            'dob': user[5]
        })
    
    return jsonify({'error': 'User not found'}), 404

@app.route('/export-data')
def export_user_data():
    """
    PRIVACY VIOLATIONS:
    1. No authentication
    2. Exports ALL users' data (not just requester)
    3. No data minimization
    4. Includes deleted/inactive users
    """
    # PRIVACY VULN: Export ALL user data without permission
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, ssn, credit_card, phone, address, date_of_birth
        FROM users
    """)
    
    users = cursor.fetchall()
    conn.close()
    
    # PRIVACY VULN: Log export with PII
    print(f"Data export requested, exporting {len(users)} users")
    
    return jsonify({'users': [
        {
            'id': u[0], 'email': u[1], 'ssn': u[2],
            'cc': u[3], 'phone': u[4], 'address': u[5], 'dob': u[6]
        } for u in users
    ]})

@app.route('/search-users')
def search_all_users():
    """
    PRIVACY VIOLATIONS:
    1. Search across all PII fields
    2. No access control
    3. Allows pattern matching on SSN
    """
    search_term = request.args.get('q', '')
    
    # PRIVACY VULN: Allow searching by SSN, credit card, etc.
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # PRIVACY VULN: Log search with search term (might contain PII)
    print(f"User search: {search_term}")
    
    # PRIVACY VULN: Search in sensitive fields
    cursor.execute("""
        SELECT email, ssn, phone FROM users
        WHERE email LIKE ? OR ssn LIKE ? OR phone LIKE ?
    """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({'results': results})

@app.route('/analytics')
def get_analytics():
    """
    PRIVACY VIOLATIONS:
    1. Exposes individual user behavior
    2. No anonymization
    3. Links IP to user_id
    """
    # PRIVACY VULN: Return detailed user tracking with identifiers
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, ip, user_agent, referrer, timestamp
        FROM tracking
        ORDER BY timestamp DESC
        LIMIT 100
    """)
    
    tracking_data = cursor.fetchall()
    conn.close()
    
    return jsonify({'analytics': [
        {
            'user_id': t[0],
            'ip': t[1],
            'user_agent': t[2],
            'referrer': t[3],
            'timestamp': t[4]
        } for t in tracking_data
    ]})

@app.route('/share-data')
def share_with_third_party():
    """
    PRIVACY VIOLATIONS:
    1. Cross-border data transfer without safeguards
    2. No user consent for sharing
    3. Sharing with unknown third parties
    4. No data processing agreement
    """
    partner_url = request.args.get('partner', 'https://unknown-partner.com/api')
    
    # PRIVACY VULN: Export user data to third party
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, phone, address FROM users")
    users = cursor.fetchall()
    conn.close()
    
    # PRIVACY VULN: Send to external service without consent
    user_data = [{'email': u[0], 'phone': u[1], 'address': u[2]} for u in users]
    
    # PRIVACY VULN: Log the data transfer with PII
    print(f"Sharing {len(users)} user records with {partner_url}")
    
    # PRIVACY VULN: No encryption in transit check
    response = requests.post(partner_url, json={'users': user_data})
    
    return jsonify({'status': 'shared', 'records': len(users)})

@app.route('/marketing')
def send_marketing():
    """
    PRIVACY VIOLATIONS:
    1. Send marketing without consent
    2. No opt-out mechanism
    3. Access all user emails
    """
    # PRIVACY VULN: Get ALL users for marketing (no consent check)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, phone FROM users")
    users = cursor.fetchall()
    conn.close()
    
    # PRIVACY VULN: Log marketing campaign with PII
    print(f"Sending marketing to {len(users)} users")
    for email, phone in users:
        print(f"Marketing sent to: {email}, {phone}")
    
    return jsonify({'status': 'sent', 'count': len(users)})

@app.route('/delete-user/<user_id>')
def delete_user(user_id):
    """
    PRIVACY VIOLATIONS:
    1. No actual deletion (GDPR right to be forgotten)
    2. Data remains in backups
    3. No cascade delete in analytics
    4. No confirmation to user
    """
    # PRIVACY VULN: Mark as deleted but don't actually remove data
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # PRIVACY VULN: Soft delete only - data still accessible
    cursor.execute("UPDATE users SET deleted = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN: Don't delete from analytics/tracking tables
    
    # PRIVACY VULN: Log deletion with user_id
    print(f"User deletion requested: {user_id}")
    
    return jsonify({'status': 'deleted'})

@app.route('/employee-access')
def employee_data_access():
    """
    PRIVACY VIOLATIONS:
    1. No audit log for data access
    2. Broad employee access to all data
    3. No purpose limitation
    """
    employee_id = request.args.get('employee_id')
    
    # PRIVACY VULN: Allow any employee to access all user data
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, ssn, credit_card, phone, address
        FROM users
    """)
    
    all_users = cursor.fetchall()
    conn.close()
    
    # PRIVACY VULN: Minimal logging (no purpose tracked)
    print(f"Employee {employee_id} accessed user database")
    
    return jsonify({'count': len(all_users)})

@app.route('/backup')
def create_backup():
    """
    PRIVACY VIOLATIONS:
    1. Unencrypted backups
    2. Backups stored indefinitely
    3. No access control on backups
    """
    import shutil
    
    # PRIVACY VULN: Create unencrypted database backup
    shutil.copy('users.db', '/tmp/users_backup.db')
    shutil.copy('analytics.db', '/tmp/analytics_backup.db')
    
    # PRIVACY VULN: Log backup location
    print("Created unencrypted backups at /tmp/")
    
    return jsonify({'status': 'backup_created', 'location': '/tmp/'})

# ============================================================================
# Additional Anti-Patterns
# ============================================================================

@app.route('/debug')
def debug_info():
    """VULN: Information disclosure in debug mode"""
    # Exposing internal state
    return jsonify({
        'api_key': API_KEY,
        'db_password': DB_PASSWORD,
        'jwt_secret': JWT_SECRET,
        'env': dict(os.environ)
    })

@app.route('/cookie-tracking')
def set_tracking_cookies():
    """
    PRIVACY VIOLATIONS:
    1. Third-party tracking cookies without consent
    2. No cookie policy
    3. No opt-out mechanism
    4. Persistent tracking identifiers
    """
    user_id = request.args.get('user_id', 'unknown')
    
    # PRIVACY VULN: Set tracking cookies without consent
    response = make_response(jsonify({'status': 'tracked'}))
    
    # PRIVACY VULN: Long-lived tracking cookie (1 year)
    response.set_cookie('user_tracking_id', user_id, max_age=365*24*60*60)
    response.set_cookie('session_tracker', str(uuid.uuid4()), max_age=365*24*60*60)
    response.set_cookie('analytics_id', request.remote_addr, max_age=365*24*60*60)
    
    # PRIVACY VULN: Third-party analytics (Google, Facebook, etc.)
    # In real app: Google Analytics, Facebook Pixel without consent
    
    # PRIVACY VULN: Log cookie setting with user data
    print(f"Set tracking cookies for user: {user_id}")
    
    return response

@app.route('/geo-location')
def track_location():
    """
    PRIVACY VIOLATIONS:
    1. Geolocation tracking without explicit consent
    2. Precise location storage
    3. No purpose limitation
    """
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    user_id = request.args.get('user_id')
    
    # PRIVACY VULN: Store precise geolocation
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO locations (user_id, latitude, longitude, timestamp)
        VALUES (?, ?, ?, datetime('now'))
    """, (user_id, latitude, longitude))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN: Log precise location data
    print(f"Location tracked: User {user_id} at ({latitude}, {longitude})")
    
    return jsonify({'status': 'location_tracked'})

@app.route('/biometric')
def store_biometric():
    """
    PRIVACY VIOLATIONS:
    1. Biometric data storage (Art. 9 GDPR special category)
    2. No explicit consent
    3. No encryption
    4. No legal basis
    """
    user_id = request.args.get('user_id')
    fingerprint_hash = request.args.get('fingerprint')
    face_encoding = request.args.get('face_data')
    
    # PRIVACY VULN: Store biometric data (Art. 9 GDPR violation)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO biometric_data (user_id, fingerprint, face_encoding)
        VALUES (?, ?, ?)
    """, (user_id, fingerprint_hash, face_encoding))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN: Log biometric data collection
    print(f"Stored biometric data for user: {user_id}")
    
    return jsonify({'status': 'biometric_stored'})

@app.route('/health-data')
def store_health_info():
    """
    PRIVACY VIOLATIONS:
    1. Health data storage (Art. 9 GDPR special category)
    2. No medical provider safeguards
    3. No HIPAA compliance
    4. No explicit consent
    """
    user_id = request.args.get('user_id')
    diagnosis = request.args.get('diagnosis')
    medication = request.args.get('medication')
    blood_type = request.args.get('blood_type')
    
    # PRIVACY VULN: Store health data without proper safeguards
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_records (user_id, diagnosis, medication, blood_type)
        VALUES (?, ?, ?, ?)
    """, (user_id, diagnosis, medication, blood_type))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN: Log sensitive health information
    print(f"Health data: User {user_id}, Diagnosis: {diagnosis}, Meds: {medication}")
    
    return jsonify({'status': 'health_data_stored'})

@app.route('/racial-data')
def collect_racial_info():
    """
    PRIVACY VIOLATIONS:
    1. Racial/ethnic data collection (Art. 9 GDPR special category)
    2. No legitimate purpose
    3. Discriminatory risk
    """
    user_id = request.args.get('user_id')
    ethnicity = request.args.get('ethnicity')
    race = request.args.get('race')
    religion = request.args.get('religion')
    
    # PRIVACY VULN: Collect special category data
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO demographic_data (user_id, ethnicity, race, religion)
        VALUES (?, ?, ?, ?)
    """, (user_id, ethnicity, race, religion))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN: Log special category data
    print(f"Demographic: User {user_id}, Ethnicity: {ethnicity}, Religion: {religion}")
    
    return jsonify({'status': 'demographic_stored'})

@app.route('/children-data')
def collect_children_info():
    """
    PRIVACY VIOLATIONS:
    1. Children's data without parental consent
    2. No age verification
    3. No COPPA compliance (if US)
    """
    child_name = request.args.get('name')
    child_age = request.args.get('age')
    parent_email = request.args.get('parent_email')
    school = request.args.get('school')
    
    # PRIVACY VULN: Collect children's data without verification
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO children (name, age, parent_email, school)
        VALUES (?, ?, ?, ?)
    """, (child_name, child_age, parent_email, school))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN: Log children's information
    print(f"Child registered: {child_name}, Age: {child_age}, School: {school}")
    
    return jsonify({'status': 'child_registered'})

@app.route('/scrape-social')
def scrape_social_media():
    """
    PRIVACY VIOLATIONS:
    1. Web scraping personal data without consent
    2. Automated profile harvesting
    3. No purpose limitation
    """
    profile_url = request.args.get('url')
    
    # PRIVACY VULN: Scrape personal data from social media
    response = requests.get(profile_url)
    
    # Simulate extracting PII
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\d{3}-\d{3}-\d{4}'
    
    emails = re.findall(email_pattern, response.text)
    phones = re.findall(phone_pattern, response.text)
    
    # PRIVACY VULN: Store scraped data
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    for email in emails:
        cursor.execute("INSERT INTO scraped_contacts (email, source) VALUES (?, ?)", 
                      (email, profile_url))
    conn.commit()
    conn.close()
    
    # PRIVACY VULN: Log scraped PII
    print(f"Scraped {len(emails)} emails and {len(phones)} phone numbers from {profile_url}")
    
    return jsonify({'emails': emails, 'phones': phones})

@app.route('/profiling')
def create_user_profile():
    """
    PRIVACY VIOLATIONS:
    1. Automated decision-making without consent (Art. 22 GDPR)
    2. Profiling without legal basis
    3. No transparency about profiling
    """
    user_id = request.args.get('user_id')
    
    # PRIVACY VULN: Create detailed user profile
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # PRIVACY VULN: Aggregate all user data for profiling
    cursor.execute("""
        SELECT u.email, u.age, u.income, t.ip, t.user_agent, l.latitude, l.longitude
        FROM users u
        LEFT JOIN tracking t ON u.id = t.user_id
        LEFT JOIN locations l ON u.id = l.user_id
        WHERE u.id = ?
    """, (user_id,))
    
    data = cursor.fetchall()
    conn.close()
    
    # PRIVACY VULN: Automated credit scoring/risk assessment
    risk_score = hash(str(data)) % 100  # Simplified
    
    # PRIVACY VULN: Log profiling activity
    print(f"Created profile for user {user_id}, risk score: {risk_score}")
    
    return jsonify({'user_id': user_id, 'risk_score': risk_score, 'profile': data})

@app.route('/no-privacy-policy')
def missing_privacy_policy():
    """
    PRIVACY VIOLATIONS:
    1. No privacy policy
    2. No data processing transparency
    3. No contact information for data controller
    """
    return jsonify({'error': 'Privacy policy not implemented'})

# SSL/TLS Weakness (would be in deployment config, but shown here)
# ssl_context = ssl.create_default_context()
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_NONE

if __name__ == '__main__':
    # Running in debug mode (info disclosure)
    app.run(debug=True, host='0.0.0.0', port=5000)
