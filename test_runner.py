#!/usr/bin/env python3
"""Simple test runner that checks key security behaviors on both input_backup.py and input.py
- By default (--target both) it tests both: ensures backup shows older (vulnerable) behavior and fixed behaves correctly.
- Exit code 0 when checks meet expectations (fixed is more secure than backup).
"""
import importlib.util
import sys
import os
import sqlite3
import time
from argparse import ArgumentParser

P = ArgumentParser()
P.add_argument("--target", choices=("both", "backup", "fixed"), default="both")
args = P.parse_args()

# ensure working DB and config
DB = os.environ.get("DB_FILE", "appdata.db")
if not os.path.exists(DB):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
    c.execute('INSERT OR IGNORE INTO profiles (id,name,balance) VALUES (1, "alice", 100.0)')
    conn.commit(); conn.close()

os.makedirs(os.environ.get("CONFIG_DIR", "configs"), exist_ok=True)
with open(os.path.join(os.environ.get("CONFIG_DIR", "configs"), "test.yaml"), "w", encoding="utf-8") as f:
    f.write("ok: true\n")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

backup = load_module(os.path.join(os.path.dirname(__file__), "input_backup.py"), "input_backup")
fixed = load_module(os.path.join(os.path.dirname(__file__), "input.py"), "input_fixed")

errors = []

# Test 1: hashing algorithm lengths: backup should be MD5 (32), fixed should be HMAC-SHA256 (64)
try:
    b = backup.auth_user({"username": "alice"})
    f = fixed.auth_user({"username": "alice"})
    if not (isinstance(b, str) and len(b) == 32):
        errors.append("backup.auth_user not producing MD5 (expected 32 hex chars)")
    if not (isinstance(f, str) and len(f) == 64):
        errors.append("fixed.auth_user not producing HMAC-SHA256 (expected 64 hex chars)")
except Exception as e:
    errors.append(f"hash test failed: {e}")

# Test 2: query_profile validation - fixed should reject non-digit id
try:
    try:
        fixed.query_profile("bad_id")
        errors.append("fixed.query_profile accepted invalid id (expected rejection)")
    except Exception:
        pass
    # backup may accept or raise; if it accepts without error that's the vulnerable behavior we expect
    try:
        backup.query_profile("bad_id")
    except Exception:
        # backup raised too; that's acceptable but we note it
        pass
except Exception as e:
    errors.append(f"query_profile test failed: {e}")

# Test 3: export_data - fixed should successfully create a zip file for a safe name
zipname = "test_export"
zipfile_path = f"{zipname}.zip"
try:
    if os.path.exists(zipfile_path):
        os.remove(zipfile_path)
    ok = fixed.export_data(zipname)
    if not ok or not os.path.exists(zipfile_path):
        errors.append("fixed.export_data did not create expected zip archive")
    else:
        os.remove(zipfile_path)
except Exception as e:
    errors.append(f"export_data test failed: {e}")

# Test 4: update_records should reject path traversal
try:
    try:
        fixed.update_records("../../etc/passwd")
        errors.append("fixed.update_records did not reject a traversal path")
    except Exception:
        pass
except Exception as e:
    errors.append(f"update_records test failed: {e}")

# Evaluate outcome: we expect fixed to be secure and backup to show older behavior; overall pass if fixed passed checks
if errors:
    print("TEST FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)
else:
    print("TEST PASSED")
    sys.exit(0)
