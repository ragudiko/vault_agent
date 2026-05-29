import os
import re
import subprocess
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")


# 1. Official Validated Feature List extracted from developer.hashicorp.com/vault
VALID_VAULT_FEATURES = [
    "kv", "database", "pki", "transit", "cubbyhole", "ssh", "totp", "ldap", 
    "aws", "gcp", "azure", "approle", "kubernetes", "userpass", "github", 
    "token", "namespaces", "secrets sync", "replication", "control groups"
]

# 2. Initialize Gemini Client
client = genai.Client()
MODEL_ID = 'gemini-3.1-flash-lite'

def analyze_and_validate_intent(user_prompt: str) -> str:
    """
    Step 1 & 2: Analyzes the prompt and extracts the core Vault feature.
    Cross-references it with the official validated list.
    """
    system_instruction = f"""
    You are a Vault Documentation parsing assistant. Analyze the user's request and output ONLY 
    the exact matching lowercase core feature name from this list: {VALID_VAULT_FEATURES}.
    If the request does not map cleanly to any of these features, respond with exactly: "UNKNOWN".
    Do not include any other text, markdown, or punctuation.
    """
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=f"Extract the target feature name from this request: '{user_prompt}'",
        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.0)
    )

    # --- FIX START: Safeguard against NoneType response.text ---
    if not response.text:
        print("\n❌ Error: The AI model returned an empty response or was blocked by filters.")
        print(f"Raw response structure for debugging: {response}")
        sys.exit(0)
    
    feature = response.text.strip().lower()
    
    # Validation Gate
    if feature not in VALID_VAULT_FEATURES or "unknown" in feature:
        print("\n❌ Error: feature does not exist")
        sys.exit(0) # Terminate execution as requested
        
    print(f"✅ Feature Validated Successfully: '{feature.upper()}' matches official documentation.")
    return feature

def generate_test_suite(feature_name: str) -> str:
    """
    Step 3: Generates 3 production-grade pytest test cases for the validated feature.
    """
    print(f"🤖 Generating 3 robust test cases for '{feature_name}' using Gemini...")
    
    system_instruction = """
    You are an expert QA Automation Engineer. Generate a functional, executable Python test script using `pytest`.
    
    Constraints:
    1. Write exactly 3 test functions (prefixed with test_).
    2. Use `subprocess.run(..., shell=True, capture_output=True, text=True, env=env)` to interact with the Vault CLI.
    3. Ensure you map the environment variables contextually so the CLI commands pass successfully.
    4. Keep assert statement with simple text check like assert "Success!" in result.stdout
    5. Provide valid assertions on result.stdout, result.stderr, or result.returncode.
    6. Wrap your Python script cleanly inside markdown fences: ```python ... ```
    """
    
    prompt = f"""
    Generate an automation test file testing exactly 3 scenarios for the Vault '{feature_name}' feature backend.
    
    Assume the user has initialized a clean environment mapping variable layout like this:
    env = {{**os.environ, "VAULT_ADDR": os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"), "VAULT_TOKEN": os.getenv("VAULT_TOKEN")}}
    
    Ensure all operations handle cleanup steps or unique paths so the tests don't collide.
    """
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
    )
    
    # Extract code from response
    # code_match = re.search(r"```python(.*?)```", response.text, re.DOTALL)
    if response is not None and response.text:
        code_match = re.search(r"```python(.*?)```", response.text, re.DOTALL)
    else:
        code_match=None
        print("Error: The response is empty or None.")
    if not code_match:
        raise ValueError("The AI model output did not contain a clean Python code block.")
        
    return code_match.group(1).strip()

def execute_and_report(test_code: str):
    """
    Step 4: Executes the generated suite using pytest and generates an interactive HTML report.
    """
    test_filename = "test_vault_dynamic_suite.py"
    report_filename = "vault_execution_report.html"
    
    print(f"💾 Writing generated assertions to local file system matrix ({test_filename})...")
    with open(test_filename, "w") as f:
        f.write(test_code)
        
    print(f"🚀 Running pytest suite and compiling layout presentation pipeline to '{report_filename}'...")
    
    # Run pytest with html reporting module enabled
    cmd = f"pytest {test_filename} --html={report_filename} --self-contained-html -s"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print("\n=== Test Execution Live Terminal Output Summary ===")
    print(result.stdout)
    
    if os.path.exists(report_filename):
        print(f"✨ [SUCCESS] Execution complete. HTML report generated here: {os.path.abspath(report_filename)}")
    else:
        print("⚠️ Execution finished, but failed to compile visual HTML asset dashboards.")

if __name__ == "__main__":
    # --- CHANGE THIS PROMPT TO TEST VALIDATION LABELS ---
    # user_request = "I want to test secret path version handling, soft deletes, and restores using kv2"
    # Example invalid prompt to test failure path:
    # user_request = "I want to configure the oracle-legacy-mainframe module engine"
    # user_request = "I want to enable the LDAP auth method, configure it to connect to a directory server, and verify a login mapping"
    user_request = input("📋 Enter your Vault feature test request: ").strip()
    print(f"📋 User Prompt Input: '{user_request}'")
    print("--------------------------------------------------")
    
    # Step 1 & 2: Parse and Validate
    validated_feature = analyze_and_validate_intent(user_request)
    
    # Step 3: Generate
    generated_pytest_code = generate_test_suite(validated_feature)
    
    # Step 4: Execute & Report
    execute_and_report(generated_pytest_code)