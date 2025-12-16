import os
import sqlite3
import requests
import hmac
import hashlib
import logging
import re
from flask import Flask, request, jsonify, abort
import zipfile
import yaml
from itsdangerous import URLSafeTimedSerializer
from urllib.parse import urlparse
from pathlib import Path

app = Flask(__name__)

# Load secrets from environment (do NOT hardcode in source)
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
ALLOWED_NOTIFY_HOSTS = os.environ.get("ALLOWED_NOTIFY_HOSTS", "").split(",") if os.environ.get("ALLOWED_NOTIFY_HOSTS") else []

DB_FILE = os.environ.get("DB_FILE", "appdata.db")
CONFIGS_DIR = Path(os.environ.get("CONFIGS_DIR", "configs")).resolve()
EXPORTS_DIR = Path(os.environ.get("EXPORTS_DIR", "exports")).resolve()

# Basic setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

if not SECRET_KEY:
    logger.warning("SECRET_KEY not set; generating an ephemeral key (do not use in production)")
    SECRET_KEY = os.urandom(32).hex()

serializer = URLSafeTimedSerializer(SECRET_KEY)

# Helpers

def generate_token(username):
    return serializer.dumps({"username": username})


def verify_token(token, max_age=3600):
    try:
        payload = serializer.loads(token, max_age=max_age)
        return payload.get("username")
    except Exception:
        return None


def require_auth(f):
    def wrapped(*args, **kwargs):
        token = request.headers.get("X-Auth-Token")
        if not token:
            abort(401, description="Missing auth token")
        user = verify_token(token)
        if not user:
            abort(401, description="Invalid or expired token")
        return f(*args, **kwargs)
    wrapped.__name__ = f.__name__
    return wrapped


def get_db_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# Application logic (secure replacements)

def auth_user(info):
    username = info.get("username")
    password = info.get("password")
    if not username or not password:
        abort(400, description="username and password required")
    if ADMIN_PASSWORD and not hmac.compare_digest(password, ADMIN_PASSWORD):
        abort(401, description="invalid credentials")
    # Issue a signed token
    token = generate_token(username)
    return token


def query_profile(uid):
    # validate uid (only integer ids allowed)
    if not isinstance(uid, (str, int)) or (isinstance(uid, str) and not uid.isdigit()):
        raise ValueError("invalid uid")
    uid_int = int(uid)
    with get_db_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, balance FROM profiles WHERE id = ?", (uid_int,))
        rows = c.fetchall()
    return [dict(r) for r in rows]


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")

    # input validation
    try:
        amount_val = float(amount)
    except Exception:
        abort(400, description="invalid amount")
    if amount_val <= 0:
        abort(400, description="amount must be positive")

    # validate URL (must be https and whitelisted host if configured)
    parsed = urlparse(url)
    if parsed.scheme != "https":
        abort(400, description="notify_url must use https")
    host = parsed.hostname
    if ALLOWED_NOTIFY_HOSTS and host not in ALLOWED_NOTIFY_HOSTS:
        abort(400, description="notify_url host not allowed")

    # send notification securely
    headers = {"Content-Type": "application/json"}
    payload = {"amount": amount_val}
    if PAYMENT_TOKEN:
        payload["token"] = PAYMENT_TOKEN

    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.error("notify request failed: %s", e)
        abort(502, description="failed to notify target")


def update_records(path):
    # Only allow reading files from CONFIGS_DIR
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    requested = Path(path).resolve()
    if CONFIGS_DIR not in requested.parents and requested != CONFIGS_DIR:
        raise ValueError("access to the requested path is not allowed")
    with open(requested, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Sanitize name and create zip using zipfile (no shell)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("invalid export name")
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = EXPORTS_DIR / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=Path(DB_FILE).name)
    return str(zip_path)


# Routes
@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    token = auth_user(info)
    return jsonify({"token": token})


@app.route("/profile")
@require_auth
def api_profile():
    uid = request.args.get("id")
    try:
        data = query_profile(uid)
    except ValueError as e:
        abort(400, description=str(e))
    return jsonify(data)


@app.route("/transfer", methods=["POST"])
@require_auth
def api_transfer():
    p = request.json or {}
    result = transfer_funds(p)
    return jsonify({"result": result})


@app.route("/config", methods=["POST"])
@require_auth
def api_config():
    path = request.json.get("file")
    try:
        data = update_records(path)
    except ValueError as e:
        abort(400, description=str(e))
    return jsonify(data)


@app.route("/export")
@require_auth
def api_export():
    name = request.args.get("name")
    try:
        zip_path = export_data(name)
    except ValueError as e:
        abort(400, description=str(e))
    return jsonify({"ok": 1, "file": zip_path})


if __name__ == "__main__":
    # Only enable debug when explicitly allowed via env var (do not default to True)
    debug_flag = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug_flag)

