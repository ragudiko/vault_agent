# Vault Setup and Test Generation Pipeline - Flow Diagram

## Overview
This document contains editable flow diagrams for the `main_setup.py` pipeline.

---

## 1. Sequence Diagrams (Separated by Step)

### 1.1 STEP 1: Vault Installation Sequence

```mermaid
sequenceDiagram
    participant User
    participant MainSetup as main_setup.py
    participant Installer as VaultInstaller
    participant System as OS/Package Manager

    User->>MainSetup: Run python main_setup.py
    activate MainSetup
    
    Note over MainSetup: STEP 1: VAULT INSTALLATION
    
    MainSetup->>Installer: Create VaultInstaller()
    activate Installer
    
    Installer->>System: Detect OS
    Note right of System: platform.system()<br/>platform.release()
    System-->>Installer: OS Info<br/>(Darwin/Linux/Windows)
    
    Installer->>System: Check if Vault installed
    Note right of System: vault --version
    
    alt Vault Already Installed
        System-->>Installer: ✓ Vault v1.15.0
        Installer-->>MainSetup: ✓ Installation verified
        deactivate Installer
        Note over MainSetup: Proceed to Step 2
        deactivate MainSetup
    else Vault Not Installed
        Installer->>System: Install Vault
        
        alt macOS
            Note right of System: brew tap hashicorp/tap<br/>brew install vault
        else Linux (Ubuntu/Debian)
            Note right of System: apt update<br/>apt install vault
        else Linux (RHEL/CentOS)
            Note right of System: yum install vault
        else Windows
            Note right of System: choco install vault
        end
        
        System-->>Installer: Installation complete
        
        Installer->>System: Verify installation
        Note right of System: vault --version
        
        alt Verification Success
            System-->>Installer: ✓ Vault v1.15.0
            Installer-->>MainSetup: ✓ Installation verified
            deactivate Installer
            Note over MainSetup: Proceed to Step 2
            deactivate MainSetup
        else Verification Failed
            System-->>Installer: ❌ Command not found
            Installer-->>MainSetup: ❌ Installation failed
            deactivate Installer
            MainSetup->>User: ❌ PIPELINE TERMINATED<br/>Exit code 1
            deactivate MainSetup
        end
    end
```

### 1.2 STEP 2: Test Generation Sequence

```mermaid
sequenceDiagram
    participant User
    participant MainSetup as main_setup.py
    participant Gemini as Gemini AI
    participant Validator as Feature Validator

    Note over MainSetup: Vault installation verified ✓
    
    activate MainSetup
    Note over MainSetup: STEP 2: TEST GENERATION
    
    MainSetup->>User: 📋 Enter your Vault feature test request:
    User-->>MainSetup: "I want to test KV2 secrets"
    
    MainSetup->>Gemini: analyze_and_validate_intent(prompt)
    activate Gemini
    
    Note right of Gemini: System Instruction:<br/>Extract feature name<br/>from user prompt
    
    Gemini->>Gemini: Process prompt with AI
    Gemini->>Validator: Extract feature: "kv"
    activate Validator
    
    Validator->>Validator: Check against<br/>VALID_VAULT_FEATURES
    Note right of Validator: ["kv", "database", "pki",<br/>"transit", "ldap", ...]
    
    alt Feature Valid
        Validator-->>Gemini: ✓ "kv" is valid
        deactivate Validator
        Gemini-->>MainSetup: ✓ Feature validated: "kv"
        deactivate Gemini
        
        MainSetup->>Gemini: generate_test_suite("kv")
        activate Gemini
        
        Note right of Gemini: System Instruction:<br/>Generate 3 pytest tests<br/>for KV2 feature
        
        Gemini->>Gemini: Generate Python code
        Note right of Gemini: - test_create_secret()<br/>- test_read_secret()<br/>- test_delete_secret()
        
        Gemini-->>MainSetup: Python test code<br/>(wrapped in ```python)
        deactivate Gemini
        
        MainSetup->>MainSetup: Extract code from markdown
        Note over MainSetup: Parse ```python ... ```
        
        MainSetup->>MainSetup: ✓ Test code ready
        Note over MainSetup: Proceed to Step 3
        deactivate MainSetup
        
    else Feature Invalid
        Validator-->>Gemini: ❌ "xyz" not in list
        deactivate Validator
        Gemini-->>MainSetup: None (validation failed)
        deactivate Gemini
        
        MainSetup->>User: ❌ PIPELINE TERMINATED<br/>Invalid feature<br/>Exit code 1
        deactivate MainSetup
    end
