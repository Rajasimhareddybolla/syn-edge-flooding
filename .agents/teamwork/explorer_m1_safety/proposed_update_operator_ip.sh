#!/usr/bin/env bash
# ==============================================================================
# update_operator_ip.sh — Atomic Operator Public IP Rotation for lab-sg
# ==============================================================================
# Usage: bash infra/update_operator_ip.sh
# Safely updates Security Group port 22 access when the operator's ISP/public IP changes.
# ==============================================================================
set -euo pipefail

LAB_ENV_PATH="${LAB_ENV_PATH:-lab.env}"
LOG_FILE="${LOG_FILE:-LAB_LOG.md}"

if [ ! -f "$LAB_ENV_PATH" ]; then
  echo "FATAL: lab.env not found at '$LAB_ENV_PATH'!" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$LAB_ENV_PATH"

echo "==> Resolving current public IPv4 address..."
NEW_IP=$(curl -s --connect-timeout 5 https://checkip.amazonaws.com | tr -d '[:space:]')

if ! [[ "$NEW_IP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
  echo "FATAL: Resolved invalid IPv4: '$NEW_IP'" >&2
  exit 1
fi

echo "    Current Public IPv4: $NEW_IP"

# Describe SG to find existing SSH rules
SG_JSON=$(aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" --output json)

OLD_IPS=$(echo "$SG_JSON" | jq -r '
  .SecurityGroups[0].IpPermissions[] |
  select(.FromPort == 22 and .ToPort == 22 and .IpProtocol == "tcp") |
  .IpRanges[].CidrIp
')

if [ "$OLD_IPS" = "${NEW_IP}/32" ]; then
  echo "==> Security Group $SG_ID is already configured for $NEW_IP/32. No update needed."
  exit 0
fi

echo "==> Authorizing new SSH ingress rule: $NEW_IP/32 on port 22..."
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --region "$AWS_REGION" \
  --ip-permissions IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges="[{CidrIp=${NEW_IP}/32,Description='Operator SSH access'}]"

# Revoke old IP rules if present
if [ -n "$OLD_IPS" ]; then
  for OLD_CIDR in $OLD_IPS; do
    if [ "$OLD_CIDR" != "${NEW_IP}/32" ]; then
      echo "==> Revoking outdated SSH ingress rule: $OLD_CIDR..."
      aws ec2 revoke-security-group-ingress \
        --group-id "$SG_ID" \
        --region "$AWS_REGION" \
        --ip-permissions IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges="[{CidrIp=${OLD_CIDR}}]" || true
    fi
  done
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_ENTRY="- **[$TIMESTAMP] OPERATOR IP ROTATION:** Updated $SG_ID SSH ingress from ${OLD_IPS:-none} to ${NEW_IP}/32."
echo "$LOG_ENTRY" >> "$LOG_FILE"
echo "==> Updated $LOG_FILE with rotation record."

echo "==> Verifying new security group configuration..."
bash infra/verify_m1_safety.sh
echo "==> IP rotation completed successfully."
