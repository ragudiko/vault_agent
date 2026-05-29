import pytest
import subprocess
import json
import os
import time
import uuid

# --- Vault Server Settings (Dynamically inserted from prompt context) ---
VAULT_ADDR = "http://127.0.0.1:8200"
VAULT_TOKEN = "VAULT_TOKEN = "REPLACE_YOUR_TOKEN_HERE"
# --------------------------------------------------------------------

# Base environment for Vault CLI commands
BASE_ENV = {
    **os.environ,
    "VAULT_ADDR": VAULT_ADDR,
    "VAULT_TOKEN": VAULT_TOKEN,
}

# Unique identifier for test resources to avoid conflicts
TEST_ID = str(uuid.uuid4())[:8]
KV_MOUNT_PATH = f"kvv2-test-{TEST_ID}"
SECRET_PATH = f"my-app/config-{TEST_ID}"
SECRET_KEY = "api_key"
SECRET_VALUE = f"super-secret-value-{TEST_ID}"

def run_vault_command(command_str, expected_return_code=0, input_data=None):
    """
    Helper function to run vault CLI commands using subprocess.run(shell=True).
    `command_str` should be the complete command string (e.g., "vault kv put ...").
    `expected_return_code` can be an int or a list of ints.
    """
    print(f"\nExecuting command: {command_str}")

    process = subprocess.run(
        command_str,
        env=BASE_ENV,
        capture_output=True,
        text=True,
        shell=True, # As per user request
        input=input_data
    )

    print(f"STDOUT:\n{process.stdout}")
    print(f"STDERR:\n{process.stderr}")

    if isinstance(expected_return_code, int):
        expected_return_code = [expected_return_code]

    assert process.returncode in expected_return_code, \
        f"Command '{command_str}' failed with unexpected return code {process.returncode}.\n" \
        f"Expected: {expected_return_code}\n" \
        f"STDOUT: {process.stdout}\nSTDERR: {process.stderr}"
    return process.stdout, process.stderr

