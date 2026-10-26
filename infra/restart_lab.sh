#!/usr/bin/env bash
# ==============================================================================
# infra/restart_lab.sh — Start stopped lab EC2 instances, update public IPs, and verify
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_ENV="$REPO_ROOT/lab.env"

if [[ ! -f "$LAB_ENV" ]]; then
    echo "❌ Error: $LAB_ENV not found" >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$LAB_ENV"

echo "=============================================================================="
echo "⚡ Starting TCP Flood Lab EC2 Instances..."
echo "=============================================================================="
echo "Region:       $AWS_REGION"
echo "Victim ID:    $VICTIM_ID"
echo "Attacker ID:  $ATTACKER_ID"
echo "Client ID:    $CLIENT_ID"

aws ec2 start-instances \
    --region "$AWS_REGION" \
    --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
    --output text

echo "⏳ Waiting for instances to reach 'running' state..."
aws ec2 wait instance-running \
    --region "$AWS_REGION" \
    --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID"

echo "🔍 Fetching new public IP assignments..."
VICTIM_NEW_PUB=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$VICTIM_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
ATTACKER_NEW_PUB=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$ATTACKER_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
CLIENT_NEW_PUB=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$CLIENT_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "  Victim Public IP:   $VICTIM_NEW_PUB"
echo "  Attacker Public IP: $ATTACKER_NEW_PUB"
echo "  Client Public IP:   $CLIENT_NEW_PUB"

echo "📝 Updating $LAB_ENV with new public IPs..."
cat > "$LAB_ENV" <<EOF
# ==============================================================================
# lab.env — TCP Flooding Detection Research Lab Environment Configuration
# Updated by infra/restart_lab.sh
# ==============================================================================

export AWS_REGION="$AWS_REGION"
export VPC_ID="$VPC_ID"
export SG_ID="$SG_ID"
export KEY_NAME="$KEY_NAME"
export KEY_PATH="$KEY_PATH"

export VICTIM_ID="$VICTIM_ID"
export ATTACKER_ID="$ATTACKER_ID"
export CLIENT_ID="$CLIENT_ID"

export VICTIM_PUB="$VICTIM_NEW_PUB"
export ATTACKER_PUB="$ATTACKER_NEW_PUB"
export CLIENT_PUB="$CLIENT_NEW_PUB"

export VICTIM_PRIVATE_IP="$VICTIM_PRIVATE_IP"
export ATTACKER_PRIVATE_IP="$ATTACKER_PRIVATE_IP"
export CLIENT_PRIVATE_IP="$CLIENT_PRIVATE_IP"

export VICTIM_IFACE="$VICTIM_IFACE"
EOF

echo "🔒 Updating Security Group with current operator IP..."
bash "$REPO_ROOT/infra/update_sg_ip.sh"

echo "⏳ Waiting 10s for SSH daemons to initialize..."
sleep 10

echo "🔍 Verifying SSH reachability to all nodes..."
SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10)

ssh "${SSH_OPTS[@]}" "ubuntu@$VICTIM_NEW_PUB" "uptime" >/dev/null && echo "  ✅ Victim SSH OK"
ssh "${SSH_OPTS[@]}" "ubuntu@$ATTACKER_NEW_PUB" "uptime" >/dev/null && echo "  ✅ Attacker SSH OK"
ssh "${SSH_OPTS[@]}" "ubuntu@$CLIENT_NEW_PUB" "uptime" >/dev/null && echo "  ✅ Client SSH OK"

echo "=============================================================================="
echo "🎉 Lab instances successfully restarted and ready!"
echo "=============================================================================="

