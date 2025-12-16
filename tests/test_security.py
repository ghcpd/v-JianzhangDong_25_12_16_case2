import os
import pytest
import importlib
import inspect


def get_module(name):
    return importlib.import_module(name)


def test_hardcoded_secrets_present():
    # Only run when testing the backup (vulnerable) code
    if os.getenv("TEST_TARGET") != "backup":
        pytest.skip("Not running backup tests")
    data = open("input_backup.py").read()
    assert "tok_production_998877" in data
    assert "mail_srv_key_ABCDEFG" in data
    assert "admin_internal_5566" in data


def test_hardcoded_secrets_absent():
    if os.getenv("TEST_TARGET") != "fixed":
        pytest.skip("Not running fixed tests")
    data = open("input.py").read()
    assert "tok_production_998877" not in data
    assert "mail_srv_key_ABCDEFG" not in data
    assert "admin_internal_5566" not in data


def test_sql_parameterization_backup():
    if os.getenv("TEST_TARGET") != "backup":
        pytest.skip("Not running backup tests")
    mod = get_module("input_backup")
    src = inspect.getsource(mod.query_profile)
    assert "%s" in src  # string interpolation present -> vulnerable


def test_sql_parameterization_fixed():
    if os.getenv("TEST_TARGET") != "fixed":
        pytest.skip("Not running fixed tests")
    mod = get_module("input")
    src = inspect.getsource(mod.query_profile)
    assert "?" in src  # parameterized query used


def test_transfer_funds_ssrf_validation_backup():
    if os.getenv("TEST_TARGET") != "backup":
        pytest.skip("Not running backup tests")
    mod = get_module("input_backup")
    # With no validation, it should attempt to post; we mock requests.post
    def fake_post(url, json=None):
        class Resp:
            text = "ok"
        return Resp()
        
    import requests
    monkey = type('m', (), {'post': fake_post})
    # monkeypatch requests
    # We'll just call and expect no exception
    payload = {"notify_url": "http://localhost:1234/callback", "amount": 1}
    # replace requests.post temporarily
    old = requests.post
    requests.post = fake_post
    try:
        res = mod.transfer_funds(payload)
        assert res == "ok"
    finally:
        requests.post = old


def test_transfer_funds_ssrf_validation_fixed():
    if os.getenv("TEST_TARGET") != "fixed":
        pytest.skip("Not running fixed tests")
    mod = get_module("input")
    # Mock requests.post
    def fake_post(url, json=None):
        class Resp:
            text = "ok"
        return Resp()
    import requests
    old = requests.post
    requests.post = fake_post
    try:
        # Local host should be blocked
        payload = {"notify_url": "http://localhost:1234/callback", "amount": 1}
        with pytest.raises(ValueError):
            mod.transfer_funds(payload)

        # Allowed HTTPS should pass
        payload2 = {"notify_url": "https://example.com/ok", "amount": 1}
        res = mod.transfer_funds(payload2)
        assert res == "ok"

    finally:
        requests.post = old


def test_export_sanitization_backup():
    if os.getenv("TEST_TARGET") != "backup":
        pytest.skip("Not running backup tests")
    mod = get_module("input_backup")
    # The backup uses shell command; test that it constructs shell command with passed name
    # It's difficult to assert internal, so just call with safe name and expect True
    assert mod.export_data("testname")


def test_export_sanitization_fixed():
    if os.getenv("TEST_TARGET") != "fixed":
        pytest.skip("Not running fixed tests")
    mod = get_module("input")
    # Should reject invalid filename
    with pytest.raises(ValueError):
        mod.export_data("../evil")

    # Should accept valid filename
    assert mod.export_data("testname")


def test_update_records_path_backup():
    if os.getenv("TEST_TARGET") != "backup":
        pytest.skip("Not running backup tests")
    mod = get_module("input_backup")
    # backup allows path traversal, so provide path that could be dangerous; here just run OK
    # No exception expected
    open("tmp.yaml", "w").write("a: 1")
    try:
        cfg = mod.update_records("tmp.yaml")
        assert cfg == {"a": 1}
    finally:
        os.remove("tmp.yaml")


def test_update_records_path_fixed():
    if os.getenv("TEST_TARGET") != "fixed":
        pytest.skip("Not running fixed tests")
    mod = get_module("input")
    # Create temporary file in current dir
    open("tmp.yaml", "w").write("a: 1")
    try:
        cfg = mod.update_records("tmp.yaml")
        assert cfg == {"a": 1}
    finally:
        os.remove("tmp.yaml")
        