```

### 1.3 STEP 3: Test Execution Sequence

```mermaid
sequenceDiagram
    participant User
    participant MainSetup as main_setup.py
    participant FileSystem as File System
    participant Pytest as Pytest Runner
    participant Vault as Vault CLI
    participant Report as HTML Report

    Note over MainSetup: Test code generated ✓
    
    activate MainSetup
    Note over MainSetup: STEP 3: TEST EXECUTION
    
    MainSetup->>FileSystem: Write test code
    Note right of FileSystem: test_vault_dynamic_suite.py
    FileSystem-->>MainSetup: ✓ File saved
    
    MainSetup->>Pytest: Run pytest with HTML report
    Note right of Pytest: pytest test_vault_dynamic_suite.py<br/>--html=vault_execution_report.html
    activate Pytest
    
    Pytest->>Pytest: Discover test functions
    Note right of Pytest: - test_create_secret<br/>- test_read_secret<br/>- test_delete_secret
    
    loop For each test
        Pytest->>Vault: Execute vault CLI command
        activate Vault
        Note right of Vault: vault kv put secret/test<br/>vault kv get secret/test<br/>vault kv delete secret/test
        
        Vault->>Vault: Process command
        
        alt Command Success
            Vault-->>Pytest: ✓ Success (returncode=0)<br/>stdout: "Success! Data written..."
            Note over Pytest: Test PASSED ✓
        else Command Failed
            Vault-->>Pytest: ❌ Error (returncode≠0)<br/>stderr: "Error: permission denied"
            Note over Pytest: Test FAILED ✗
        end
        deactivate Vault
    end
    
    Pytest->>Report: Generate HTML report
    activate Report
    Note right of Report: Compile test results<br/>Format as HTML<br/>Add CSS styling
    Report-->>Pytest: ✓ Report created
    deactivate Report
    
    Pytest-->>MainSetup: Test execution complete
    Note right of Pytest: Summary:<br/>3 passed, 0 failed
    deactivate Pytest
    
    MainSetup->>FileSystem: Check report exists
    FileSystem-->>MainSetup: ✓ vault_execution_report.html
    
    MainSetup->>User: ✨ [SUCCESS] Execution complete<br/>HTML report: vault_execution_report.html
    
    MainSetup->>User: ✓ PIPELINE COMPLETED<br/>Exit code 0
    deactivate MainSetup
    
    User->>Report: Open in browser
    activate Report
    Report-->>User: Display test results
    deactivate Report
```

---

## 2. Detailed Flowchart

```mermaid
flowchart TD
    Start([User runs main_setup.py]) --> Init[Initialize Pipeline]
    
    Init --> Step1[STEP 1: VAULT INSTALLATION]
    
    Step1 --> DetectOS{Detect Operating System}
    DetectOS -->|macOS| CheckMac[Check if Vault installed]
    DetectOS -->|Linux| CheckLinux[Check if Vault installed]
    DetectOS -->|Windows| CheckWin[Check if Vault installed]
    DetectOS -->|Other| UnsupportedOS[❌ Unsupported OS]
    
    CheckMac --> IsInstalled{Already Installed?}
    CheckLinux --> IsInstalled
    CheckWin --> IsInstalled
    
    IsInstalled -->|Yes| VerifyVersion[✓ Verify version]
    IsInstalled -->|No| InstallVault[Install Vault]
    
    InstallVault -->|macOS| Homebrew[brew install vault]
    InstallVault -->|Linux| DetectDistro{Detect Distribution}
    InstallVault -->|Windows| Chocolatey[choco install vault]
    
    DetectDistro -->|Ubuntu/Debian| APT[apt install vault]
    DetectDistro -->|RHEL/CentOS| YUM[yum install vault]
    DetectDistro -->|Other| ManualInstall[❌ Manual install required]
    
    Homebrew --> VerifyInstall[Verify installation]
    APT --> VerifyInstall
    YUM --> VerifyInstall
    Chocolatey --> VerifyInstall
    
    VerifyInstall -->|Success| VerifyVersion
    VerifyInstall -->|Failed| InstallFailed[❌ Installation failed]
    
    VerifyVersion --> Step2[STEP 2: TEST GENERATION]
    
    InstallFailed --> Exit1[Exit code 1]
    UnsupportedOS --> Exit1
    ManualInstall --> Exit1
    
    Step2 --> GetInput[Get user input for test request]
    GetInput --> ValidateInput{Input empty?}
    
    ValidateInput -->|Yes| EmptyInput[❌ Empty request]
    ValidateInput -->|No| CallGemini[Call Gemini AI]
    
    CallGemini --> ExtractFeature[Extract feature name from prompt]
    ExtractFeature --> ValidateFeature{Feature in<br/>VALID_VAULT_FEATURES?}
    
    ValidateFeature -->|Yes| FeatureValid[✓ Feature validated]
    ValidateFeature -->|No| InvalidFeature[❌ Invalid feature]
    
    FeatureValid --> GenerateTests[Generate 3 pytest test functions]
    GenerateTests --> ParseCode{Code block<br/>extracted?}
    
    ParseCode -->|Yes| Step3[STEP 3: TEST EXECUTION]
    ParseCode -->|No| GenFailed[❌ Generation failed]
    
    InvalidFeature --> Exit2[Exit code 1]
    EmptyInput --> Exit2
    GenFailed --> Exit2
    
    Step3 --> SaveFile[Save test code to<br/>test_vault_dynamic_suite.py]
    SaveFile --> RunPytest[Run pytest with HTML report]
    
    RunPytest --> ExecuteTests[Execute vault CLI commands]
    ExecuteTests --> GenerateReport[Generate HTML report]
    
    GenerateReport --> ReportExists{Report file<br/>created?}
    
    ReportExists -->|Yes| Success[✨ Report: vault_execution_report.html]
    ReportExists -->|No| ReportWarning[⚠️ Report generation failed]
    
    Success --> Complete[✓ PIPELINE COMPLETED]
    ReportWarning --> Complete
    
    Complete --> Exit0[Exit code 0]
    
    Exit0 --> End([End])
    Exit1 --> End
    Exit2 --> End
    
    style Step1 fill:#cce5ff
    style Step2 fill:#ccffdd
    style Step3 fill:#ffddcc
    style Success fill:#90EE90
    style Complete fill:#90EE90
    style InstallFailed fill:#FFB6C1
    style InvalidFeature fill:#FFB6C1
    style GenFailed fill:#FFB6C1
    style UnsupportedOS fill:#FFB6C1
