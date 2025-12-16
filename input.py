import os
import re
import sqlite3
import requests
import logging
import zipfile
from flask import Flask, request, jsonify, abort
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import yaml
from urllib.parse import urlparse

# App and configuration
app = Flask(__name__)

# Load secrets from environment (avoid hardcoded secrets)
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")  # in prod set SECRET_KEY env var
DB_FILE = os.getenv("DB_FILE", "appdata.db")
CONFIG_DIR = os.getenv("CONFIG_DIR", os.path.join(os.getcwd(), "configs"))
ALLOWED_NOTIFY_HOSTS = set([h for h in os.getenv("ALLOWED_NOTIFY_HOSTS", "").split(",") if h])
TOKEN_MAX_AGE = int(os.getenv("TOKEN_MAX_AGE", "3600"))

# Logging configuration
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Token serializer
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Utilities
def generate_token(username):
    return serializer.dumps(username)


def verify_token(token):
    try:
        user = serializer.loads(token, max_age=TOKEN_MAX_AGE)
        return user
    except SignatureExpired:
        logger.warning("Token expired")
        return None
    except BadSignature:
        logger.warning("Invalid token signature")
        return None


def require_auth(fn):
    def wrapper(*args, **kwargs):
        auth_hdr = request.headers.get("Authorization", "")
        if not auth_hdr.startswith("Bearer "):
            abort(401, description="Missing or invalid Authorization header")
        token = auth_hdr.split(" ", 1)[1]
        user = verify_token(token)
        if not user:
            abort(401, description="Invalid or expired token")
        request.user = user
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


def auth_user(info):
    # Generate a time-limited token if username exists in DB
    username = info.get("username")
    if not username:
        raise ValueError("username required")
    # verify user exists
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM profiles WHERE name = ?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise ValueError("user not found")
    return generate_token(username)


def query_profile(uid):
    # Validate uid (allow only digits)
    if not uid or not re.fullmatch(r"\d+", uid):
        return []
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
    data = c.fetchall()
    conn.close()
    return data


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")
    if not url:
        raise ValueError("notify_url is required")

    parsed = urlparse(url)
    host = parsed.hostname
    if ALLOWED_NOTIFY_HOSTS and host not in ALLOWED_NOTIFY_HOSTS:
        raise ValueError("notify_url host not allowed")

    # Use timeouts and handle exceptions
    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.exception("failed to notify payment endpoint")
        raise


def update_records(path):
    # Prevent path traversal by restricting to CONFIG_DIR
    full = os.path.realpath(path)
    cfg_dir = os.path.realpath(CONFIG_DIR)
    if not full.startswith(cfg_dir + os.sep):
        raise ValueError("access to specified path is not allowed")
    with open(full) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Allow only safe filename characters
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", name):
        raise ValueError("invalid archive name")
    archive_name = f"{name}.zip"
    # Create zip file without using shell/ subprocess
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    return archive_name


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json
    try:
        token = auth_user(info)
        return jsonify({"token": token})
    except Exception as e:
        logger.exception("auth failed")
        abort(400, description=str(e))


@app.route("/profile")
@require_auth
def api_profile():
    uid = request.args.get("id")
    return jsonify(query_profile(uid))


@app.route("/transfer", methods=["POST"])
@require_auth
def api_transfer():
    p = request.json
    try:
        result = transfer_funds(p)
        return jsonify({"result": result})
    except Exception as e:
        abort(400, description=str(e))


@app.route("/config", methods=["POST"])
@require_auth
def api_config():
    path = request.json.get("file")
    try:
        return jsonify(update_records(path))
    except Exception as e:
        abort(400, description=str(e))


@app.route("/export")
@require_auth
def api_export():
    name = request.args.get("name")
    try:
        archive = export_data(name)
        return jsonify({"ok": 1, "archive": archive})
    except Exception as e:
        abort(400, description=str(e))


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)

