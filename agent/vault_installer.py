"""
vault_installer.py
Step 1: Detect OS and install Vault based on HashiCorp documentation
Reference: https://developer.hashicorp.com/vault/install
"""

import platform
import subprocess
import sys


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
        """
        Install Vault on macOS using Homebrew.
        Reference: https://developer.hashicorp.com/vault/install#homebrew
        """
        print("\n[macOS] Installing Vault via Homebrew...")
        
        # Check if Homebrew is installed
        try:
            subprocess.run(['brew', '--version'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("✗ Homebrew not found. Install from: https://brew.sh")
            return False
        
        # Add HashiCorp tap
        print("  Adding HashiCorp tap...")
        subprocess.run(['brew', 'tap', 'hashicorp/tap'], check=False)
        
        # Install Vault
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
        """
        Install Vault on Linux.
        Reference: https://developer.hashicorp.com/vault/install#linux
        """
        print("\n[Linux] Installing Vault...")
        
        # Detect Linux distribution
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
        """
        Install Vault on Windows.
        Reference: https://developer.hashicorp.com/vault/install#windows
        """
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
        print("VAULT INSTALLER")
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


if __name__ == "__main__":
    installer = VaultInstaller()
    if installer.install():
        print("\n✓ Vault installation completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Vault installation failed")
        sys.exit(1)
