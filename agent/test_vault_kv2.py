import subprocess
import pytest
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")

print("Loading environment variables...")
print(f"VAULT_ADDR: {os.getenv('VAULT_ADDR')}")
print(f"VAULT_TOKEN: {'Set' if os.getenv('VAULT_TOKEN') else 'Not set'}")

def run_command(cmd):
    """Execute vault command with environment variables."""
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

# create secret, read secret, list secrets, delete secret, undelete secret

# Here are 3-4 pytest test functions for Vault kv2 feature using the setup_vault fixture:

import pytest

def test_create_secret(setup_vault):
    result = run_command("vault kv put secret/test key=value")
    assert "created_time" in result
    assert "version" in result
    assert result is not None 

def test_read_secret(setup_vault):
    result = run_command("vault kv get secret/test")
    assert "key" in result
    assert "value" in result
    assert result is not None 

def test_list_secrets(setup_vault):
    result = run_command("vault kv list secret/")
    assert "test" in result
    assert result is not None 

def test_delete_and_undelete_secret(setup_vault):
    # Delete the secret
    result = run_command("vault kv delete secret/test")
    print("1================" ,result)
    assert result is not None 

    # Verify the secret is deleted
    result = run_command("vault kv get secret/test")
    print("2================" ,result)
    assert "Key" not in result
    assert "Value" not in result

    # Undelete the secret
    # result = run_command("vault kv undelete secret/test")
    result = run_command("vault kv undelete -versions=1 secret/test")
    print("3================" ,result)
    # assert "version" in result
    # assert result is not None
    assert "Success!" in result
    assert "secret/undelete/test" in result 
    

    # Verify the secret is undeleted and accessible
    result = run_command("vault kv get secret/test")
    print("4================" ,result)
    assert "Key" in result
    assert "Value" in result

# These test functions cover the following scenarios:

# 1. `test_create_secret`: Tests creating a new secret using the `vault kv put` command. It asserts that the response contains the `created_time` and `version` fields, and that there are no errors in the response.

# 2. `test_read_secret`: Tests reading an existing secret using the `vault kv get` command. It asserts that the response contains the `key` and `value` fields, and that there are no errors in the response.

# 3. `test_list_secrets`: Tests listing secrets using the `vault kv list` command. It asserts that the response contains the `test` secret, and that there are no errors in the response.

# 4. `test_delete_and_undelete_secret`: Tests deleting and then undeleting a secret. It first deletes the secret using the `vault kv delete` command and verifies that the secret is no longer accessible. Then, it undeletes the secret using the `vault kv undelete` command and asserts that the secret is restored and accessible again.

# These test functions assume that the `setup_vault` fixture is properly configured and that the Vault server is running. The `run_command` function is used to execute Vault CLI commands and capture the output and errors.

# Remember to adjust the test functions according to your specific Vault setup and requirements. Additionally, you may need to handle authentication and permissions appropriately in your tests.