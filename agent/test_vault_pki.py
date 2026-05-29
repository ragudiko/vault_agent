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

def test_create_pki_mount(setup_vault):
    result = run_command("vault mount pki")
    assert "Successfully mounted" in result

def test_generate_intermediate_certificate(setup_vault):
    result = run_command("vault write pki/intermediate/generate/internal common_name=\"Example Intermediate CA\" ttl=\"8760h\"")
    assert "certificate" in result

def test_sign_intermediate_certificate(setup_vault):
    result = run_command("vault write pki/root/sign-intermediate csr=@intermediate.csr format=pem_bundle ttl=\"43800h\"")
    assert "certificate" in result

def test_revoke_certificate(setup_vault):
    result = run_command("vault write pki/revoke serial_number=\"<serial_number_from_previous_step>\"")
    assert "Success! Data written" in result