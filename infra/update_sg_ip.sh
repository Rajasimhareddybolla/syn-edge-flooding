#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="/Users/raja/Documents/syn-edge-flooding"
LAB_ENV="$LAB_ROOT/lab.env"

if [[ ! -f "$LAB_ENV" ]]; then
  echo "❌ Error: $LAB_ENV not found" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$LAB_ENV"

NEW_IP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
if ! [[ "$NEW_IP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
  echo "❌ Error: Failed to resolve valid operator IPv4 address: '$NEW_IP'" >&2
  exit 1
fi
echo "Detected current operator IP: $NEW_IP"

# Query existing SSH ingress rule CIDRs
CURRENT_CIDRS=$(aws ec2 describe-security-groups \
  --group-ids "$SG_ID" \
  --region "$AWS_REGION" \
  --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`].IpRanges[].CidrIp' \
  --output text)

for CIDR in $CURRENT_CIDRS; do
  if [[ "$CIDR" != "${NEW_IP}/32" ]]; then
    echo "Revoking stale SSH rule for $CIDR..."
    aws ec2 revoke-security-group-ingress \
      --group-id "$SG_ID" \
      --protocol tcp \
      --port 22 \
      --cidr "$CIDR" \
      --region "$AWS_REGION" || true
  fi
done

echo "Authorizing updated SSH ingress for ${NEW_IP}/32..."
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 22 \
  --cidr "${NEW_IP}/32" \
  --region "$AWS_REGION" 2>/dev/null || echo "Rule already active."

# Audit to LAB_LOG.md if IP changed
if [[ -f "$LAB_ROOT/LAB_LOG.md" ]]; then
  echo -e "\n## [$(date -u +"%Y-%m-%dT%H:%M:%SZ")] — PARAMETER_CHANGE: Operator IP Shift\n- **Phase:** Active Phase\n- **Agent / Actor:** update_sg_ip.sh\n- **Category:** [PARAMETER_CHANGE]\n- **Description:** Security group $SG_ID SSH rule updated to $NEW_IP/32.\n- **Rationale / Justification:** Maintain operator reachability.\n" >> "$LAB_ROOT/LAB_LOG.md"
fi

echo "✅ Security Group SSH ingress updated to ${NEW_IP}/32"