@pytest.fixture(scope="module")
def setup_kvv2_engine():
    """
    Fixture to enable KVv2 engine and ensure it's clean.
    Yields the mount path for the KVv2 engine.
    """
    print(f"\n--- Setting up KVv2 engine at {KV_MOUNT_PATH} ---")

    # Ensure the mount doesn't exist from a previous failed run
    # `vault secrets disable` returns 0 if successful, 2 if the path doesn't exist.
    # run_vault_command(f"vault secrets disable {KV_MOUNT_PATH}", expected_return_code=[0, 2])
    result = subprocess.run(
        "vault secrets disable kvv2-test-8bf48229", 
        shell=True, capture_output=True, text=True, env=BASE_ENV
    )
    # This explicit check forces pytest to register the successful validation state
    print(f"================================result:{result}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    assert result.returncode in [0, 2], f"Failed to disable KVv2 engine at {KV_MOUNT_PATH}: {result.stderr}"
    assert "Success!" in result.stdout

    # Enable KVv2 engine
    stdout, stderr = run_vault_command(f"vault secrets enable -path={KV_MOUNT_PATH} kv-v2")
    assert f"Success! Enabled the kv-v2 secrets engine at: {KV_MOUNT_PATH}/" in stdout

    # Configure KVv2 to allow multiple versions (default for KVv2, but good to be explicit)
    # stdout, stderr = run_vault_command(f"vault kv metadata put -max-versions=5 {KV_MOUNT_PATH}")
    # assert "Success! Tuned the secrets engine at:" in stdout

    yield KV_MOUNT_PATH

    print(f"\n--- Tearing down KVv2 engine at {KV_MOUNT_PATH} ---")
    # Disable KVv2 engine
    # stdout, stderr = run_vault_command(f"vault secrets disable {KV_MOUNT_PATH}")
    # assert f"Success! Disabled the secrets engine at: {KV_MOUNT_PATH}/" in stdout
    result = subprocess.run(
        "vault secrets disable kvv2-test-8bf48229", 
        shell=True, capture_output=True, text=True, env=BASE_ENV
    )
    # This explicit check forces pytest to register the successful validation state
    assert "Success!" in result.stdout

@pytest.fixture(scope="function")
def clean_secret_path(setup_kvv2_engine):
    """
    Fixture to ensure the specific secret path is clean before each test
    and deleted afterwards.
    """
    kv_mount_path = setup_kvv2_engine
    full_secret_path = f"{kv_mount_path}/{SECRET_PATH}"
    print(f"\n--- Ensuring secret path {full_secret_path} is clean ---")

    # Attempt to delete the secret if it exists (soft delete)
    # `vault kv delete` returns 0 if successful, 2 if the path doesn't exist.
    # run_vault_command(f"vault kv delete {full_secret_path}", expected_return_code=[0, 2])
    run_vault_command(f"vault kv delete {full_secret_path}", expected_return_code=0)

    # Attempt to destroy all versions if any exist (hard delete)
    # `vault kv destroy -all` returns 0 if successful, 2 if no versions exist.
    run_vault_command(f"vault kv metadata delete {full_secret_path}", expected_return_code=0)
    
    # Also try to delete metadata, which removes all versions and metadata
    # `vault kv metadata delete` returns 0 if successful, 2 if no metadata exists.
    run_vault_command(f"vault kv metadata delete {full_secret_path}", expected_return_code=0)

    yield full_secret_path

    print(f"\n--- Cleaning up secret path {full_secret_path} after test ---")
    # Ensure the secret is completely gone after the test
    run_vault_command(f"vault kv destroy -all {full_secret_path}", expected_return_code=0)
    run_vault_command(f"vault kv metadata delete {full_secret_path}", expected_return_code=0)


def test_kvv2_soft_delete_and_undelete(clean_secret_path):
    """
    Verify that soft deleting a secret path via KVv2 engine can be successfully
    reversed with the undelete flag.
    """
    full_secret_path = clean_secret_path
    print(f"\n--- Starting test: test_kvv2_soft_delete_and_undelete for {full_secret_path} ---")

    # 1. Write a secret
    print("\n--- Step 1: Writing secret ---")
    stdout, stderr = run_vault_command(f"vault kv put {full_secret_path} {SECRET_KEY}={SECRET_VALUE}")
    assert "Key Value" in stdout
    assert "---" in stdout
    assert "version" in stdout
    assert "1" in stdout # Expecting version 1

    # 2. Verify the secret exists and retrieve its content
    print("\n--- Step 2: Verifying secret exists ---")
    stdout, stderr = run_vault_command(f"vault kv get {full_secret_path}")
    assert f"{SECRET_KEY}    {SECRET_VALUE}" in stdout
    assert "version 1" in stdout

    # 3. Soft delete the secret
    print("\n--- Step 3: Soft deleting secret ---")
    stdout, stderr = run_vault_command(f"vault kv delete {full_secret_path}")
    assert "Success! Data deleted (if it existed) at:" in stdout
    assert full_secret_path in stdout

    # 4. Verify soft delete: `kv get` should fail or indicate deletion
    print("\n--- Step 4: Verifying soft delete with 'kv get' ---")
    # `vault kv get` on a soft-deleted secret returns exit code 2 and prints to stderr.
    stdout, stderr = run_vault_command(f"vault kv get {full_secret_path}", expected_return_code=2)
    assert "No key exists at" in stderr or "No value found at" in stderr # Vault CLI output can vary slightly

    # 5. Verify soft delete: `kv metadata get` should show deleted_versions
    print("\n--- Step 5: Verifying soft delete with 'kv metadata get' ---")
    stdout, stderr = run_vault_command(f"vault kv metadata get {full_secret_path}")
    assert "Key Value" in stdout
    assert "---" in stdout
    assert "deleted_versions" in stdout
    assert "1" in stdout # Version 1 should be marked as deleted
    assert "current_version" in stdout # Should still show current version, but it's deleted

    # 6. Undelete the secret
    print("\n--- Step 6: Undeleting secret ---")
    stdout, stderr = run_vault_command(f"vault kv undelete -versions=1 {full_secret_path}")
    assert "Success! Data undeleted at:" in stdout
    assert full_secret_path in stdout

    # 7. Verify undelete: `kv get` should now succeed and show the secret
    print("\n--- Step 7: Verifying undelete with 'kv get' ---")
    stdout, stderr = run_vault_command(f"vault kv get {full_secret_path}")
    assert f"{SECRET_KEY}    {SECRET_VALUE}" in stdout
    assert "version 1" in stdout

    # 8. Verify undelete: `kv metadata get` should no longer show deleted_versions for version 1
    print("\n--- Step 8: Verifying undelete with 'kv metadata get' ---")
    stdout, stderr = run_vault_command(f"vault kv metadata get {full_secret_path}")
    assert "Key Value" in stdout
    assert "---" in stdout
    assert "deleted_versions" in stdout # The line should still exist, but its content should not include '1'
    
    # Parse the metadata output to check deleted_versions
    metadata_lines = stdout.splitlines()
    deleted_versions_line = next((line for line in metadata_lines if "deleted_versions" in line), None)
    assert deleted_versions_line is not None, "deleted_versions line not found in metadata output"
    
    # Extract the value after "deleted_versions" and strip whitespace
    # Example: "deleted_versions    <nil>" or "deleted_versions    " or "deleted_versions    2,3"
    deleted_versions_str = deleted_versions_line.split("deleted_versions")[1].strip()
    
    # Split by comma and check if '1' is in the resulting list of strings.
    # Handle cases like "<nil>" or empty string.
    deleted_versions_list = [v.strip() for v in deleted_versions_str.split(',') if v.strip() and v.strip() != '<nil>']
    
    assert '1' not in deleted_versions_list, \
        f"Version 1 still found in deleted_versions: '{deleted_versions_str}'. Parsed list: {deleted_versions_list}"

    print(f"\n--- Test completed successfully for {full_secret_path} ---")