```

---

## 3. Component Interaction Diagram

```mermaid
graph TB
    subgraph User Interface
        UI[User Terminal]
    end
    
    subgraph Main Pipeline - main_setup.py
        Main[main function]
        Main --> Installer[VaultInstaller Class]
        Main --> Agent[Test Agent Functions]
    end
    
    subgraph Vault Installer
        Installer --> DetectOS[detect_os]
        Installer --> CheckInstall[is_vault_installed]
        Installer --> InstallMac[install_macos]
        Installer --> InstallLinux[install_linux]
        Installer --> InstallWin[install_windows]
    end
    
    subgraph Test Agent
        Agent --> Validate[analyze_and_validate_intent]
        Agent --> Generate[generate_test_suite]
        Agent --> Execute[execute_and_report]
    end
    
    subgraph External Systems
        Brew[Homebrew]
        APT[APT Package Manager]
        YUM[YUM Package Manager]
        Choco[Chocolatey]
        Gemini[Google Gemini AI]
        Pytest[Pytest Framework]
        Vault[Vault CLI]
    end
    
    UI -->|Run script| Main
    
    DetectOS -->|platform.system| OS[Operating System]
    CheckInstall -->|vault --version| Vault
    
    InstallMac -->|brew install| Brew
    InstallLinux -->|apt/yum install| APT
    InstallLinux -->|apt/yum install| YUM
    InstallWin -->|choco install| Choco
    
    Validate -->|API call| Gemini
    Generate -->|API call| Gemini
    
    Execute -->|pytest command| Pytest
    Pytest -->|vault commands| Vault
    
    Execute -->|HTML report| Report[vault_execution_report.html]
    Execute -->|Test file| TestFile[test_vault_dynamic_suite.py]
    
    Report -->|View in browser| UI
    
    style Main fill:#4A90E2
    style Installer fill:#7ED321
    style Agent fill:#F5A623
    style Gemini fill:#BD10E0
    style Vault fill:#50E3C2
```

---

## 4. State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> Initializing: Run main_setup.py
    
    Initializing --> InstallingVault: Start Step 1
    
    InstallingVault --> CheckingInstallation: Detect OS
    CheckingInstallation --> AlreadyInstalled: Vault found
    CheckingInstallation --> Installing: Vault not found
    
    Installing --> VerifyingInstallation: Package manager install
    VerifyingInstallation --> InstallationVerified: Success
    VerifyingInstallation --> InstallationFailed: Failed
    
    AlreadyInstalled --> InstallationVerified: Version check passed
    
    InstallationVerified --> GettingUserInput: Start Step 2
    InstallationFailed --> [*]: Exit(1)
    
    GettingUserInput --> ValidatingFeature: User enters request
    ValidatingFeature --> CallingGemini: Non-empty input
    ValidatingFeature --> [*]: Empty input - Exit(1)
    
    CallingGemini --> FeatureValidated: Feature in valid list
    CallingGemini --> FeatureInvalid: Feature not recognized
    
    FeatureInvalid --> [*]: Exit(1)
    
    FeatureValidated --> GeneratingTests: Call Gemini AI
    GeneratingTests --> TestsGenerated: Code extracted
    GeneratingTests --> GenerationFailed: No code block
    
    GenerationFailed --> [*]: Exit(1)
    
    TestsGenerated --> ExecutingTests: Start Step 3
    ExecutingTests --> SavingTestFile: Write to file
    SavingTestFile --> RunningPytest: Execute pytest
    
    RunningPytest --> GeneratingReport: Tests complete
    GeneratingReport --> ReportGenerated: HTML created
    GeneratingReport --> ReportFailed: HTML not created
    
    ReportGenerated --> Completed: Success
    ReportFailed --> Completed: Warning shown
    
    Completed --> [*]: Exit(0)
```

