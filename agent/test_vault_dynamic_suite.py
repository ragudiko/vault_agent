import pytest
import subprocess
import os
import uuid

from dotenv import load_dotenv

load_dotenv("/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")

# Setup environment context
env = {
    **os.environ, 
    "VAULT_ADDR": os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"), 
    "VAULT_TOKEN": os.getenv("VAULT_TOKEN")
}

@pytest.fixture(scope="module", autouse=True)
def setup_userpass():
    """Enable the userpass auth engine once for the test module."""
    subprocess.run("vault auth enable userpass", shell=True, env=env)
    yield
    subprocess.run("vault auth disable userpass", shell=True, env=env)

def test_create_user():
    """Test creating a new user in the userpass backend."""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    cmd = f"vault write auth/userpass/users/{username} password=password123"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    
    assert result.returncode == 0
    assert "Success!" in result.stdout

def test_read_user():
    """Test reading back a user configuration."""
    username = "readtestuser"
    subprocess.run(f"vault write auth/userpass/users/{username} password=password123", shell=True, env=env)
    
    cmd = f"vault read auth/userpass/users/{username}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    
    assert result.returncode == 0
    assert "token_policies" in result.stdout or "token_ttl" in result.stdout

def test_delete_user():
    """Test deleting a user from the userpass backend."""
    username = f"deluser_{uuid.uuid4().hex[:8]}"
    subprocess.run(f"vault write auth/userpass/users/{username} password=password123", shell=True, env=env)
    
    cmd = f"vault delete auth/userpass/users/{username}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    
    assert result.returncode == 0
    assert "Success!" in result.stdout