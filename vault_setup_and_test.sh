#!/bin/bash
# vault_setup_and_test.sh

echo "=== Vault Setup and Test Script ==="

# Step 1: Check if Vault is installed
if ! command -v vault &> /dev/null; then
    echo "❌ Vault is not installed"
    echo "Install with: brew install hashicorp/tap/vault"
    exit 1
fi

echo "✓ Vault is installed: $(vault --version)"

# Step 2: Check if Vault server is running
if ! curl -s http://127.0.0.1:8200/v1/sys/health &> /dev/null; then
    echo "❌ Vault server is not running"
    echo ""
    echo "Start Vault dev server in a separate terminal:"
    echo "  vault server -dev"
    echo ""
    echo "Then set these environment variables:"
    echo "  export VAULT_ADDR='http://127.0.0.1:8200'"
    echo "  export VAULT_TOKEN='<root-token-from-dev-server>'"
    exit 1
fi

echo "✓ Vault server is running"

# Step 3: Check environment variables
if [ -z "$VAULT_ADDR" ]; then
    echo "❌ VAULT_ADDR is not set"
    echo "Set with: export VAULT_ADDR='http://127.0.0.1:8200'"
    exit 1
fi

if [ -z "$VAULT_TOKEN" ]; then
    echo "❌ VAULT_TOKEN is not set"
    echo "Set with: export VAULT_TOKEN='<your-root-token>'"
    exit 1
fi

echo "✓ Environment variables are set"
echo "  VAULT_ADDR: $VAULT_ADDR"
echo "  VAULT_TOKEN: ${VAULT_TOKEN:0:10}..."

# Step 4: Verify connection
echo ""
echo "=== Testing Vault Connection ==="
if vault status &> /dev/null; then
    echo "✓ Successfully connected to Vault"
else
    echo "❌ Failed to connect to Vault"
    exit 1
fi

# Step 5: Enable KV2 (if not already enabled)
echo ""
echo "=== Enabling KV2 Secrets Engine ==="
if vault secrets list | grep -q "^secret/"; then
    echo "✓ KV2 secrets engine already enabled at 'secret/'"
else
    vault secrets enable -version=2 -path=secret kv
    echo "✓ KV2 secrets engine enabled at 'secret/'"
fi

# Step 6: Run test operations
echo ""
echo "=== Running Test Operations ==="

# Test 1: Create secret
echo "Test 1: Creating secret..."
vault kv put secret/myapp username=admin password=secret123 email=admin@example.com
echo "✓ Secret created"

# Test 2: Read secret
echo ""
echo "Test 2: Reading secret..."
vault kv get secret/myapp
echo "✓ Secret read successfully"

# Test 3: Update secret
echo ""
echo "Test 3: Updating secret..."
vault kv put secret/myapp username=admin password=newsecret456 email=admin@example.com
echo "✓ Secret updated"

# Test 4: Get metadata
echo ""
echo "Test 4: Getting metadata..."
vault kv metadata get secret/myapp
echo "✓ Metadata retrieved"

# Test 5: List secrets
echo ""
echo "Test 5: Listing secrets..."
vault kv list secret/
echo "✓ Secrets listed"

echo ""
echo "=== All Tests Completed Successfully ==="
