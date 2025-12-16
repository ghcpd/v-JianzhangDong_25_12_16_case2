import os
import importlib
import sqlite3
import tempfile
import shutil
import subprocess
import sys
import builtins
import pytest

MODULE_NAME = os.getenv('MODULE_NAME', 'input')


def setup_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
    c.execute('DELETE FROM profiles')
    c.execute('INSERT INTO profiles (id,name,balance) VALUES (1, "alice", 100.0)')
    c.execute('INSERT INTO profiles (id,name,balance) VALUES (2, "bob", 50.0)')
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def prepare(tmp_path, monkeypatch):
    # Ensure working directory and DB file
    cwd = tmp_path
    os.chdir(cwd)
    db_path = os.path.join(cwd, 'appdata.db')
    setup_db(db_path)

    # Create config and secret files
    cfg_dir = os.path.join(cwd, 'configs')
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, 'allowed.yaml'), 'w') as f:
        f.write('ok: true')
    secret_dir = os.path.join(cwd, 'secrets')
    os.makedirs(secret_dir, exist_ok=True)
    with open(os.path.join(secret_dir, 'secret.txt'), 'w') as f:
        f.write('TOPSECRET')

    yield


def import_module(name):
    if name in sys.modules:
        del sys.modules[name]
    return importlib.import_module(name)


def test_sql_injection_behavior():
    mod = import_module(MODULE_NAME)
    # vulnerable input_backup should return both rows for injected uid
    res = mod.query_profile("1' OR '1'='1")
    if MODULE_NAME == 'input_backup':
        assert len(res) == 2
    else:
        # patched version should not allow injection and return empty
        assert len(res) == 0


def test_update_records_path_restriction():
    mod = import_module(MODULE_NAME)
    # attempt path traversal
    path = os.path.join('configs', '..', 'secrets', 'secret.txt')
    if MODULE_NAME == 'input_backup':
        data = mod.update_records(path)
        # returns parsed YAML or raw content; check that secret is readable
        assert 'TOPSECRET' in str(data)
    else:
        with pytest.raises(Exception):
            mod.update_records(path)


def test_export_command_injection_behavior(monkeypatch):
    mod = import_module(MODULE_NAME)
    calls = {}

    def fake_popen(cmd, shell=None, *args, **kwargs):
        calls['cmd'] = cmd
        calls['shell'] = shell
        class Dummy:
            def __init__(self):
                pass
        return Dummy()

    monkeypatch.setattr('subprocess.Popen', fake_popen)

    if MODULE_NAME == 'input_backup':
        # backup uses shell=True and will pass user input into command string
        mod.export_data("injected;rm -rf /")
        assert 'cmd' in calls
        assert calls['shell'] is True
        assert 'injected' in calls['cmd']
    else:
        # patched version should not call subprocess and should create a zip file
        # ensure subprocess.Popen was not called
        mod.export_data("safe_name")
        assert 'cmd' not in calls
        assert os.path.exists('safe_name.zip')


def test_transfer_notify_host_validation(monkeypatch):
    # For patched module, ALLOWED_NOTIFY_HOSTS enforced
    # Set allowed hosts
    os.environ['ALLOWED_NOTIFY_HOSTS'] = 'example.com'
    mod = import_module(MODULE_NAME)
    sent = {}

    def fake_post(url, json=None, timeout=None):
        sent['url'] = url
        class R:
            status_code = 200
            text = 'ok'
            def raise_for_status(self):
                return None
        return R()

    monkeypatch.setattr('requests.post', fake_post)

    if MODULE_NAME == 'input_backup':
        # backup does not validate host
        res = mod.transfer_funds({'target': 'alice', 'amount': 10, 'notify_url': 'http://malicious.com/callback'})
        assert 'ok' in res or isinstance(res, str)
    else:
        # patched should reject unknown host
        with pytest.raises(Exception):
            mod.transfer_funds({'target': 'alice', 'amount': 10, 'notify_url': 'http://malicious.com/callback'})
        # allowed host should succeed
        res = mod.transfer_funds({'target': 'alice', 'amount': 10, 'notify_url': 'http://example.com/callback'})
        assert res == 'ok'


def test_auth_token_is_secure():
    mod = import_module(MODULE_NAME)
    # auth requires existing username; use alice
    if MODULE_NAME == 'input_backup':
        token = mod.auth_user({'username': 'alice'})
        # old token was md5 of username + INTERNAL_AUTH, should be lowercase hex length 32
        assert isinstance(token, str) and len(token) == 32
    else:
        token = mod.auth_user({'username': 'alice'})
        assert isinstance(token, str)
        # verify token
        user = mod.verify_token(token)
        assert user == 'alice'
