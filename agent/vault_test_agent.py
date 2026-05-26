"""
vault_test_agent.py
Step 2: AI Agent using IBM watsonx.ai to generate and run tests
FIXED: Better feature extraction with improved prompting
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
        
        # Initialize watsonx.ai with system prompt
        self.model = Model(
            # model_id="ibm/granite-13b-chat-v2",
            model_id=os.getenv('MODEL', "ibm/granite-4-h-small"),
            params={
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: 2000,
                GenParams.TEMPERATURE: 0.5,
                GenParams.TOP_P: 1,
                GenParams.TOP_K: 50,
            },
            credentials={
                "url": "https://us-south.ml.cloud.ibm.com",
                "apikey": self.api_key
            },
            project_id=self.project_id
        )
        
        self.vault_features = {
            "kv2": {
                "name": "KV2",
                "full_name": "Key-Value version 2 secrets engine",
                "url": "https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2",
                "keywords": ["kv2", "kv", "key-value", "key value", "secrets engine", "secret store"]
            },
            "transit": {
                "name": "Transit",
                "full_name": "Transit encryption as a service",
                "url": "https://developer.hashicorp.com/vault/docs/secrets/transit",
                "keywords": ["transit", "encryption", "encrypt", "decrypt", "crypto"]
            },
            "pki": {
                "name": "PKI",
                "full_name": "PKI certificates and CA",
                "url": "https://developer.hashicorp.com/vault/docs/secrets/pki",
                "keywords": ["pki", "certificate", "cert", "ca", "x509", "ssl", "tls"]
            }
        }
        
        # System prompt for the agent
        self.system_prompt = """You are a HashiCorp Vault expert assistant.

Available Vault Features:
1. kv2 - Key-Value version 2 secrets engine (keywords: kv, kv2, key-value, secret store)
2. transit - Encryption as a service (keywords: transit, encryption, encrypt, decrypt)
3. pki - PKI certificates and CA (keywords: pki, certificate, cert, ca, ssl, tls)

Your task: Extract the feature name from user requests.
Rules:
- Respond with ONLY the feature name: kv2, transit, or pki
- If unclear, respond with: unknown
- Be case-insensitive
- Look for keywords in the request"""
    
    def generate_response(self, prompt):
        """Generate response from watsonx.ai."""
        try:
            response = self.model.generate_text(prompt=prompt)
            print(f"  ==========Raw response type: {type(response)}")
            print(f"  ==========Raw response: {response}")
            if isinstance(response, str):
                return response
            elif isinstance(response, list) and len(response) > 0:
                return str(response[0])
            elif isinstance(response, dict):
                return response.get('generated_text', str(response))
            return str(response)
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
    
    def extract_feature(self, user_prompt):
        """
        Extract feature name from user prompt using AI.
        FIXED: Better prompting with system context and fallback logic.
        """
        
        # First, try simple keyword matching as fallback
        user_lower = user_prompt.lower()
        for feature_key, feature_info in self.vault_features.items():
            for keyword in feature_info['keywords']:
                if keyword in user_lower:
                    print(f"  Matched keyword '{keyword}' -> {feature_key}")
                    return feature_key
        
        # If no keyword match, use LLM with improved prompt
        full_prompt = f"""{self.system_prompt}

User Request: "{user_prompt}"

Feature name (kv2, transit, pki, or unknown):"""
        
        print(f" ===========extract_feature full_prompt {full_prompt}")
        print(f"  Asking LLM to extract feature...")
        response = self.generate_response(full_prompt)
        
        if response:
            response_clean = str(response).strip().lower()
            
            # Extract feature from response
            for feature in self.vault_features.keys():
                if feature in response_clean:
                    print(f"  LLM identified: {feature}")
                    return feature
            
            # Check if response contains feature keywords
            for feature_key, feature_info in self.vault_features.items():
                for keyword in feature_info['keywords']:
                    if keyword in response_clean:
                        print(f"  LLM response contains '{keyword}' -> {feature_key}")
                        return feature_key
        
        print(f"  Could not identify feature from: {user_prompt}")
        return "unknown"
    
    def generate_test_code(self, feature):
        """Generate test code for the feature."""
        
        feature_info = self.vault_features[feature]
        print(f"==========feature_info:{feature_info}")
        
        test_template = '''import subprocess
import pytest
import os
from dotenv import load_dotenv

load_dotenv("/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")

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
    load_dotenv("/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")
    try:
        run_command("vault status")
    except:
        pytest.skip("Vault not accessible")
    yield
'''
        
        # Improved prompt with system context
        prompt = f"""{self.system_prompt}


