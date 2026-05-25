# vault_test_agent_ibm.py - FULLY FIXED VERSION
from pyexpat import model
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import subprocess
import os
from dotenv import load_dotenv

class VaultTestAgentIBM:
    """AI Agent using IBM watsonx.ai - FULLY FIXED VERSION"""
    
    def __init__(self, api_key=None, project_id=None):
        """Initialize with IBM watsonx.ai credentials."""
        load_dotenv()
        
        self.api_key = api_key or os.getenv('IBM_CLOUD_API_KEY')
        self.project_id = project_id or os.getenv('WATSONX_PROJECT_ID')
        
        if not self.api_key:
            raise ValueError("IBM_CLOUD_API_KEY not set")
        if not self.project_id:
            raise ValueError("WATSONX_PROJECT_ID not set")
        
        self.credentials = {
            "url": "https://us-south.ml.cloud.ibm.com",
            "apikey": self.api_key
        }
        
        self.model_params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 2000,
            GenParams.MIN_NEW_TOKENS: 1,
            GenParams.TEMPERATURE: 0.7,
            GenParams.TOP_K: 50,
            GenParams.TOP_P: 1
        }
        
        try:
            self.model = Model(
                # model_id="ibm/granite-13b-chat-v2",
                model_id="ibm/granite-4-h-small",
                params=self.model_params,
                credentials=self.credentials,
                project_id=self.project_id
            )
            print("✓ IBM watsonx.ai model initialized successfully")
        except Exception as e:
            raise ValueError(f"Failed to initialize watsonx.ai model: {e}")
        
        self.vault_features = {
            "kv2": "https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2",
            "transit": "https://developer.hashicorp.com/vault/docs/secrets/transit",
            "pki": "https://developer.hashicorp.com/vault/docs/secrets/pki",
            "database": "https://developer.hashicorp.com/vault/docs/secrets/databases",
            "aws": "https://developer.hashicorp.com/vault/docs/secrets/aws",
            "ssh": "https://developer.hashicorp.com/vault/docs/secrets/ssh"
        }
    
    def generate_response(self, prompt):
        """Generate response using IBM watsonx.ai with proper error handling."""
        try:
            response = self.model.generate_text(prompt=prompt)
            
            # Handle different response types
            if isinstance(response, str):
                return response
            elif isinstance(response, list):
                if len(response) > 0:
                    if isinstance(response[0], str):
                        return response[0]
                    elif isinstance(response[0], dict):
                        return response[0].get('generated_text', 
                               response[0].get('results', str(response[0])))
                return ""
            elif isinstance(response, dict):
                return response.get('generated_text', 
                       response.get('results', str(response)))
            else:
                return str(response)
                
        except Exception as e:
            print(f"✗ Error generating response: {e}")
            return None
    
    def extract_feature(self, user_prompt):
        """Extract Vault feature from user prompt."""
        extraction_prompt = f"""Extract the Vault feature name from this user request.

User request: "{user_prompt}"

Available Vault features:
- kv2: Key-Value version 2 secrets engine
- transit: Encryption as a service
- pki: PKI certificates and CA
- database: Dynamic database credentials
- aws: AWS dynamic credentials
- ssh: SSH certificate authority

Respond with ONLY the feature name (kv2, transit, pki, database, aws, or ssh).
If the feature is not clear, respond with "unknown".

Feature name:"""
        
        response = self.generate_response(extraction_prompt)
        
        if response:
            response_str = str(response).strip().lower()
            for known_feature in self.vault_features.keys():
                if known_feature in response_str:
                    return known_feature
        
        return "unknown"
    
    def fetch_feature_documentation(self, feature):
        """Get documentation summary for the feature."""
        if feature not in self.vault_features:
            print(f"✗ Feature '{feature}' not found")
            return None
        
        doc_url = self.vault_features[feature]
        
        doc_prompt = f"""Based on HashiCorp Vault {feature} feature documentation:

Provide:
1. Main purpose
2. Key CLI commands
3. Common operations

Keep it concise and focused on testing."""
        
        try:
            documentation = self.generate_response(doc_prompt)
            
            if documentation is None or str(documentation).strip() == "":
                print(f"✗ Failed to generate documentation")
                return None
            
            return {
                "feature": feature,
                "url": doc_url,
                "documentation": str(documentation)
            }
        
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def generate_test_cases(self, feature, documentation):
        """Generate test cases."""
        generation_prompt = f"""Generate pytest test cases for Vault {feature}.

Documentation: {documentation[:500]}

Generate simple Python pytest code with:
- 3-4 basic test functions
- Use subprocess for vault commands
- Include assertions

Code only, no explanations."""
        
        test_code = self.generate_response(generation_prompt)
        
        if test_code:
            test_code = str(test_code)
            if "```python" in test_code:
                test_code = test_code.split("```python")[1].split("```")[0]
            test_code = test_code.strip()
        
        return test_code
    
    def save_test_file(self, feature, test_code):
        """Save generated tests to file."""
        filename = f"test_vault_{feature}.py"
        with open(filename, 'w') as f:
            f.write(test_code)
        print(f"✓ Test file saved: {filename}")
        return filename
    
    def execute_tests(self, test_file):
        """Execute the generated tests."""
        print(f"Executing tests from {test_file}...")
        result = subprocess.run(
            ['pytest', test_file, '-v'],
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    
    def generate_report(self, feature, test_results):
        """Generate test report."""
        report_prompt = f"""Generate HTML test report for Vault {feature}.

Results: {test_results['output'][:300]}

Simple HTML with summary and results table."""
        
        report_html = self.generate_response(report_prompt)
        return str(report_html) if report_html else "<html><body>Report generation failed</body></html>"
    
    def process_user_request(self, user_prompt):
        """Main AI Agent workflow - FULLY FIXED."""
        print("\n" + "="*70)
        print("IBM WATSONX.AI VAULT TEST AGENT")
        print("="*70)
        print(f"\nUser Request: {user_prompt}")
        
        # Step 1
        print("\n[1/5] Extracting feature...")
        feature = self.extract_feature(user_prompt)
        print(f"✓ Detected: {feature}")
        
        if feature == "unknown" or feature not in self.vault_features:
            print(f"✗ Unknown feature. Available: {list(self.vault_features.keys())}")
            return None
        
        # Step 2 - WITH NULL CHECK
        print(f"\n[2/5] Fetching documentation...")
        docs = self.fetch_feature_documentation(feature)
        if docs is None:  # FIX: Check for None
            print(f"✗ Failed to fetch documentation")
            return None
        print(f"✓ Retrieved from: {docs['url']}")
        
        # Step 3 - WITH NULL CHECK
        print(f"\n[3/5] Generating tests...")
        test_code = self.generate_test_cases(feature, docs['documentation'])
        if not test_code:  # FIX: Check for None/empty
            print("✗ Failed to generate tests")
            return None
        test_file = self.save_test_file(feature, test_code)
        
        # Step 4 - WITH NULL CHECK
        print(f"\n[4/5] Executing tests...")
        results = self.execute_tests(test_file)
        if results is None:  # FIX: Check for None
            print("✗ Failed to execute")
            return None
        status = "✓ PASSED" if results['success'] else "✗ FAILED"
        print(f"{status}")
        
        # Step 5 - WITH NULL CHECK
        print(f"\n[5/5] Generating report...")
        report = self.generate_report(feature, results)
        if not report:  # FIX: Check for None/empty
            print("✗ Report generation failed")
            report = "<html><body>Failed</body></html>"
        
        report_file = f"vault_{feature}_test_report.html"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"✓ Report: {report_file}")
        
        print("\n" + "="*70)
        print("COMPLETED")
        print("="*70)
        
        return {
            "feature": feature,
            "test_file": test_file,
            "report_file": report_file,
            "results": results
        }


if __name__ == "__main__":
    try:
        agent = VaultTestAgentIBM()
        result = agent.process_user_request("Generate test cases for KV2")
        
        if result:
            print(f"\n✓ Success! Files: {result['test_file']}, {result['report_file']}")
        else:
            print("\n✗ Failed")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
