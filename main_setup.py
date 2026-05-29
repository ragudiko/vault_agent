#!/usr/bin/env python3
"""
main_setup.py
Integrated Vault Setup and Test Generation Pipeline

This script:
1. Detects OS and installs Vault (if not already installed)
2. Verifies Vault installation
3. Accepts user input for test feature request
4. Generates test cases using Gemini AI
5. Executes tests and generates HTML report

Only proceeds to test generation after successful Vault installation.
"""

import os
import re
import subprocess
import sys
import platform
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/Users/rajesh/Documents/github_prj/integration-testing/tests/vault_agent/.env")


# ============================================================================
# PART 1: VAULT INSTALLER (from vault_installer.py)
# ============================================================================

class VaultInstaller:
    """Handles OS detection and Vault installation."""
    
    def __init__(self):
        self.os_info = self.detect_os()
        self.vault_installed = False
    
    def detect_os(self):
        """Detect operating system."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine()
        }
    
    def is_vault_installed(self):
        """Check if Vault is already installed."""
        try:
            result = subprocess.run(
                ['vault', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ Vault already installed: {result.stdout.strip()}")
                self.vault_installed = True
                return True
        except FileNotFoundError:
            pass
        return False
    
    def install_macos(self):
        """Install Vault on macOS using Homebrew."""
        print("\n[macOS] Installing Vault via Homebrew...")
        
        try:
            subprocess.run(['brew', '--version'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("✗ Homebrew not found. Install from: https://brew.sh")
            return False
        
        print("  Adding HashiCorp tap...")
        subprocess.run(['brew', 'tap', 'hashicorp/tap'], check=False)
        
        print("  Installing Vault...")
        result = subprocess.run(
            ['brew', 'install', 'hashicorp/tap/vault'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Vault installed successfully")
            return True
        else:
            print(f"✗ Installation failed: {result.stderr}")
            return False
    
    def install_linux(self):
        """Install Vault on Linux."""
        print("\n[Linux] Installing Vault...")
        
        try:
            with open('/etc/os-release', 'r') as f:
                os_release = f.read().lower()
                
            if 'ubuntu' in os_release or 'debian' in os_release:
                return self._install_linux_apt()
            elif 'rhel' in os_release or 'centos' in os_release:
                return self._install_linux_yum()
            else:
                print("✗ Unsupported Linux distribution")
                print("  Install manually: https://developer.hashicorp.com/vault/install")
                return False
        except Exception as e:
            print(f"✗ Error detecting Linux distribution: {e}")
            return False
    
    def _install_linux_apt(self):
        """Install on Ubuntu/Debian using apt."""
        print("  Detected: Ubuntu/Debian")
        print("  Installing via apt...")
        
        commands = [
            "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg",
            'echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list',
            "sudo apt update",
            "sudo apt install -y vault"
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"✗ Command failed: {cmd}")
                return False
        
        print("✓ Vault installed successfully")
        return True
    
    def _install_linux_yum(self):
        """Install on RHEL/CentOS using yum."""
        print("  Detected: RHEL/CentOS")
        print("  Installing via yum...")
        
        commands = [
            "sudo yum install -y yum-utils",
            "sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo",
            "sudo yum -y install vault"
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"✗ Command failed: {cmd}")
                return False
        
        print("✓ Vault installed successfully")
        return True
    
    def install_windows(self):
        """Install Vault on Windows."""
        print("\n[Windows] Installing Vault via Chocolatey...")
        
        result = subprocess.run(
            ['choco', 'install', 'vault', '-y'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Vault installed successfully")
            return True
        else:
            print("✗ Chocolatey not found or installation failed")
            print("  Install manually: https://developer.hashicorp.com/vault/install")
            return False
    
    def install(self):
        """Main installation method."""
        print("\n" + "="*60)
        print("STEP 1: VAULT INSTALLATION")
        print("="*60)
        print(f"Detected OS: {self.os_info['system']} {self.os_info['release']}")
        print(f"Architecture: {self.os_info['machine']}")
        
        # Check if already installed
        if self.is_vault_installed():
            return True
        
        # Install based on OS
        system = self.os_info['system']
        
        if system == 'Darwin':
            success = self.install_macos()
        elif system == 'Linux':
            success = self.install_linux()
        elif system == 'Windows':
            success = self.install_windows()
        else:
            print(f"✗ Unsupported OS: {system}")
            return False
        
        # Verify installation
        if success:
            return self.is_vault_installed()
        return False


# ============================================================================
# PART 2: VAULT TEST AGENT (from vault_doc_agent.py_gemini.py)
# ============================================================================

# Official Validated Feature List
VALID_VAULT_FEATURES = [
    "kv", "database", "pki", "transit", "cubbyhole", "ssh", "totp", "ldap", 
    "aws", "gcp", "azure", "approle", "kubernetes", "userpass", "github", 
    "token", "namespaces", "secrets sync", "replication", "control groups"
]

# Initialize Gemini Client
client = genai.Client()
MODEL_ID = 'gemini-3.1-flash-lite'


def analyze_and_validate_intent(user_prompt: str) -> Optional[str]:
    """
    Analyzes the prompt and extracts the core Vault feature.
    Cross-references it with the official validated list.
    Returns None if validation fails.
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

    if not response.text:
        print("\n❌ Error: The AI model returned an empty response or was blocked by filters.")
        print(f"Raw response structure for debugging: {response}")
        return None
    
    feature = response.text.strip().lower()
    
    # Validation Gate
    if feature not in VALID_VAULT_FEATURES or "unknown" in feature:
        print("\n❌ Error: feature does not exist")
        return None
        
    print(f"✅ Feature Validated Successfully: '{feature.upper()}' matches official documentation.")
    return feature