---

## 5. Data Flow Diagram

```mermaid
flowchart LR
    subgraph Input
        UserPrompt[User Prompt:<br/>'Test KV2 secrets']
        EnvVars[Environment Variables:<br/>VAULT_ADDR, VAULT_TOKEN]
    end
    
    subgraph Processing
        OSDetection[OS Detection:<br/>Darwin/Linux/Windows]
        VaultCheck[Vault Version Check]
        FeatureExtraction[Feature Extraction:<br/>Gemini AI]
        FeatureValidation[Feature Validation:<br/>Against VALID_VAULT_FEATURES]
        TestGeneration[Test Code Generation:<br/>Gemini AI]
        CodeParsing[Code Parsing:<br/>Extract Python from markdown]
    end
    
    subgraph Execution
        FileWrite[Write test_vault_dynamic_suite.py]
        PytestRun[Pytest Execution]
        VaultCommands[Vault CLI Commands]
    end
    
    subgraph Output
        TestFile[test_vault_dynamic_suite.py]
        HTMLReport[vault_execution_report.html]
        ConsoleOutput[Console Output:<br/>Success/Failure messages]
        ExitCode[Exit Code: 0 or 1]
    end
    
    UserPrompt --> FeatureExtraction
    EnvVars --> VaultCommands
    
    OSDetection --> VaultCheck
    VaultCheck -->|Installed| FeatureExtraction
    VaultCheck -->|Not Installed| InstallProcess[Installation Process]
    InstallProcess --> VaultCheck
    
    FeatureExtraction --> FeatureValidation
    FeatureValidation -->|Valid| TestGeneration
    FeatureValidation -->|Invalid| ExitCode
    
    TestGeneration --> CodeParsing
    CodeParsing --> FileWrite
    
    FileWrite --> TestFile
    TestFile --> PytestRun
    
    PytestRun --> VaultCommands
    VaultCommands --> HTMLReport
    
    PytestRun --> ConsoleOutput
    HTMLReport --> ConsoleOutput
    ConsoleOutput --> ExitCode
    
    style UserPrompt fill:#E3F2FD
    style TestFile fill:#C8E6C9
    style HTMLReport fill:#FFF9C4
    style ExitCode fill:#FFCCBC
```

---

## How to Edit These Diagrams

### Using Mermaid Live Editor
1. Visit: https://mermaid.live/
2. Copy any diagram code from above
3. Paste into the editor
4. Edit the diagram visually or via code
5. Export as PNG, SVG, or copy updated code

### Supported Markdown Viewers
- GitHub (renders Mermaid natively)
- GitLab (renders Mermaid natively)
- VS Code (with Mermaid extension)
- Obsidian (with Mermaid plugin)
- Notion (paste as code block)

### Diagram Types Included
1. **Sequence Diagram** - Shows interaction between components over time
2. **Flowchart** - Detailed step-by-step decision flow
3. **Component Diagram** - System architecture and dependencies
4. **State Diagram** - State transitions during execution
5. **Data Flow Diagram** - How data moves through the system

### Quick Edit Guide

**To add a new step:**
```mermaid
NewStep[Description] --> NextStep
```

**To add a decision:**
```mermaid
Decision{Question?} -->|Yes| YesPath
Decision -->|No| NoPath
```

**To change colors:**
```mermaid
style NodeName fill:#HexColor
```

**To add notes:**
```mermaid
Note over Component: Note text
```

---

## Legend

### Colors
- 🔵 Blue: Installation steps
- 🟢 Green: Test generation steps
- 🟠 Orange: Test execution steps
- 🔴 Red: Error/failure states
- ⚪ White: Neutral/transition states

### Symbols
- ✓ Success
- ❌ Failure/Error
- ⚠️ Warning
- 🤖 AI/Automation
- 💾 File operation
- 🚀 Execution
- ✨ Completion

---

## Version History
- v1.0 (2026-05-29): Initial diagrams created for main_setup.py