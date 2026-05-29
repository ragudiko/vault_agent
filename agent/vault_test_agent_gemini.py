import os
import re
import subprocess
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")

# 1. Initialize Gemini Client
# Ensure GEMINI_API_KEY is available in your environment variables
client = genai.Client()
MODEL_ID = 'gemini-2.5-flash'

def get_vault_env():
    """Validates and retrieves the running local Vault configuration context."""
    addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    token = os.getenv("VAULT_TOKEN")
    if not token:
        print("[!] ERROR: Please set your 'VAULT_TOKEN' environment variable to connect to the dev server.")
        sys.exit(1)
    return addr, token

def generate_test_suite_code(user_prompt: str) -> str:
    """Uses Gemini to generate a complete executable pytest script matching requested features."""
    vault_addr, vault_token = get_vault_env()
    
    system_instruction = """
    You are an expert QA Automation Engineer specialized in HashiCorp Vault. 
    Your objective is to generate an executable Python automation testing script using 'pytest'.
    
    Constraints:
    1. Use the standard operating system terminal command execution pipeline via 'subprocess.run(shell=True, capture_output=True, text=True)' to execute the Vault CLI directly.
    2. Read Vault server settings from the provided variables context dynamically inserted in the prompt setup.
    3. Output raw, valid executable Python code containing the necessary assertions. 
    4. Enclose your Python script cleanly within standard markdown block specifiers: ```python ... ```
    """

    prompt = f"""
    The user wants to validate this Vault operational requirement/feature target: 
    "{user_prompt}"

    Generate a complete, production-grade pytest script. 
    Make sure to handle clean environment variable setup for each subprocess command using:
    env = {{**os.environ, "VAULT_ADDR": "{vault_addr}", "VAULT_TOKEN": "{vault_token}"}}

    Include rigorous text assertions validating strings matching typical Vault CLI returns.
    """

    print("🤖 Agent is analyzing Vault features and designing test infrastructure...")
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1 # Low variance ensures programmatic consistency
        )
    )
    
    # Extract code from the markdown fences
    if response and response.text:
        code_match = re.search(r"```python(.*?)```", response.text, re.DOTALL)
        if not code_match:
            raise ValueError("The Agent failed to return a cleanly formatted python test suite code block.")
        
        return code_match.group(1).strip()
    return "test generation failed"

def execute_test_suite(test_code: str, file_name: str = "vault_test_agent_gemini.py"):
    """Writes the generated code layer out to disk and runs it via pytest to compile HTML reporting telemetry."""
    print(f"💾 Writing code logic layer out onto execution matrix space '{file_name}'...")
    with open(file_name, "w") as f:
        f.write(test_code)
        
    print("🚀 Initiating Test Matrix Execution and HTML UI report assembly...")
    # Executing 'pytest' command linking the standard automated html dashboard plugin
    report_name = "vault_execution_report.html"
    cmd = f"pytest {file_name} --html={report_name} --self-contained-html"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print("\n=== CLI Test Execution Metrics Output Summary ===")
    print(result.stdout)
    
    if os.path.exists(report_name):
        print(f"✨ [SUCCESS] Your interactive AI testing dashboard report has been compiled successfully: {os.path.abspath(report_name)}")
    else:
        print("[!] Warning: Could not generate HTML dashboard file asset.")

if __name__ == "__main__":
    # Example Prompt focusing on KVv2 engine feature rules tested previously
    user_intent = "Verify that soft deleting a secret path via KVv2 engine can be successfully reversed with the undelete flag"
    
    try:
        generated_code = generate_test_suite_code(user_intent)
        execute_test_suite(generated_code)
    except Exception as e:
        print(f"\n[!] Execution Chain Broken: {e}")