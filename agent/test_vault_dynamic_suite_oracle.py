import pytest
import subprocess
import os
import uuid

# Environment setup
env = {
    **os.environ, 
    "VAULT_ADDR": os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"), 
    "VAULT_TOKEN": os.getenv("VAULT_TOKEN")
}

def run_vault(cmd):
    return subprocess.run(f"vault {cmd}", shell=True, capture_output=True, text=True, env=env)

@pytest.fixture(scope="module")
def oracle_path():
    path = f"oracle-{uuid.uuid4().hex[:8]}"
    yield path

def test_1_enable_database_engine():
    result = run_vault("secrets enable database")
    assert result.returncode == 0 or "path is already in use" in result.stderr

def test_2_configure_oracle_connection(oracle_path):
    # Configure the Oracle connection
    cmd = (f"write database/config/{oracle_path} "
           f"plugin_name=oracle-database-plugin "
           f"allowed_roles='*' "
           f"connection_url='oracle://user:pass@localhost:1521/xe'")
    result = run_vault(cmd)
    assert "Success!" in result.stdout

def test_3_create_oracle_role(oracle_path):
    role_name = f"role-{uuid.uuid4().hex[:8]}"
    cmd = (f"write database/roles/{role_name} "
           f"db_name={oracle_path} "
           f"creation_statements='CREATE USER {{name}} IDENTIFIED BY {{password}};' "
           f"default_ttl=1h max_ttl=24h")
    result = run_vault(cmd)
    assert "Success!" in result.stdout

def test_4_read_oracle_connection(oracle_path):
    result = run_vault(f"read database/config/{oracle_path}")
    assert oracle_path in result.stdout

def test_5_generate_oracle_credentials(oracle_path):
    # Assumes a role 'readonly' was created via test_3 logic
    result = run_vault(f"read database/creds/readonly")
    assert result.returncode == 0
    assert "username" in result.stdout

def test_6_rotate_oracle_root_credentials(oracle_path):
    result = run_vault(f"write -f database/rotate-root/{oracle_path}")
    assert "Success!" in result.stdout

def test_7_list_database_connections():
    result = run_vault("list database/config")
    assert result.returncode == 0

def test_8_delete_oracle_connection(oracle_path):
    result = run_vault(f"delete database/config/{oracle_path}")
    assert result.returncode == 0