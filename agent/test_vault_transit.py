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
@pytest.mark.parametrize("encryption_key", ["aes256-gcm96", "chacha20-poly1305"])
def test_create_encryption_key(setup_vault, encryption_key):
    result = run_command(f"vault write -f transit/keys/{encryption_key} type={encryption_key}")
    assert "created_time" in result

def test_encrypt_data(setup_vault):
    data_to_encrypt = "test_data"
    result = run_command(f"vault write -f transit/encrypt/test_key plaintext={data_to_encrypt}")
    assert "ciphertext" in result

def test_decrypt_data(setup_vault):
    ciphertext = "vault:v1:encrypted_data_here"
    result = run_command(f"vault write -f transit/decrypt/test_key ciphertext={ciphertext}")
    assert "plaintext" in result
    assert result.split("plaintext = ")[1].strip() == "test_data"

def test_rewrap_data(setup_vault):
    ciphertext = "vault:v1:encrypted_data_here"
    result = run_command(f"vault write -f transit/rewrap/test_key ciphertext={ciphertext}")
    assert "ciphertext" in result
    assert result.split("ciphertext = ")[1].strip() != ciphertext

def test_delete_encryption_key(setup_vault):
    result = run_command("vault write -f transit/keys/test_key/delete")
    assert "deleted" in result

def test_rotate_encryption_key(setup_vault):
    result = run_command("vault write -f transit/keys/test_key/rotate")
    assert "rotation_time" in result

def test_export_encryption_key(setup_vault):
    result = run_command("vault write -f transit/keys/test_key/export")
    assert "key_material" in result

def test_import_encryption_key(setup_vault):
    key_material = "base64_encoded_key_here"
    result = run_command(f"vault write -f transit/keys/test_key/import key_material={key_material}")
    assert "imported_key_material" in result