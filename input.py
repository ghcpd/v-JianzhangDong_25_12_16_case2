import os
import re
import sqlite3
import requests
import hashlib
import hmac
import logging
from flask import Flask, request, jsonify, abort
import zipfile
import yaml
from urllib.parse import urlparse

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Secrets and configuration MUST come from environment in production
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")  # required for admin endpoints
DB_FILE = os.environ.get("DB_FILE", "appdata.db")
CONFIG_DIR = os.environ.get("CONFIG_DIR", "configs")

# Simple validators
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")
ID_RE = re.compile(r"^[0-9]+$")
AMOUNT_RE = re.compile(r"^\d+(?:\.\d{1,2})?$")


def _require_admin():
    token = request.headers.get("X-ADMIN-TOKEN")
    if not ADMIN_API_KEY or token != ADMIN_API_KEY:
        abort(401, "admin token required")


def auth_user(info):
    # Use HMAC-SHA256 with a secret (INTERNAL_AUTH) instead of MD5 concatenation
    username = (info or {}).get("username")
    if not username:
        abort(400, "username required")
    if not INTERNAL_AUTH:
        logger.warning("INTERNAL_AUTH not set; auth will be weaker in this environment")
    key = (INTERNAL_AUTH or "").encode()
    digest = hmac.new(key, username.encode(), hashlib.sha256).hexdigest()
    return digest


def query_profile(uid):
    # Validate input and use parameterized query to prevent SQL injection
    if not uid or not ID_RE.match(uid):
        abort(400, "invalid id")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def transfer_funds(payload):
    # Validate payload and protect against SSRF by restricting scheme and allowed hosts
    target = (payload or {}).get("target")
    amount = (payload or {}).get("amount")
    url = (payload or {}).get("notify_url")

    if not target or not re.match(r"^[A-Za-z0-9_\-]+$", str(target)):
        abort(400, "invalid target")
    if not amount or not AMOUNT_RE.match(str(amount)):
        abort(400, "invalid amount")
    if not url:
        abort(400, "notify_url required")

    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        abort(400, "notify_url must use https")
    hostname = parsed.hostname or ""
    # optional allowed hosts list via env var (comma separated)
    allowed = [h.strip() for h in os.environ.get("ALLOWED_CALLBACK_HOSTS", "").split(",") if h.strip()]
    if allowed and hostname not in allowed:
        abort(400, "notify_url host not allowed")

    # Mask sensitive info in logs
    logger.info("transfer to %s amount=%s notify=%s", target, "***", hostname)

    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        logger.exception("notify failed")
        abort(502, "notification failed")
    return resp.text


def update_records(path):
    # Only allow files within CONFIG_DIR and prevent path traversal
    if not path or not SAFE_NAME_RE.match(path):
        abort(400, "invalid file name")
    cfg_path = os.path.join(CONFIG_DIR, path)
    real = os.path.realpath(cfg_path)
    base = os.path.realpath(CONFIG_DIR)
    if not real.startswith(base + os.sep) and real != base:
        abort(400, "invalid file path")
    if not os.path.exists(real):
        abort(404, "file not found")
    with open(real, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Only allow safe archive names and use zipfile module (no shell)
    if not name or not SAFE_NAME_RE.match(name):
        abort(400, "invalid name")
    zip_path = f"{name}.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    except Exception:
        logger.exception("export failed")
        abort(500, "export failed")
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json
    return jsonify({"token": auth_user(info)})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    return jsonify(query_profile(uid))


@app.route("/transfer", methods=["POST"])
def api_transfer():
    p = request.json
    # require admin token for initiating transfers
    _require_admin()
    return jsonify({"result": transfer_funds(p)})


@app.route("/config", methods=["POST"])
def api_config():
    _require_admin()
    path = request.json.get("file")
    return jsonify(update_records(path))


@app.route("/export")
def api_export():
    _require_admin()
    name = request.args.get("name")
    export_data(name)
    return jsonify({"ok": 1})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    # never enable the interactive debugger in production by default
    app.run(debug=debug)