Task: Generate pytest test functions for Vault {feature} feature.

Feature: {feature}
Documentation: {feature_info['url']}

Start with this template:
{test_template}

Then generate 4-5 test functions for {feature} operations.
Each test should:
- Use setup_vault fixture
- Call run_command() with vault CLI commands
- Include assertions
- Have descriptive names

Example for kv2:
def test_create_secret(setup_vault):
    result = run_command("vault kv put secret/test key=value")
    assert "created_time" in result or "version" in result

Generate complete test functions for {feature}.
Only generate the test functions, not the template again."""
        
        print(f" ==========prompt {prompt}")
        print(f"  Generating test code for {feature}...")
        code = self.generate_response(prompt)
        print(f" ==========code {code}")
        
        if code:
            code_str = str(code)
            
            # Clean up response
            if "```python" in code_str:
                code_str = code_str.split("```python")[1].split("```")[0]
            elif "```" in code_str:
                parts = code_str.split("```")
                if len(parts) >= 2:
                    code_str = parts[1]
            
            # Remove template if LLM included it
            if "import subprocess" in code_str and "def run_command" in code_str:
                # LLM included template, extract only test functions
                lines = code_str.split('\n')
                test_lines = []
                in_test = False
                for line in lines:
                    if line.startswith('def test_'):
                        in_test = True
                    if in_test:
                        test_lines.append(line)
                code_str = '\n'.join(test_lines)
            
            full_code = test_template + "\n\n" + code_str.strip()
            return full_code
        
        return None
    
    def save_and_run_tests(self, feature, test_code):
        """Save test code and execute it."""
        filename = f"test_vault_{feature}.py"
        
        with open(filename, 'w') as f:
            f.write(test_code)
        print(f"  Test file saved: {filename}")
        
        print(f"  Executing tests...")
        result = subprocess.run(
            ['pytest', filename, '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
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
        
        # Extract feature
        print("\nExtracting feature...")
        feature = self.extract_feature(user_prompt)
        
        if feature == "unknown":
            print(f"\nCould not identify feature from request.")
            print(f"Available features: {list(self.vault_features.keys())}")
            print("\nTry requests like:")
            print("  - 'Generate tests for KV2'")
            print("  - 'Test transit encryption'")
            print("  - 'I want to test PKI certificates'")
            return None
        
        feature_info = self.vault_features[feature]
        print(f"Feature: {feature_info['name']} - {feature_info['full_name']}")
        print(f"Documentation: {feature_info['url']}")
        
        # Generate tests
        print("\nGenerating tests...")
        test_code = self.generate_test_code(feature)
        if not test_code:
            print("Failed to generate tests")
            return None
        
        # Run tests
        print("\nRunning tests...")
        results = self.save_and_run_tests(feature, test_code)
        status = "PASSED" if results['success'] else "FAILED"
        print(f"Status: {status}")
        
        return {
            'feature': feature,
            'results': results,
            'doc_url': feature_info['url']
        }


if __name__ == "__main__":
    agent = VaultTestAgent()
    
    # Test different prompts
    test_prompts = [
        "Generate tests for KV2 secrets engine",
        "Test transit encryption",
        "I want to test PKI certificates",
        "kv2",
        "encryption as a service"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"Testing prompt: {prompt}")
        result = agent.process_request(prompt)
        if result:
            print(f"Success! Feature: {result['feature']}")
        else:
            print("Failed to process")
