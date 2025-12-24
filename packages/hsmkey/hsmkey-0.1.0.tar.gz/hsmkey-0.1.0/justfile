# Justfile for hsmkey project

# Default recipe
default:
    @just --list

# HSM Configuration - detect SoftHSM2 module path
SOFTHSM_MODULE := if path_exists("/usr/lib/softhsm/libsofthsm2.so") == "true" {
    "/usr/lib/softhsm/libsofthsm2.so"
} else {
    "/usr/lib64/softhsm/libsofthsm2.so"
}
KRYOPTIC_MODULE := env_var_or_default("KRYOPTIC_MODULE", "~/kryoptic/target/release/libkryoptic_pkcs11.so")
HSM_MODULE := env_var_or_default("HSM_MODULE", SOFTHSM_MODULE)
TOKEN_LABEL := "hsmkey-test"
PIN := "12345678"
KEY_DIR := "tests/data"

# Ensure SoftHSM2 configuration exists
ensure-softhsm-config:
    #!/usr/bin/env bash
    set -euo pipefail
    CONFIG_DIR="$HOME/.config/softhsm"
    CONFIG_FILE="$CONFIG_DIR/softhsm2.conf"
    TOKEN_DIR="$HOME/.local/share/softhsm/tokens"
    if [ -f "$CONFIG_FILE" ]; then
        echo "SoftHSM2 config already exists: $CONFIG_FILE"
        exit 0
    fi
    echo "Creating SoftHSM2 configuration..."
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$TOKEN_DIR"
    echo "# SoftHSM2 configuration file" > "$CONFIG_FILE"
    echo "directories.tokendir = $TOKEN_DIR" >> "$CONFIG_FILE"
    echo "objectstore.backend = file" >> "$CONFIG_FILE"
    echo "log.level = INFO" >> "$CONFIG_FILE"
    echo "slots.removable = false" >> "$CONFIG_FILE"
    echo "Created $CONFIG_FILE"
    echo "Token directory: $TOKEN_DIR"

# Ensure Kryoptic configuration exists
ensure-kryoptic-config:
    #!/usr/bin/env bash
    set -euo pipefail
    CONFIG_DIR="$HOME/.config/kryoptic"
    CONFIG_FILE="$CONFIG_DIR/token.conf"
    STORAGE_FILE="$CONFIG_DIR/token.sql"
    if [ -f "$CONFIG_FILE" ]; then
        echo "Kryoptic config already exists: $CONFIG_FILE"
        exit 0
    fi
    echo "Creating Kryoptic configuration..."
    mkdir -p "$CONFIG_DIR"
    echo "# Kryoptic PKCS#11 Token Configuration" > "$CONFIG_FILE"
    echo "" >> "$CONFIG_FILE"
    echo "[ec_point_encoding]" >> "$CONFIG_FILE"
    echo 'encoding = "Bytes"' >> "$CONFIG_FILE"
    echo "" >> "$CONFIG_FILE"
    echo "[[slots]]" >> "$CONFIG_FILE"
    echo "slot = 1" >> "$CONFIG_FILE"
    echo 'description = "{{TOKEN_LABEL}}"' >> "$CONFIG_FILE"
    echo 'manufacturer = "Kryoptic"' >> "$CONFIG_FILE"
    echo 'dbtype = "sqlite"' >> "$CONFIG_FILE"
    echo "dbargs = \"$STORAGE_FILE\"" >> "$CONFIG_FILE"
    echo "Created $CONFIG_FILE"
    echo "Storage file: $STORAGE_FILE"

# Initialize SoftHSM2 token for testing
init-hsm: ensure-softhsm-config
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if token already exists
    if softhsm2-util --show-slots 2>/dev/null | grep -q "{{TOKEN_LABEL}}"; then
        echo "Token '{{TOKEN_LABEL}}' already exists"
        exit 0
    fi

    echo "Initializing token '{{TOKEN_LABEL}}'..."
    softhsm2-util --init-token --free --label "{{TOKEN_LABEL}}" --so-pin "{{PIN}}" --pin "{{PIN}}"
    echo "Token initialized successfully"

# Delete the test token
delete-hsm:
    #!/usr/bin/env bash
    set -euo pipefail

    # Find the token slot
    SLOT=$(softhsm2-util --show-slots 2>/dev/null | grep -B5 "{{TOKEN_LABEL}}" | grep "Slot" | head -1 | grep -oP '0x[0-9a-f]+' || echo "")

    if [ -n "$SLOT" ]; then
        echo "Deleting token in slot $SLOT..."
        softhsm2-util --delete-token --token "{{TOKEN_LABEL}}"
        echo "Token deleted"
    else
        echo "Token '{{TOKEN_LABEL}}' not found"
    fi

