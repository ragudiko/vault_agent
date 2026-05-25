from vault_nutan import VaultTestingWorkflow

# vault_setup.py - Predefined steps

def __init__(self):
        self.os_info = {}
        self.vault_installed = False
        self.test_results = []
        self.citations = []

def setup_vault(self):
    """Fixed workflow - no AI needed."""
    VaultTestingWorkflow.step1_detect_os(self)
    VaultTestingWorkflow.step3_install_and_verify(self)
    verify_installation()
    start_dev_server()
    return True
