#!/usr/bin/env bash
# ==============================================================================
# infra/stop_lab.sh — Stop lab EC2 instances to halt compute charges
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
echo "🛑 Stopping TCP Flood Lab EC2 Instances to eliminate compute costs..."
echo "=============================================================================="
echo "Region:       $AWS_REGION"
echo "Victim ID:    $VICTIM_ID"
echo "Attacker ID:  $ATTACKER_ID"
echo "Client ID:    $CLIENT_ID"

aws ec2 stop-instances \
    --region "$AWS_REGION" \
    --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
    --output text

echo "⏳ Waiting for instances to reach 'stopped' state..."
aws ec2 wait instance-stopped \
    --region "$AWS_REGION" \
    --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID"

echo "🔍 Verifying instance states..."
aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
    --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' \
    --output table

echo "=============================================================================="
echo "✅ All 3 EC2 instances successfully stopped. No compute charges accruing."
echo "   To power them back on at any time, run: bash infra/restart_lab.sh"
echo "=============================================================================="

