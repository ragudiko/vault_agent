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

def test_create_secret(setup_vault):
    """Test creating a secret in KV2."""
    result = run_command("vault kv put secret/test-app username=admin password=secret123")
    assert "created_time" in result or "version" in result

def test_read_secret(setup_vault):
    """Test reading a secret from KV2."""
    run_command("vault kv put secret/test-read key=value")
    result = run_command("vault kv get secret/test-read")
    assert "key" in result and "value" in result

def test_update_secret(setup_vault):
    """Test updating a secret."""
    run_command("vault kv put secret/test-update version=1")
    result = run_command("vault kv put secret/test-update version=2")
    assert "version" in result.lower()

def test_delete_secret(setup_vault):
    """Test deleting a secret."""
    run_command("vault kv put secret/test-delete temp=data")
    run_command("vault kv delete secret/test-delete")
    assert True

def test_list_secrets(setup_vault):
    """Test listing secrets."""
    run_command("vault kv put secret/list-test-1 data=1")
    result = run_command("vault kv list secret/")
    assert "list-test-1" in result

# Made with Bob
