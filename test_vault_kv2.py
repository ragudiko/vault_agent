import subprocess
import pytest

VLT_ADDR = "http://127.0.0.1:8200"
VLT_TOKEN = "root"

def run_vault_command(command):
    result = subprocess.run(
        ["vault", "-address=" + VLT_ADDR, "-token=" + VLT_TOKEN] + command,
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr

def test_enable_kv2():
    out, err = run_vault_command(["secrets", "enable", "-version=2", "kv"])
    assert "Success! Enabled the kv secrets engine" in out

def test_write_secret():
    out, err = run_vault_command(["write", "kv/my_secret", "value=initial"])
    assert "Success! Data written" in out

def test_read_secret():
    out, err = run_vault_command(["read", "kv/my_secret"])
    assert "value=initial" in out

def test_list_secrets():
    out, err = run_vault_command(["list", "kv/"])
    assert "my_secret" in out

def test_update_secret():
    out, err = run_vault_command(["write", "kv/my_secret", "value=updated"])
    assert "Success! Data written" in out

def test_delete_secret():
    out, err = run_vault_command(["delete", "kv/my_secret"])
    assert "Success! Data deleted" in out

def test_read_deleted_secret():
    out, err = run_vault_command(["read", "kv/my_secret"])
    assert "No value found" in err

Future Directions:
- Implement additional test cases for handling secret versioning.
- Add tests for pagination when listing secrets.
- Explore integration with CI/CD pipelines for automated testing.
- Investigate the use of fixtures for setting up and tearing down test environments.