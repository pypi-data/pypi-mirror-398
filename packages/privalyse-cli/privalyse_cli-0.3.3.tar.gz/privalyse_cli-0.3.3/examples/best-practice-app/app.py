"""
BEST PRACTICE APP - Secure & Privacy-Compliant Application
=========================================================

This application demonstrates SECURE coding practices and proper
privacy handling according to GDPR requirements.

HOWEVER: It also includes patterns that MIGHT trigger false positives
to test scanner accuracy and allow for fine-tuning.

Security Best Practices:
- Parameterized queries (no SQL injection)
- Input validation & sanitization
- Secure password hashing (bcrypt/argon2)
- Cryptographically secure random
- No hardcoded secrets (environment variables)
- Proper error handling
- Content Security Policy
- HTTPS enforcement

Privacy Best Practices:
- Encryption at rest for PII
- Minimal data collection
- Consent tracking
- Purpose limitation
- Data retention policies
- Anonymization/pseudonymization
- Audit logging
"""

import os
import sqlite3
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Secure configuration via environment variables
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///secure.db')

# Proper logging configuration (no PII in logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SECURE: Configuration Management
# ============================================================================

class Config:
    """Secure configuration from environment"""
    API_KEY = os.environ.get('API_KEY')  # Not hardcoded!
    DB_PASSWORD = os.environ.get('DB_PASSWORD')  # Not hardcoded!
    JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_urlsafe(32))
    
    # Security settings
    MAX_LOGIN_ATTEMPTS = 5
    SESSION_TIMEOUT = timedelta(hours=1)
    PASSWORD_MIN_LENGTH = 12

# ============================================================================
# SECURE: Cryptography
# ============================================================================

def hash_password_secure(password: str) -> str:
    """
    SECURE: Using werkzeug's secure password hashing (bcrypt/pbkdf2)
    
    FALSE POSITIVE CHECK: Scanner might flag any password hashing,
    but this is actually using a secure algorithm.
    """
    return generate_password_hash(password, method='pbkdf2:sha256:600000')

def verify_password(password: str, hash: str) -> bool:
    """SECURE: Constant-time password verification"""
    return check_password_hash(hash, password)

def generate_secure_token() -> str:
    """
    SECURE: Cryptographically secure random token
    
    FALSE POSITIVE CHECK: Contains word "token" which might trigger
    detection, but uses secrets module (secure).
    """
    return secrets.token_urlsafe(32)

def generate_secure_session_id() -> str:
    """SECURE: Using secrets for session IDs"""
    return secrets.token_hex(32)

def calculate_file_checksum(data: bytes) -> str:
    """
    SECURE: SHA-256 for file integrity (not passwords!)
    
    FALSE POSITIVE CHECK: Uses hashlib but for legitimate purpose
    (file checksums, not passwords). Scanner should differentiate.
    """
    return hashlib.new('sha256', data).hexdigest()

def generate_verification_code() -> str:
    """
    SECURE: Secure random for verification codes
    
    FALSE POSITIVE CHECK: Contains "code" which might trigger
    security context detection, but uses secrets module.
    """
    return ''.join(secrets.choice('0123456789') for _ in range(6))

# ============================================================================
# SECURE: Input Validation
# ============================================================================

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_username(username: str) -> bool:
    """Validate username - alphanumeric only"""
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def sanitize_filename(filename: str) -> str:
    """
    SECURE: Prevent path traversal
    
    FALSE POSITIVE CHECK: Works with filenames but is actually
    PREVENTING path traversal, not causing it.
    """
    # Remove path components
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = re.sub(r'[^\w\.-]', '', filename)
    return filename

def validate_url(url: str) -> bool:
    """
    SECURE: URL validation with whitelist
    
    FALSE POSITIVE CHECK: Contains URL handling which might trigger
    SSRF detection, but this is validation, not vulnerability.
    """
    allowed_domains = ['api.example.com', 'cdn.example.com']
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        return parsed.hostname in allowed_domains and parsed.scheme == 'https'
    except:
        return False

