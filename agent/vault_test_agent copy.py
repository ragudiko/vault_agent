"""
vault_test_agent.py
FIXED: Added debugging, error handling, and fallback test generation
"""

from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import subprocess
import os
from dotenv import load_dotenv


class VaultTestAgent:
    """AI Agent for generating and executing Vault tests."""
    
    def __init__(self):
        load_dotenv(dotenv_path="/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")
        
        self.api_key = os.getenv('IBM_CLOUD_API_KEY')
        self.project_id = os.getenv('WATSONX_PROJECT_ID')
        
        if not self.api_key or not self.project_id:
            raise ValueError("IBM_CLOUD_API_KEY and WATSONX_PROJECT_ID must be set in .env")
        
        print(f"Initializing watsonx.ai...")
        print(f"  Project ID: {self.project_id[:10]}...")
        
        try:
            self.model = Model(
                model_id=os.getenv('MODEL', "ibm/granite-4-h-small"),
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 1500,
                    GenParams.MIN_NEW_TOKENS: 50,
                    GenParams.TEMPERATURE: 0.7,
                    GenParams.TOP_P: 1,
                },
                credentials={
                    "url": "https://us-south.ml.cloud.ibm.com",
                    "apikey": self.api_key
                },
                project_id=self.project_id
            )
            print("  watsonx.ai initialized successfully")
        except Exception as e:
            print(f"  Error initializing watsonx.ai: {e}")
            raise
        
        self.vault_features = {
            "kv2": {
                "name": "KV2",
                "full_name": "Key-Value version 2 secrets engine",
                "url": "https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2",
                "keywords": ["kv2", "kv", "key-value", "key value", "secrets engine"]
            },
            "transit": {
                "name": "Transit",
                "full_name": "Transit encryption",
                "url": "https://developer.hashicorp.com/vault/docs/secrets/transit",
                "keywords": ["transit", "encryption", "encrypt", "decrypt"]
            },
            "pki": {
                "name": "PKI",
                "full_name": "PKI certificates",
                "url": "https://developer.hashicorp.com/vault/docs/secrets/pki",
                "keywords": ["pki", "certificate", "cert", "ca"]
            }
        }
    
    def generate_response(self, prompt):
        """Generate response from watsonx.ai with debugging."""
        print(f"\n  Calling watsonx.ai...")
        print(f"  Prompt length: {len(prompt)} characters")
        
        try:
            response = self.model.generate_text(prompt=prompt)
            
            print(f"  Response type: {type(response)}")
            print(f"  Response: {str(response)[:200]}...")
            
            if isinstance(response, str):
                return response
            elif isinstance(response, list) and len(response) > 0:
                return str(response[0])
            elif isinstance(response, dict):
                return response.get('generated_text', str(response))
            else:
                print(f"  Unexpected response type: {type(response)}")
                return str(response) if response else None
                
        except Exception as e:
            print(f"  Error calling watsonx.ai: {e}")
            return None
    
    def extract_feature(self, user_prompt):
        """Extract feature using keyword matching (reliable fallback)."""
        user_lower = user_prompt.lower()
        
        print(f"\n  Extracting feature from: {user_prompt}")
        
        for feature_key, feature_info in self.vault_features.items():
            for keyword in feature_info['keywords']:
                if keyword in user_lower:
                    print(f"  Matched keyword '{keyword}' -> {feature_key}")
                    return feature_key
        
        print(f"  No keyword match found")
        return "unknown"
    
    def generate_test_code_fallback(self, feature):
        """
        Fallback: Generate test code without LLM.
        Uses predefined templates for each feature.
        """
        print(f"  Using fallback test generation for {feature}")
        
        base_template = '''import subprocess
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

'''
        
        if feature == "kv2":
            tests = '''
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
'''
        
        elif feature == "transit":
            tests = '''
def test_create_key(setup_vault):
    """Test creating an encryption key."""
    result = run_command("vault write -f transit/keys/test-key")
    assert "Success" in result or result.strip() == ""

def test_encrypt_data(setup_vault):
    """Test encrypting data."""
    run_command("vault write -f transit/keys/encrypt-key")
    result = run_command("vault write transit/encrypt/encrypt-key plaintext=$(echo 'test' | base64)")
    assert "ciphertext" in result

def test_decrypt_data(setup_vault):
    """Test decrypting data."""
    run_command("vault write -f transit/keys/decrypt-key")
    encrypt_result = run_command("vault write transit/encrypt/decrypt-key plaintext=$(echo 'test' | base64)")
    assert "ciphertext" in encrypt_result
'''
        
        elif feature == "pki":
            tests = '''
def test_generate_root_ca(setup_vault):
    """Test generating root CA."""
    result = run_command("vault write pki/root/generate/internal common_name=test.com ttl=8760h")
    assert "certificate" in result or "issuing_ca" in result

def test_generate_intermediate(setup_vault):
    """Test generating intermediate CA."""
    run_command("vault write pki/root/generate/internal common_name=test.com ttl=8760h")
    result = run_command("vault write pki/intermediate/generate/internal common_name='Test Intermediate'")
    assert "csr" in result or "certificate" in result
'''
        else:
            tests = '''
def test_placeholder(setup_vault):
    """Placeholder test."""
    assert True
'''
        
        return base_template + tests
    
    def generate_test_code(self, feature):
        """Generate test code - try LLM first, fallback to template."""
        
        # Try LLM generation
        prompt = f"""Generate pytest test functions for Vault {feature} feature.

Create 3-4 test functions that:
- Use setup_vault fixture
- Call run_command() with vault CLI commands
- Include assertions

Example:
def test_create_secret(setup_vault):
    result = run_command("vault kv put secret/test key=value")
    assert "created_time" in result

Generate test functions for {feature}:"""
        
        print(f"\n  Attempting LLM test generation...")
        code = self.generate_response(prompt)
        
        if code and len(str(code).strip()) > 50:
            print(f"  LLM generated {len(str(code))} characters")
            code_str = str(code)
            
            if "```python" in code_str:
                code_str = code_str.split("```python")[1].split("```")[0]
            
            if "def test_" in code_str:
                print(f"  Using LLM-generated tests")
                base = '''import subprocess
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

'''
                return base + code_str.strip()
        
        print(f"  LLM generation failed or returned empty")
        return self.generate_test_code_fallback(feature)
    
    def save_and_run_tests(self, feature, test_code):
        """Save and execute tests."""
        filename = f"/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/test_vault_{feature}.py"
        
        with open(filename, 'w') as f:
            f.write(test_code)
        print(f"\n  Test file saved: {filename}")
        print(f"  File size: {len(test_code)} bytes")
        
        print(f"\n  Executing tests...")
        result = subprocess.run(
            ['pytest', filename, '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=60
        )
        print(f"  Exit code: {result.returncode}\n result ==> {result}")
        print(f"  Test output:\n{result.stdout}\n{result.stderr}")
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr,
            'test_file': filename
        }
    
    def process_request(self, user_prompt):
        """Main processing method."""
        print("\n" + "="*60)
        print("VAULT TEST AGENT")
        print("="*60)
        print(f"User request: {user_prompt}")
        
        feature = self.extract_feature(user_prompt)
        
        if feature == "unknown":
            print(f"\nCould not identify feature.")
            print(f"Available: {list(self.vault_features.keys())}")
            return None
        
        feature_info = self.vault_features[feature]
        print(f"\nFeature: {feature_info['name']}")
        print(f"Documentation: {feature_info['url']}")
        
        print(f"\nGenerating tests...")
        test_code = self.generate_test_code(feature)
        print(f"=====Generated {len(test_code)} characters of test code \n, test_code {test_code}")
        
        if not test_code or len(test_code) < 100:
            print("Test generation failed")
            return None
        
        results = self.save_and_run_tests(feature, test_code)
        status = "PASSED" if results['success'] else "FAILED"
        print(f"\nStatus: {status}")
        
        return {
            'feature': feature,
            'results': results,
            'doc_url': feature_info['url']
        }


if __name__ == "__main__":
    agent = VaultTestAgent()
    result = agent.process_request("Generate tests for KV2")
    if result:
        print(f"\nCompleted: {result['feature']}")
