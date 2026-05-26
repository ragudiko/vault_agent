# """
# main.py
# Step 4: Main orchestrator integrating all components
# Accepts user input for feature selection
# """

# from typing import Any


# from tests.vault_agent.vault_test_agent import VaultTestAgent


# import sys
# from vault_installer import VaultInstaller
# from vault_test_agent import VaultTestAgent
# from html_report_generator import HTMLReportGenerator


# def get_user_input():
#     """Get user input for which feature to test."""
#     print("\n" + "="*60)
#     print("VAULT FEATURE TESTING")
#     print("="*60)
#     print("\nAvailable features:")
#     print("  1. KV2 - Key-Value version 2 secrets engine")
#     print("  2. Transit - Encryption as a service")
#     print("  3. PKI - PKI certificates and CA")
#     print("\nYou can also type a custom request like:")
#     print("  - 'Generate tests for KV2'")
#     print("  - 'Test the transit encryption feature'")
#     print("  - 'I want to test PKI certificates'")
#     print("="*60)
    
#     user_input = input("\nEnter your request (or feature number): ").strip()
    
#     if not user_input:
#         print("No input provided. Using default: KV2")
#         return "Generate tests for KV2 secrets engine"
    
#     # Handle numeric input
#     if user_input == "1":
#         return "Generate tests for KV2 secrets engine"
#     elif user_input == "2":
#         return "Generate tests for Transit encryption"
#     elif user_input == "3":
#         return "Generate tests for PKI certificates"
    
#     # Return user's natural language input
#     return user_input


# def main():
#     """Main workflow orchestrator with dynamic user input."""
#     print("\n" + "#"*60)
#     print("# VAULT TESTING WORKFLOW")
#     print("#"*60)
    
#     # Step 1: Install Vault
#     print("\n[STEP 1/4] Installing Vault...")
#     installer = VaultInstaller()
#     if not installer.install():
#         print("\n✗ Vault installation failed")
#         sys.exit(1)
    
#     # Step 2: Get user input
#     print("\n[STEP 2/4] Getting user input...")
#     user_prompt = get_user_input()
#     print(f"\nUser request: {user_prompt}")
    
#     # Step 3: Generate and run tests
#     print("\n[STEP 3/4] Generating and running tests...")
#     try:
#         agent: VaultTestAgent = VaultTestAgent()
#         result: dict[str, Any] | None = agent.process_request(user_prompt)
        
#         if not result:
#             print("\n✗ Test generation failed")
#             print("The agent could not identify the feature from your request.")
#             print("Please try again with: kv2, transit, or pki")
#             sys.exit(1)
    
#     except Exception as e:
#         print(f"\n✗ Error: {e}")
#         sys.exit(1)
    
#     # Step 4: Generate HTML report
#     print("\n[STEP 4/4] Generating HTML report...")
#     html = HTMLReportGenerator.generate(
#         feature=result['feature'],
#         results=result['results'],
#         doc_url=result['doc_url']
#     )
    
#     report_file = 'vault_agent_test_report.html'
#     with open(report_file, 'w') as f:
#         f.write(html)
    
#     print(f"✓ Report generated: {report_file}")
    
#     # Summary
#     print("\n" + "#"*60)
#     print("# WORKFLOW COMPLETED")
#     print("#"*60)
#     print(f"User Request: {user_prompt}")
#     print(f"Detected Feature: {result['feature']}")
#     print(f"Test File: {result['results']['test_file']}")
#     print(f"Report: {report_file}")
#     print(f"Status: {'✓ PASSED' if result['results']['success'] else '✗ FAILED'}")
#     print("#"*60)


# if __name__ == "__main__":
#     main()

"""
main.py - With command-line arguments
"""

from typing import Any


from argparse import ArgumentParser, Namespace


import sys
import argparse
from vault_installer import VaultInstaller
from vault_test_agent import VaultTestAgent
from html_report_generator import HTMLReportGenerator


def parse_arguments() -> tuple[str | Any, Any]:
    """Parse command-line arguments."""
    parser: ArgumentParser = argparse.ArgumentParser(
        description='Vault Testing Workflow with AI Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Generate tests for KV2"
  python main.py "Test transit encryption"
  python main.py "I want to test PKI certificates"
  python main.py --feature kv2
  python main.py --feature transit
        """
    )
    
    parser.add_argument(
        'prompt',
        nargs='?',
        default=None,
        help='Natural language prompt for feature testing'
    )
    
    parser.add_argument(
        '--feature',
        choices=['kv2', 'transit', 'pki'],
        help='Directly specify feature to test'
    )
    
    parser.add_argument(
        '--skip-install',
        action='store_true',
        help='Skip Vault installation step'
    )
    
    args: Namespace = parser.parse_args()
    
    # Determine user prompt
    if args.feature:
        user_prompt = f"Generate tests for {args.feature}"
    elif args.prompt:
        user_prompt = args.prompt
    else:
        # Interactive mode
        print("\nNo prompt provided. Available features:")
        print("  - kv2: Key-Value version 2")
        print("  - transit: Encryption as a service")
        print("  - pki: PKI certificates")
        
        user_input = input("\nEnter feature or custom prompt: ").strip()
        if not user_input:
            print("No input. Using default: kv2")
            user_prompt = "Generate tests for KV2"
        else:
            user_prompt = user_input
    
    return user_prompt, args.skip_install


def main():
    """Main workflow orchestrator."""
    print("\n" + "#"*60)
    print("# VAULT TESTING WORKFLOW")
    print("#"*60)
    
    # Parse arguments
    user_prompt, skip_install = parse_arguments()
    
    # Step 1: Install Vault (optional)
    if not skip_install:
        print("\n[STEP 1/4] Installing Vault...")
        installer = VaultInstaller()
        if not installer.install():
            print("\n✗ Vault installation failed")
            sys.exit(1)
    else:
        print("\n[STEP 1/4] Skipping Vault installation...")
    
    # Step 2: Show user prompt
    print("\n[STEP 2/4] Processing user request...")
    print(f"User prompt: {user_prompt}")
    
    # Step 3: Generate and run tests
    print("\n[STEP 3/4] Generating and running tests...")
    try:
        agent = VaultTestAgent()
        result = agent.process_request(user_prompt)
        
        if not result:
            print("\n✗ Test generation failed")
            print("Could not identify feature. Try: kv2, transit, or pki")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    
    # Step 4: Generate HTML report
    print("\n[STEP 4/4] Generating HTML report...")
    html = HTMLReportGenerator.generate(
        feature=result['feature'],
        results=result['results'],
        doc_url=result['doc_url']
    )
    
    report_file = 'vault_agent_test_report.html'
    with open(report_file, 'w') as f:
        f.write(html)
    
    print(f"✓ Report: {report_file}")
    
    # Summary
    print("\n" + "#"*60)
    print("# WORKFLOW COMPLETED")
    print("#"*60)
    print(f"User Request: {user_prompt}")
    print(f"Detected Feature: {result['feature']}")
    print(f"Test File: {result['results']['test_file']}")
    print(f"Report: {report_file}")
    print(f"Status: {'✓ PASSED' if result['results']['success'] else '✗ FAILED'}")
    print("#"*60)


if __name__ == "__main__":
    main()
