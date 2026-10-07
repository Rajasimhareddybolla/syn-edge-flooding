#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-lab.env}"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ FAIL: Environment file $ENV_FILE does not exist." >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

REQUIRED_VARS=(
    "AWS_REGION" "VPC_ID" "SG_ID" "KEY_NAME" "KEY_PATH"
    "VICTIM_ID" "ATTACKER_ID" "CLIENT_ID"
    "VICTIM_PUB" "ATTACKER_PUB" "CLIENT_PUB"
    "VICTIM_PRIVATE_IP" "ATTACKER_PRIVATE_IP" "CLIENT_PRIVATE_IP"
    "VICTIM_IFACE"
)

ERRORS=0
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        echo "❌ FAIL: Required variable '$var' is unset or empty in $ENV_FILE" >&2
        ERRORS=$((ERRORS + 1))
    fi
done

# Check key path exists
RESOLVED_KEY=$(eval echo "$KEY_PATH")
if [[ ! -f "$RESOLVED_KEY" ]]; then
    echo "❌ FAIL: KEY_PATH '$RESOLVED_KEY' does not point to an existing file." >&2
    ERRORS=$((ERRORS + 1))
fi

if [[ $ERRORS -gt 0 ]]; then
    echo "❌ Validation failed with $ERRORS errors." >&2
    exit 1
fi

echo "PASS: lab.env is complete and syntactically valid."