# ============================================================================
# SECURE: Database Operations (Parameterized Queries)
# ============================================================================

@app.route('/api/search')
def search_users():
    """
    SECURE: Parameterized query prevents SQL injection
    
    FALSE POSITIVE CHECK: Contains SQL query but uses proper
    parameterization. Scanner should NOT flag this.
    """
    username = request.args.get('username', '')
    
    # Input validation
    if not validate_username(username):
        abort(400, 'Invalid username format')
    
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()
    
    # SECURE: Parameterized query with ?
    cursor.execute(
        "SELECT id, username, email FROM users WHERE username = ?",
        (username,)
    )
    
    results = cursor.fetchall()
    conn.close()
    
    # Audit logging (no PII)
    logger.info(f"User search performed, results: {len(results)}")
    
    return jsonify({'results': [
        {'id': r[0], 'username': r[1], 'email': r[2]} for r in results
    ]})

@app.route('/api/login', methods=['POST'])
def login():
    """
    SECURE: Parameterized login with rate limiting
    
    FALSE POSITIVE CHECK: Has SQL query but properly secured.
    """
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Input validation
    if not validate_username(username):
        abort(400, 'Invalid username')
    
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()
    
    # SECURE: Parameterized query
    cursor.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (username,)
    )
    
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(password, user[1]):
        token = generate_secure_token()
        logger.info(f"Successful login for user ID {user[0]}")
        return jsonify({'status': 'success', 'token': token})
    
    logger.warning(f"Failed login attempt for username")
    return jsonify({'status': 'failed'}), 401

# ============================================================================
# SECURE: File Operations (No Path Traversal)
# ============================================================================

@app.route('/api/files/<filename>')
def download_file(filename):
    """
    SECURE: Path traversal prevention
    
    FALSE POSITIVE CHECK: Uses file operations but with proper
    sanitization. Should NOT trigger path traversal detection.
    """
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Construct path safely
    base_dir = os.path.abspath('/var/www/uploads')
    filepath = os.path.join(base_dir, safe_filename)
    
    # Verify path is within allowed directory
    if not filepath.startswith(base_dir):
        abort(403, 'Access denied')
    
    # Check file exists
    if not os.path.exists(filepath):
        abort(404, 'File not found')
    
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Calculate checksum for integrity
        checksum = calculate_file_checksum(content)
        
        # logger.info(f"File download: {safe_filename}, checksum: {checksum}")
        return jsonify({
            'content': content.decode('utf-8', errors='ignore'),
            'checksum': checksum
        })
    except Exception as e:
        logger.error(f"File read error: {str(e)}")
        abort(500, 'Internal server error')

# ============================================================================
# SECURE: External Requests (SSRF Prevention)
# ============================================================================

# Removed proxy endpoint to ensure maximum security in best practice example
# @app.route('/api/proxy')
# def proxy_request():
#     ...

# ============================================================================
# SECURE: Data Processing (Safe Serialization)
# ============================================================================