# Generate all test keys on disk
recreate-keys:
    #!/usr/bin/env bash
    set -euo pipefail

    PRIV_DIR="{{KEY_DIR}}/privatekeys"
    PUB_DIR="{{KEY_DIR}}/publickeys"

    mkdir -p "$PRIV_DIR" "$PUB_DIR"

    echo "Generating RSA keys..."
    # RSA 2048
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$PRIV_DIR/rsa-2048.pem"
    openssl pkey -in "$PRIV_DIR/rsa-2048.pem" -pubout -out "$PUB_DIR/rsa-2048.pem"

    # RSA 3072
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out "$PRIV_DIR/rsa-3072.pem"
    openssl pkey -in "$PRIV_DIR/rsa-3072.pem" -pubout -out "$PUB_DIR/rsa-3072.pem"

    # RSA 4096
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out "$PRIV_DIR/rsa-4096.pem"
    openssl pkey -in "$PRIV_DIR/rsa-4096.pem" -pubout -out "$PUB_DIR/rsa-4096.pem"

    echo "Generating EC keys..."
    # EC P-256
    openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:prime256v1 -out "$PRIV_DIR/ec-p256.pem"
    openssl pkey -in "$PRIV_DIR/ec-p256.pem" -pubout -out "$PUB_DIR/ec-p256.pem"

    # EC P-384
    openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:secp384r1 -out "$PRIV_DIR/ec-p384.pem"
    openssl pkey -in "$PRIV_DIR/ec-p384.pem" -pubout -out "$PUB_DIR/ec-p384.pem"

    # EC P-521
    openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:secp521r1 -out "$PRIV_DIR/ec-p521.pem"
    openssl pkey -in "$PRIV_DIR/ec-p521.pem" -pubout -out "$PUB_DIR/ec-p521.pem"

    echo "Generating EdDSA keys..."
    # Ed25519
    openssl genpkey -algorithm Ed25519 -out "$PRIV_DIR/ed25519.pem"
    openssl pkey -in "$PRIV_DIR/ed25519.pem" -pubout -out "$PUB_DIR/ed25519.pem"

    # Ed448
    openssl genpkey -algorithm Ed448 -out "$PRIV_DIR/ed448.pem"
    openssl pkey -in "$PRIV_DIR/ed448.pem" -pubout -out "$PUB_DIR/ed448.pem"

    echo "All keys generated successfully in $PRIV_DIR and $PUB_DIR"
    ls -la "$PRIV_DIR"

# Import all keys to SoftHSM2
import-keys: init-hsm
    #!/usr/bin/env bash
    set -euo pipefail

    PRIV_DIR="{{KEY_DIR}}/privatekeys"
    PUB_DIR="{{KEY_DIR}}/publickeys"
    MODULE="{{HSM_MODULE}}"

    # Check if keys exist
    if [ ! -d "$PRIV_DIR" ] || [ -z "$(ls -A $PRIV_DIR 2>/dev/null)" ]; then
        echo "No keys found in $PRIV_DIR. Run 'just recreate-keys' first."
        exit 1
    fi

    echo "Importing keys to SoftHSM2..."

    # Import RSA keys (both private and public)
    echo "Importing RSA 2048..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/rsa-2048.pem" --type privkey \
        --label "rsa-2048" --id 10 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/rsa-2048.pem" --type pubkey \
        --label "rsa-2048" --id 10 2>/dev/null || true

    echo "Importing RSA 3072..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/rsa-3072.pem" --type privkey \
        --label "rsa-3072" --id 11 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/rsa-3072.pem" --type pubkey \
        --label "rsa-3072" --id 11 2>/dev/null || true

    echo "Importing RSA 4096..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/rsa-4096.pem" --type privkey \
        --label "rsa-4096" --id 12 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/rsa-4096.pem" --type pubkey \
        --label "rsa-4096" --id 12 2>/dev/null || true

    # Import EC keys (both private and public)
    echo "Importing EC P-256..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/ec-p256.pem" --type privkey \
        --label "ec-p256" --id 01 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/ec-p256.pem" --type pubkey \
        --label "ec-p256" --id 01 2>/dev/null || true

    echo "Importing EC P-384..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/ec-p384.pem" --type privkey \
        --label "ec-p384" --id 02 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/ec-p384.pem" --type pubkey \
        --label "ec-p384" --id 02 2>/dev/null || true

    echo "Importing EC P-521..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/ec-p521.pem" --type privkey \
        --label "ec-p521" --id 03 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/ec-p521.pem" --type pubkey \
        --label "ec-p521" --id 03 2>/dev/null || true

    # Import EdDSA keys using Python (pkcs11-tool doesn't support EdDSA import well)
    echo "Importing Ed25519 and Ed448 keys..."
    uv run python scripts/import_eddsa_keys.py

    echo "Listing imported keys..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" -O 2>/dev/null | grep -E "(label:|ID:|type:)" || true

    echo "Keys imported successfully"

# List all keys in the HSM
list-keys:
    pkcs11-tool --module "{{HSM_MODULE}}" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" -O

# Run tests
test:
    uv run pytest tests/ -v

# Run type checker
lint:
    uv run ty check src/

# Run tests with coverage
test-cov:
    uv run pytest tests/ -v --cov=src/hsmkey --cov-report=term-missing

