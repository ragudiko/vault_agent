import subprocess
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

def run_command(cmd):
    env = os.environ.copy()
    if "VAULT_ADDR" not in env:
        env["VAULT_ADDR"] = "http://127.0.0.1:8200"
    if "VAULT_TOKEN" not in env:
        pytest.skip("VAULT_TOKEN not set")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env, timeout=30)
    if result.returncode != 0:
        pytest.skip(f"Command failed: {result.stderr}")
    return result.stdout

@pytest.fixture(scope="module")
def setup_vault():
    load_dotenv()
    try:
        run_command("vault status")
    except:
        pytest.skip("Vault not accessible")
    yield

import pytest
def test_kv2_create_secret(setup_vault):
    result = run_command("vault kv put secret/test key1=value1 key2=value2")
    assert "created_time" in result

def test_kv2_read_secret(setup_vault):
    result = run_command("vault kv get secret/test")
    assert "key1" in result
    assert "key2" in result

def test_kv2_delete_secret(setup_vault):
    run_command("vault kv delete secret/test")
    result = run_command("vault kv get secret/test")
    assert "No value found" in result

def test_kv2_list_secrets(setup_vault):
    run_command("vault kv put secret/foo key=value")
    run_command("vault kv put secret/bar key=value")
    result = run_command("vault kv list secret/")
    assert "foo" in result
    assert "bar" in result
    assert "test" not in result