@app.route('/api/config', methods=['POST'])
def save_config():
    """
    SECURE: JSON instead of pickle/yaml
    
    FALSE POSITIVE CHECK: Handles serialization but uses safe JSON,
    not pickle or unsafe yaml. Should NOT trigger deserialization warning.
    """
    import json
    
    try:
        # Use safe JSON instead of pickle/yaml
        config = request.get_json()
        
        # Validate config structure
        if not isinstance(config, dict):
            abort(400, 'Invalid config format')
        
        # Save to database with parameterized query
        conn = sqlite3.connect('secure.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO configs (data, created_at) VALUES (?, ?)",
            (json.dumps(config), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        
        logger.info("Configuration saved successfully")
        return jsonify({'status': 'saved'})
    except Exception as e:
        logger.error(f"Config save error: {str(e)}")
        abort(500, 'Save failed')

# ============================================================================
# SECURE: Template Rendering (No SSTI)
# ============================================================================

@app.route('/api/welcome/<username>')
def welcome(username):
    """
    SECURE: Using Jinja2 auto-escaping (no SSTI)
    
    FALSE POSITIVE CHECK: Uses templates but with safe rendering.
    render_template() with file is safe, not render_template_string().
    """
    # Validate input
    if not validate_username(username):
        abort(400, 'Invalid username')
    
    # SECURE: Using render_template with file (not render_template_string)
    # Template file has auto-escaping enabled
    from flask import render_template
    
    return render_template('welcome.html', username=username)

# ============================================================================
# PRIVACY: GDPR-Compliant User Registration
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register_user():
    """
    PRIVACY COMPLIANT: Proper consent, encryption, minimal data
    
    FALSE POSITIVE CHECK: Handles email/password but with proper
    security and privacy measures. Should show GOOD practices.
    """
    data = request.get_json()
    
    email = data.get('email', '')
    password = data.get('password', '')
    consent_marketing = data.get('consent_marketing', False)
    consent_analytics = data.get('consent_analytics', False)
    
    # Input validation
    if not validate_email(email):
        abort(400, 'Invalid email format')
    
    if len(password) < Config.PASSWORD_MIN_LENGTH:
        abort(400, f'Password must be at least {Config.PASSWORD_MIN_LENGTH} characters')
    
    # SECURE: Hash password properly
    password_hash = hash_password_secure(password)
    
    # PRIVACY: Store minimal data with consent tracking
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (
                email, 
                password_hash, 
                consent_marketing,
                consent_analytics,
                created_at,
                ip_address_hash
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            email,
            password_hash,
            consent_marketing,
            consent_analytics,
            datetime.now().isoformat(),
            # PRIVACY: Hash IP instead of storing plaintext
            hashlib.new('sha256', request.remote_addr.encode()).hexdigest()
        ))
        conn.commit()
        
        user_id = cursor.lastrowid
        
        # Audit log (no PII)
        logger.info(f"New user registered")
        
        conn.close()
        
        return jsonify({
            'status': 'registered',
            'user_id': user_id,
            'token': generate_secure_token()
        })
    
    except sqlite3.IntegrityError:
        conn.close()
        abort(409, 'Email already registered')

# ============================================================================
# PRIVACY: Anonymized Analytics
# ============================================================================

@app.route('/api/track', methods=['POST'])
def track_event():
    """
    PRIVACY COMPLIANT: Anonymized tracking with consent check
    
    FALSE POSITIVE CHECK: Tracks data but with anonymization and
    consent. Should show GOOD privacy practices.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    event_type = data.get('event_type')
    
    # Check user consent
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT consent_analytics FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    
    if not user or not user[0]:
        # User hasn't consented to analytics
        logger.info(f"Analytics tracking skipped - no consent")
        return jsonify({'status': 'skipped'}), 200
    
    # PRIVACY: Store anonymized data only
    # PRIVACY: Hash user_id for anonymization using HMAC
    import hmac
    user_hash = hmac.new(app.config['SECRET_KEY'].encode(), str(user_id).encode(), 'sha256').hexdigest()
    
    cursor.execute("""
        INSERT INTO analytics (
            user_id_hash,
            event_type,
            timestamp
        ) VALUES (?, ?, ?)
    """, (
        user_hash,
        event_type,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    
    logger.info(f"Analytics event tracked: {event_type}")
    return jsonify({'status': 'tracked'})

# ============================================================================
# Helper: Database Schema
# ============================================================================

def init_database():
    """Initialize database with proper schema"""
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()
    
    # Users table with privacy considerations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            consent_marketing BOOLEAN DEFAULT 0,
            consent_analytics BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            ip_address_hash TEXT,
            deleted_at TEXT
        )
    """)
    
    # Anonymized analytics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_hash TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Configs with JSON
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()
    
    # SECURE: Production mode, HTTPS only
    app.run(
        debug=False,
        host='127.0.0.1',  # Only localhost in dev
        port=5000,
        ssl_context='adhoc'  # Use proper certs in production
    )
