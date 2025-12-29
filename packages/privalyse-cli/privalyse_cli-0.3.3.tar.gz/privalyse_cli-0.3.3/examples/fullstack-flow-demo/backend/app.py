from flask import Flask, request
import logging

app = Flask(__name__)

# Configure logging to file
logging.basicConfig(filename='app.log', level=logging.INFO)

@app.route('/api/signup', methods=['POST'])
def signup():
    # Source: API Input
    data = request.json
    
    # Extraction
    user_email = data.get('user_email')
    user_password = data.get('user_password')
    
    # Sink 1: Logging PII (Leak)
    logging.info(f"Processing signup for: {user_email}")
    
    # Sink 2: Logging Secrets (Critical Leak)
    logging.info(f"Password received: {user_password}")
    
    return {"status": "ok"}
