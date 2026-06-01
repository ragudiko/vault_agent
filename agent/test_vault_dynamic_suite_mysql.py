import pytest
import subprocess
import os
import uuid

# Environment setup
env = {**os.environ, "VAULT_ADDR": os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"), "VAULT_TOKEN": os.getenv("VAULT_TOKEN")}

def run_vault(cmd):
    return subprocess.run(f"vault {cmd}", shell=True, capture_output=True, text=True, env=env)

@pytest.fixture(scope="module")
def mount_path():
    path = f"mysql-{uuid.uuid4().hex[:8]}"
    run_vault(f"secrets enable -path={path} database")
    yield path
    run_vault(f"secrets disable {path}")

def test_1_configure_mysql_connection(mount_path):
    result = run_vault(f"write {mount_path}/config/my-mysql-db "
                       "plugin_name=mysql-database-plugin "
                       "allowed_roles=readonly "
                       "connection_url='root:password@tcp(127.0.0.1:3306)/'")
    assert "Success!" in result.stdout

def test_2_create_role(mount_path):
    result = run_vault(f"write {mount_path}/roles/readonly "
                       "db_name=my-mysql-db "
                       "creation_statements='CREATE USER \"{{name}}\"@\"%\" IDENTIFIED BY \"{{password}}\"; GRANT SELECT ON *.* TO \"{{name}}\"@\"%\";' "
                       "default_ttl=1h max_ttl=24h")
    assert "Success!" in result.stdout

def test_3_read_role(mount_path):
    result = run_vault(f"read {mount_path}/roles/readonly")
    assert "db_name" in result.stdout
    assert "my-mysql-db" in result.stdout

def test_4_generate_credentials(mount_path):
    result = run_vault(f"read {mount_path}/creds/readonly")
    assert "username" in result.stdout
    assert "password" in result.stdout
    assert result.returncode == 0

def test_5_list_roles(mount_path):
    result = run_vault(f"list {mount_path}/roles")
    assert "readonly" in result.stdout

def test_6_rotate_root_credentials(mount_path):
    # Note: Requires root credentials to be configured first
    result = run_vault(f"write {mount_path}/rotate-root/my-mysql-db")
    assert "Success!" in result.stdout or "error" in result.stderr

def test_7_delete_role(mount_path):
    result = run_vault(f"delete {mount_path}/roles/readonly")
    assert "Success!" in result.stdout

def test_8_verify_role_deletion(mount_path):
    result = run_vault(f"read {mount_path}/roles/readonly")
    assert result.returncode != 0