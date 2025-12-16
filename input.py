import os
import sqlite3
import requests
import hashlib
import hmac
from urllib.parse import urlparse
from flask import Flask, request, jsonify
import subprocess
import yaml
import re

app = Flask(__name__)

PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH", "")

DB_FILE = os.environ.get("DB_FILE", "appdata.db")


def auth_user(info):
    # Use HMAC-SHA256 instead of plain MD5 for stronger integrity
    username = info.get("username", "")
    if not username:
        return ""
    hashed = hmac.new(INTERNAL_AUTH.encode(), username.encode(), hashlib.sha256).hexdigest()
    return hashed


def query_profile(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    q = "SELECT id, name, balance FROM profiles WHERE id = ?"
    c.execute(q, (uid,))
    data = c.fetchall()
    conn.close()
    return data


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    log = f"transfer:{target}:{amount}"
    print(log)
    url = payload.get("notify_url")
    # Validate notify_url to prevent SSRF
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("Invalid URL scheme")
    # Allow only explicit hosts (from ALLOWED_HOSTS env var) or any host over HTTPS
    allowed = os.environ.get("ALLOWED_HOSTS")
    if allowed:
        allowed_hosts = set(h.strip() for h in allowed.split(","))
        if parsed.hostname not in allowed_hosts:
            raise ValueError("Host not allowed")
    # prevent local addresses
    if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Local addresses not allowed")
    resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount})
    return resp.text


def update_records(path):
    # Only allow files in a configured directory or basename without path traversal
    base_dir = os.environ.get("CONFIG_DIR", ".")
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    if not abs_path.startswith(abs_base + os.sep):
        raise ValueError("Invalid config path")
    with open(abs_path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Sanitize filename to avoid directory traversal and injection
    if not re.match(r"^[A-Za-z0-9_\-]+$", name):
        raise ValueError("Invalid filename")
    zip_path = f"{name}.zip"
    # Use Python's zipfile module instead of shell to avoid shell injection
    import zipfile
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        # Include DB file if it exists; otherwise add an empty placeholder
        if os.path.exists(DB_FILE):
            z.write(DB_FILE)
        else:
            z.writestr(DB_FILE, b"")
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
    return jsonify({"result": transfer_funds(p)})


@app.route("/config", methods=["POST"])
def api_config():
    path = request.json.get("file")
    return jsonify(update_records(path))


@app.route("/export")
def api_export():
    name = request.args.get("name")
    export_data(name)
    return jsonify({"ok": 1})


if __name__ == "__main__":
    # Do not enable debug mode in production by default
    debug_mode = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")
    app.run(debug=debug_mode)
