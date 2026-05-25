# vault_test_agent.py - AI-powered dynamic testing
class VaultTestAgent:
    """
    AI Agent that:
    1. Extracts feature name from user prompt
    2. Searches documentation for that feature
    3. Generates appropriate test cases
    4. Executes tests
    5. Creates report
    """
    
    def __init__(self):
        self.llm = OpenAI()
        self.vault_features = {
            "kv2": "https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2",
            "transit": "https://developer.hashicorp.com/vault/docs/secrets/transit",
            "pki": "https://developer.hashicorp.com/vault/docs/secrets/pki",
            "database": "https://developer.hashicorp.com/vault/docs/secrets/databases",
            "aws": "https://developer.hashicorp.com/vault/docs/secrets/aws",
            "ssh": "https://developer.hashicorp.com/vault/docs/secrets/ssh"
        }
    
    def extract_feature(self, user_prompt):
        """
        AI Agent extracts feature name from natural language.
        
        Examples:
        - "Generate tests for KV2 secrets engine" → "kv2"
        - "Test the transit encryption feature" → "transit"
        - "I want to test PKI certificates" → "pki"
        """
        
        extraction_prompt = f"""
        Extract the Vault feature name from this user request:
        
        User: "{user_prompt}"
        
        Available features:
        - kv2: Key-Value version 2 secrets engine
        - transit: Encryption as a service
        - pki: PKI certificates and CA
        - database: Dynamic database credentials
        - aws: AWS dynamic credentials
        - ssh: SSH certificate authority
        
        Respond with ONLY the feature name (e.g., "kv2", "transit", etc.)
        If unclear, respond with "unknown"
        """
        
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        
        feature = response.choices[0].message.content.strip().lower()
        return feature
    
    def fetch_feature_documentation(self, feature):
        """
        AI Agent searches and retrieves documentation for the feature.
        """
        
        if feature not in self.vault_features:
            return None
        
        doc_url = self.vault_features[feature]
        
        # In real implementation, would fetch actual documentation
        # For now, simulate with prompt
        doc_prompt = f"""
        Based on HashiCorp Vault documentation for {feature} feature:
        URL: {doc_url}
        
        Provide:
        1. Key operations/commands
        2. Common use cases
        3. Important parameters
        4. Expected behaviors
        
        Format as structured data for test generation.
        """
        
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": doc_prompt}]
        )
        
        return {
            "feature": feature,
            "url": doc_url,
            "documentation": response.choices[0].message.content
        }
    
    def generate_test_cases(self, feature, documentation):
        """
        AI Agent generates test cases based on documentation.
        """
        
        generation_prompt = f"""
        Generate comprehensive test cases for Vault {feature} feature.
        
        Documentation:
        {documentation}
        
        Generate test cases in this format:
        
        ```python
        import subprocess
        import pytest
        
        class Test{feature.upper()}:
            def test_case_name(self):
                # Test implementation
                pass
        ```
        
        Include:
        1. Setup/teardown
        2. Positive test cases
        3. Negative test cases
        4. Edge cases
        5. Assertions
        
        Generate complete, runnable pytest code.
        """
        
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": generation_prompt}]
        )
        
        test_code = response.choices[0].message.content
        
        # Extract code from markdown if present
        if "```python" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0].strip()
        
        return test_code
    
    def save_test_file(self, feature, test_code):
        """Save generated tests to file."""
        filename = f"test_vault_{feature}.py"
        with open(filename, 'w') as f:
            f.write(test_code)
        return filename
    
    def execute_tests(self, test_file):
        """Execute the generated tests."""
        result = subprocess.run(
            ['pytest', test_file, '-v', '--tb=short'],
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
        report_prompt = f"""
        Generate a comprehensive test report for Vault {feature} feature.
        
        Test Results:
        {test_results}
        
        Include:
        1. Executive summary
        2. Test coverage
        3. Pass/fail statistics
        4. Detailed results
        5. Recommendations
        
        Format as HTML.
        """
        
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": report_prompt}]
        )
        
        return response.choices[0].message.content
    
    def process_user_request(self, user_prompt):
        """
        Main AI Agent workflow - processes any feature request.
        """
        
        print("\n" + "="*60)
        print("AI VAULT TEST AGENT")
        print("="*60)
        print(f"\nUser Request: {user_prompt}")
        
        # Step 1: Extract feature from natural language
        print("\n[1/5] Extracting feature from request...")
        feature = self.extract_feature(user_prompt)
        print(f"✓ Detected feature: {feature}")
        
        if feature == "unknown" or feature not in self.vault_features:
            print(f"✗ Unknown feature. Available: {list(self.vault_features.keys())}")
            return None
        
        # Step 2: Fetch documentation
        print(f"\n[2/5] Fetching {feature} documentation...")
        docs = self.fetch_feature_documentation(feature)
        print(f"✓ Documentation retrieved from: {docs['url']}")
        
        # Step 3: Generate test cases
        print(f"\n[3/5] Generating test cases for {feature}...")
        test_code = self.generate_test_cases(feature, docs['documentation'])
        test_file = self.save_test_file(feature, test_code)
        print(f"✓ Test cases generated: {test_file}")
        
        # Step 4: Execute tests
        print(f"\n[4/5] Executing tests...")
        results = self.execute_tests(test_file)
        status = "✓ PASSED" if results['success'] else "✗ FAILED"
        print(f"{status}")
        
        # Step 5: Generate report
        print(f"\n[5/5] Generating report...")
        report = self.generate_report(feature, results)
        report_file = f"vault_{feature}_test_report.html"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"✓ Report generated: {report_file}")
        
        print("\n" + "="*60)
        print("AGENT COMPLETED SUCCESSFULLY")
        print("="*60)
        
        return {
            "feature": feature,
            "test_file": test_file,
            "report_file": report_file,
            "results": results
        }


# Usage Examples
if __name__ == "__main__":
    agent = VaultTestAgent()
    
    # Example 1: User asks for KV2 tests
    agent.process_user_request("Generate test cases for KV2 secrets engine")
    
    # Example 2: User asks for Transit tests
    agent.process_user_request("I want to test the transit encryption feature")
    
    # Example 3: User asks for PKI tests
    agent.process_user_request("Test PKI certificate generation")
    
    # Example 4: User asks for Database tests
    agent.process_user_request("Generate tests for database dynamic credentials")