# Clean up generated files
clean:
    rm -rf tests/data/privatekeys/*.pem tests/data/publickeys/*.pem
    rm -rf .pytest_cache __pycache__ .coverage
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Full setup: recreate keys and import to HSM
setup: recreate-keys import-keys
    @echo "Setup complete!"

# Reset: delete token and reimport the keys
reset: delete-hsm import-keys
    @echo "Reset complete!"

# ============ Kryoptic Support ============

# Initialize kryoptic token
init-kryoptic: ensure-kryoptic-config
    #!/usr/bin/env bash
    set -euo pipefail

    STORAGE_DIR="$HOME/.config/kryoptic"

    # Remove old database if exists
    rm -f "$STORAGE_DIR/token.sql"

    echo "Initializing kryoptic token..."
    pkcs11-tool --module "{{KRYOPTIC_MODULE}}" \
        --init-token \
        --label "{{TOKEN_LABEL}}" \
        --so-pin "{{PIN}}" 2>/dev/null

    pkcs11-tool --module "{{KRYOPTIC_MODULE}}" \
        --init-pin \
        --so-pin "{{PIN}}" \
        --pin "{{PIN}}" 2>/dev/null

    echo "Kryoptic token initialized"

# Import keys to kryoptic (RSA and EC only, no EdDSA)
import-keys-kryoptic: init-kryoptic
    #!/usr/bin/env bash
    set -euo pipefail

    PRIV_DIR="{{KEY_DIR}}/privatekeys"
    PUB_DIR="{{KEY_DIR}}/publickeys"
    MODULE="{{KRYOPTIC_MODULE}}"

    # Check if keys exist
    if [ ! -d "$PRIV_DIR" ] || [ -z "$(ls -A $PRIV_DIR 2>/dev/null)" ]; then
        echo "No keys found in $PRIV_DIR. Run 'just recreate-keys' first."
        exit 1
    fi

    echo "Importing keys to kryoptic..."

    # Import RSA keys (with usage flags for sign/decrypt)
    echo "Importing RSA 2048..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/rsa-2048.pem" --type privkey \
        --label "rsa-2048" --id 10 --usage-sign --usage-decrypt 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/rsa-2048.pem" --type pubkey \
        --label "rsa-2048" --id 10 --usage-sign --usage-decrypt 2>/dev/null || true

    echo "Importing RSA 3072..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/rsa-3072.pem" --type privkey \
        --label "rsa-3072" --id 11 --usage-sign --usage-decrypt 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/rsa-3072.pem" --type pubkey \
        --label "rsa-3072" --id 11 --usage-sign --usage-decrypt 2>/dev/null || true

    echo "Importing RSA 4096..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/rsa-4096.pem" --type privkey \
        --label "rsa-4096" --id 12 --usage-sign --usage-decrypt 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/rsa-4096.pem" --type pubkey \
        --label "rsa-4096" --id 12 --usage-sign --usage-decrypt 2>/dev/null || true

    # Import EC keys (with usage flag for sign)
    echo "Importing EC P-256..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/ec-p256.pem" --type privkey \
        --label "ec-p256" --id 01 --usage-sign 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/ec-p256.pem" --type pubkey \
        --label "ec-p256" --id 01 --usage-sign 2>/dev/null || true

    echo "Importing EC P-384..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/ec-p384.pem" --type privkey \
        --label "ec-p384" --id 02 --usage-sign 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/ec-p384.pem" --type pubkey \
        --label "ec-p384" --id 02 --usage-sign 2>/dev/null || true

    echo "Importing EC P-521..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PRIV_DIR/ec-p521.pem" --type privkey \
        --label "ec-p521" --id 03 --usage-sign 2>/dev/null || true
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" \
        --write-object "$PUB_DIR/ec-p521.pem" --type pubkey \
        --label "ec-p521" --id 03 --usage-sign 2>/dev/null || true

    echo "Note: EdDSA keys not imported (kryoptic requires OpenSSL 3.2+)"

    echo "Listing imported keys..."
    pkcs11-tool --module "$MODULE" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" -O 2>/dev/null | grep -E "(label:|ID:|Usage:)" || true

    echo "Keys imported successfully"

# List keys in kryoptic
list-keys-kryoptic:
    pkcs11-tool --module "{{KRYOPTIC_MODULE}}" --token-label "{{TOKEN_LABEL}}" \
        --login --pin "{{PIN}}" -O

# Run tests against kryoptic (skips EdDSA tests)
test-kryoptic:
    HSM_MODULE="{{KRYOPTIC_MODULE}}" HSM_PIN="{{PIN}}" uv run pytest tests/ -v --ignore=tests/test_ed25519.py --ignore=tests/test_ed448.py

# Clean kryoptic storage
clean-kryoptic:
    #!/usr/bin/env bash
    rm -f "$HOME/.config/kryoptic/token.sql"
    echo "Kryoptic storage cleaned"

# Setup kryoptic: generate keys and import
setup-kryoptic: recreate-keys import-keys-kryoptic
    @echo "Kryoptic setup complete!"

# Full test: run against both SoftHSM2 and kryoptic
test-all: reset test clean-kryoptic setup-kryoptic test-kryoptic
    @echo "All tests complete!"
