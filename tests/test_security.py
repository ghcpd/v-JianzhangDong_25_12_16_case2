import os
import importlib.util
from importlib.machinery import SourceFileLoader
import sqlite3
import pytest
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent.parent


def load_module(target):
    path = BASE / f"{target}.py"
    spec = importlib.util.spec_from_loader(target, SourceFileLoader(target, str(path)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def prepare_db(tmp_path, monkeypatch):
    # Ensure a fresh DB for each test
    db_path = BASE / "appdata.db"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)")
    c.execute("INSERT INTO profiles (id, name, balance) VALUES (1, 'Alice', 100.0)")
    c.execute("INSERT INTO profiles (id, name, balance) VALUES (2, 'Bob', 200.0)")
    conn.commit()
    conn.close()
    # prepare files for update_records test
    secrets = BASE / "secrets.txt"
    secrets.write_text("secret: top\n")
    configs_dir = BASE / "configs"
    configs_dir.mkdir(exist_ok=True)
    (configs_dir / "allowed.yaml").write_text("ok: true\n")


def test_sql_injection_behavior(monkeypatch):
    # BACKUP (vulnerable) should return both rows when given injection
    backup = load_module("input_backup")
    res = backup.query_profile("1' OR '1'='1")
    assert isinstance(res, list)
    assert len(res) >= 2

    # FIXED should reject non-numeric uid
    fixed = load_module("input")
    with pytest.raises(ValueError):
        fixed.query_profile("1' OR '1'='1")


def test_update_records_path_traversal():
    backup = load_module("input_backup")
    # backup will read arbitrary file
    data = backup.update_records(str(Path(__file__).resolve().parent.parent / "secrets.txt"))
    assert isinstance(data, dict) or isinstance(data, list) or isinstance(data, str)

    fixed = load_module("input")
    # fixed should not allow reading files outside configs dir
    with pytest.raises(ValueError):
        fixed.update_records(str(Path(__file__).resolve().parent.parent / "secrets.txt"))


def test_transfer_notify_url_validation(monkeypatch):
    class DummyResp:
        def __init__(self):
            self.text = "ok"

        def raise_for_status(self):
            return None

    backup = load_module("input_backup")
    # Monkeypatch requests.post for backup
    monkeypatch.setattr(backup, "requests", type("R", (), {"post": lambda *a, **k: DummyResp()}))
    out = backup.transfer_funds({"target": "x", "amount": 10, "notify_url": "http://example.com"})
    assert out == "ok"

    fixed = load_module("input")
    # For fixed, http (non-https) should be rejected
    with pytest.raises(Exception):
        fixed.transfer_funds({"target": "x", "amount": 10, "notify_url": "http://example.com"})