def generate_test_suite(feature_name: str) -> str:
    """
    Generates 3 production-grade pytest test cases for the validated feature.
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
    
    if response is not None and response.text:
        code_match = re.search(r"```python(.*?)```", response.text, re.DOTALL)
    else:
        code_match = None
        print("Error: The response is empty or None.")
        
    if not code_match:
        raise ValueError("The AI model output did not contain a clean Python code block.")
        
    return code_match.group(1).strip()


def execute_and_report(test_code: str):
    """
    Executes the generated suite using pytest and generates an interactive HTML report.
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


# ============================================================================
# MAIN INTEGRATION PIPELINE
# ============================================================================

def main():
    """
    Main integration pipeline:
    1. Install Vault (if needed)
    2. Verify installation
    3. Get user input for test feature
    4. Generate tests using AI
    5. Execute tests and generate report
    """
    print("\n" + "#"*60)
    print("# VAULT SETUP AND TEST GENERATION PIPELINE")
    print("#"*60)
    
    # STEP 1: Install and verify Vault
    installer = VaultInstaller()
    if not installer.install():
        print("\n❌ PIPELINE TERMINATED: Vault installation failed")
        print("   Please install Vault manually and try again.")
        print("   Reference: https://developer.hashicorp.com/vault/install")
        sys.exit(1)
    
    print("\n✓ Vault installation verified successfully")
    
    # STEP 2: Get user input for test feature
    print("\n" + "="*60)
    print("STEP 2: TEST GENERATION")
    print("="*60)
    
    user_request = input("📋 Enter your Vault feature test request: ").strip()
    
    if not user_request:
        print("❌ Error: Empty request provided")
        sys.exit(1)
    
    print(f"📋 User Prompt Input: '{user_request}'")
    print("--------------------------------------------------")
    
    # STEP 3: Parse and Validate feature
    validated_feature = analyze_and_validate_intent(user_request)
    
    if not validated_feature:
        print("\n❌ PIPELINE TERMINATED: Invalid or unsupported feature")
        print(f"   Supported features: {', '.join(VALID_VAULT_FEATURES)}")
        sys.exit(1)
    
    # STEP 4: Generate test suite
    try:
        generated_pytest_code = generate_test_suite(validated_feature)
    except Exception as e:
        print(f"\n❌ PIPELINE TERMINATED: Test generation failed")
        print(f"   Error: {e}")
        sys.exit(1)
    
    # STEP 5: Execute tests and generate report
    print("\n" + "="*60)
    print("STEP 3: TEST EXECUTION")
    print("="*60)
    
    execute_and_report(generated_pytest_code)
    
    print("\n" + "#"*60)
    print("# PIPELINE COMPLETED SUCCESSFULLY")
    print("#"*60)


if __name__ == "__main__":
    main()

# Made with Bob
