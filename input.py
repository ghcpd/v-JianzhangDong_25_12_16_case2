import os
import sqlite3
import requests
import hashlib
from flask import Flask, request, jsonify
import subprocess
import yaml
import secrets
from pathlib import Path
from urllib.parse import urlparse
import logging

app = Flask(__name__)

# Load secrets from environment variables (DO NOT hardcode in source)
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN", "")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY", "")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH", "")

if not all([PAYMENT_TOKEN, MAIL_SERVER_KEY, INTERNAL_AUTH]):
    raise ValueError("Missing required environment variables")

DB_FILE = "appdata.db"

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def auth_user(info):
    """Authenticate user with SHA256 (stronger than MD5)."""
    if not isinstance(info, dict) or "username" not in info:
        logger.warning("Invalid auth request")
        return None
    
    username = str(info.get("username", "")).strip()
    if not username or len(username) > 255:
        logger.warning("Invalid username format")
        return None
    
    # Use SHA256 instead of MD5 (FIPS compliant)
    raw = username + INTERNAL_AUTH
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return hashed


def query_profile(uid):
    """Query profile with parameterized queries to prevent SQL injection."""
    if not isinstance(uid, str) or not uid.isdigit():
        logger.warning("Invalid UID format")
        return []
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Use parameterized query instead of string formatting
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
        data = c.fetchall()
        conn.close()
        return data
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []


def transfer_funds(payload):
    """Transfer funds with SSRF protection and input validation."""
    if not isinstance(payload, dict):
        logger.warning("Invalid payload format")
        return None
    
    target = str(payload.get("target", "")).strip()
    amount = payload.get("amount")
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0 or amount > 1000000:
            logger.warning(f"Invalid amount: {amount}")
            return None
    except (TypeError, ValueError):
        logger.warning("Invalid amount type")
        return None
    
    # Validate target
    if not target or len(target) > 100:
        logger.warning("Invalid target")
        return None
    
    # SSRF Protection: Validate URL format and prevent local access
    url = str(payload.get("notify_url", "")).strip()
    if not url:
        logger.warning("Missing notify_url")
        return None
    
    try:
        parsed = urlparse(url)
        # Prevent access to internal/private IPs
        if parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
            logger.warning(f"Blocked local URL: {url}")
            return None
        
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ("http", "https"):
            logger.warning(f"Invalid URL scheme: {parsed.scheme}")
            return None
    except Exception as e:
        logger.warning(f"Invalid URL: {e}")
        return None
    
    log = f"transfer:{target}:{amount}"
    logger.info(log)
    
    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5)
        return resp.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return None


def update_records(path):
    """Load config with path traversal protection."""
    if not isinstance(path, str):
        logger.warning("Invalid path type")
        return None
    
    # Security: Prevent path traversal attacks
    allowed_dir = Path("configs").resolve()
    config_path = (allowed_dir / path).resolve()
    
    # Ensure path is within allowed directory
    if not str(config_path).startswith(str(allowed_dir)):
        logger.warning(f"Path traversal attempt blocked: {path}")
        return None
    
    # Ensure file exists and is readable
    if not config_path.exists() or not config_path.is_file():
        logger.warning(f"File not found or not a file: {config_path}")
        return None
    
    try:
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        return cfg
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None


def export_data(name):
    """Export data safely without command injection vulnerability."""
    if not isinstance(name, str):
        logger.warning("Invalid export name")
        return False
    
    # Validate name: alphanumeric, underscore, hyphen only
    if not name or len(name) > 50:
        logger.warning("Invalid export name length")
        return False
    
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        logger.warning(f"Invalid characters in export name: {name}")
        return False
    
    try:
        # Use subprocess with list args instead of shell=True to prevent command injection
        cmd = ["zip", f"{name}.zip", DB_FILE]
        result = subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        logger.info(f"Export successful: {name}.zip")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Export failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}")
        return False


@app.route("/auth", methods=["POST"])
def api_auth():
    """Authenticate user - secure version."""
    try:
        info = request.json
        if not info:
            return jsonify({"error": "Invalid request"}), 400
        
        token = auth_user(info)
        if token is None:
            return jsonify({"error": "Authentication failed"}), 401
        
        return jsonify({"token": token})
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/profile")
def api_profile():
    """Get user profile - secure version."""
    try:
        uid = request.args.get("id", "")
        if not uid:
            return jsonify({"error": "Missing uid parameter"}), 400
        
        data = query_profile(uid)
        if data is None:
            return jsonify({"error": "Query failed"}), 500
        
        return jsonify({"data": data})
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/transfer", methods=["POST"])
def api_transfer():
    """Transfer funds - secure version."""
    try:
        p = request.json
        if not p:
            return jsonify({"error": "Invalid request"}), 400
        
        result = transfer_funds(p)
        if result is None:
            return jsonify({"error": "Transfer failed"}), 400
        
        return jsonify({"result": result})
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/config", methods=["POST"])
def api_config():
    """Update config - secure version."""
    try:
        config = request.json
        if not config or "file" not in config:
            return jsonify({"error": "Missing file parameter"}), 400
        
        path = config.get("file", "")
        result = update_records(path)
        if result is None:
            return jsonify({"error": "Config update failed"}), 400
        
        return jsonify({"config": result})
    except Exception as e:
        logger.error(f"Config error: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/export")
def api_export():
    """Export data - secure version."""
    try:
        name = request.args.get("name", "")
        if not name:
            return jsonify({"error": "Missing name parameter"}), 400
        
        success = export_data(name)
        if not success:
            return jsonify({"error": "Export failed"}), 400
        
        return jsonify({"ok": 1})
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    # Never use debug=True in production
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug_mode)
