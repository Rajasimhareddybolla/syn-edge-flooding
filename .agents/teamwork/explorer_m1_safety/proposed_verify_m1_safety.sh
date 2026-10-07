#!/usr/bin/env bash
# ==============================================================================
# verify_m1_safety.sh — Milestone 1 Comprehensive Safety & Verification Check
# ==============================================================================
# Usage: bash infra/verify_m1_safety.sh
# Exit codes: 0 = ALL CHECKS PASS, 1 = FATAL VIOLATION DETECTED
# ==============================================================================
set -euo pipefail

LAB_ENV_PATH="${LAB_ENV_PATH:-lab.env}"

if [ ! -f "$LAB_ENV_PATH" ]; then
  echo "FATAL: lab.env not found at '$LAB_ENV_PATH'!" >&2
  exit 1
fi

# Load environment
# shellcheck source=/dev/null
source "$LAB_ENV_PATH"

FAILED=0

fail() {
  echo "❌ FATAL: $1" >&2
  FAILED=1
}

pass() {
  echo "✅ PASS: $1"
}

info() {
  echo "==> $1"
}

echo "========================================================================"
echo "MILESTONE 1 SAFETY & VERIFICATION HARNESS"
echo "Target Region: ${AWS_REGION:-unknown}"
echo "Security Group: ${SG_ID:-unknown}"
echo "Key Path: ${KEY_PATH:-unknown}"
echo "========================================================================"

# ------------------------------------------------------------------------------
# 1. Security Group Ingress Verification
# ------------------------------------------------------------------------------
info "[CHECK 1] Auditing Security Group Ingress Rules ($SG_ID)..."

SG_JSON=$(aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" --output json)

# 1a. Check NO 0.0.0.0/0 ingress
HAS_ZERO_IPV4=$(echo "$SG_JSON" | jq '[.SecurityGroups[].IpPermissions[].IpRanges[]? | select(.CidrIp == "0.0.0.0/0")] | length')
if [ "$HAS_ZERO_IPV4" -ne 0 ]; then
  fail "Security Group contains 0.0.0.0/0 ingress rules ($HAS_ZERO_IPV4 found)!"
else
  pass "No 0.0.0.0/0 ingress detected in $SG_ID."
fi

# 1b. Check NO ::/0 ingress
HAS_ZERO_IPV6=$(echo "$SG_JSON" | jq '[.SecurityGroups[].IpPermissions[].Ipv6Ranges[]? | select(.CidrIpv6 == "::/0")] | length')
if [ "$HAS_ZERO_IPV6" -ne 0 ]; then
  fail "Security Group contains ::/0 ingress rules ($HAS_ZERO_IPV6 found)!"
else
  pass "No ::/0 ingress detected in $SG_ID."
fi

# 1c. Resolve current operator IP and check port 22 restriction
MYIP=$(curl -s --connect-timeout 5 https://checkip.amazonaws.com | tr -d '[:space:]')
if ! [[ "$MYIP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
  fail "Unable to resolve valid public operator IPv4: got '$MYIP'"
else
  EXT_RULE_CHECK=$(echo "$SG_JSON" | jq --arg myip "${MYIP}/32" '
    [.SecurityGroups[].IpPermissions[] | select(.IpRanges | length > 0)] as $ext |
    ($ext | length == 1) and
    ($ext[0].FromPort == 22) and
    ($ext[0].ToPort == 22) and
    ($ext[0].IpProtocol == "tcp") and
    ($ext[0].IpRanges | length == 1) and
    ($ext[0].IpRanges[0].CidrIp == $myip)
  ')
  if [ "$EXT_RULE_CHECK" = "true" ]; then
    pass "External ingress strictly confined to operator ${MYIP}/32 on port 22."
  else
    fail "External ingress rules do not match operator ${MYIP}/32 on port 22!"
  fi
fi

# 1d. Check intra-SG mesh rule
INT_RULE_CHECK=$(echo "$SG_JSON" | jq --arg sgid "$SG_ID" '
  [.SecurityGroups[].IpPermissions[] | select(.UserIdGroupPairs | length > 0)] as $int |
  ($int | length == 1) and
  ($int[0].IpProtocol == "-1") and
  ($int[0].UserIdGroupPairs[0].GroupId == $sgid)
')
if [ "$INT_RULE_CHECK" = "true" ]; then
  pass "Intra-SG mesh rule strictly allows all protocols from $SG_ID to itself."
else
  fail "Intra-SG mesh rule is missing or not configured correctly!"
fi

# ------------------------------------------------------------------------------
# 2. SSH Key Permissions and Git Isolation Verification
# ------------------------------------------------------------------------------
info "[CHECK 2] Auditing SSH Private Key Permissions & Git Hygiene..."

if [ ! -f "$KEY_PATH" ]; then
  fail "Key file '$KEY_PATH' does not exist!"
elif [ ! -s "$KEY_PATH" ]; then
  fail "Key file '$KEY_PATH' is empty!"
else
  OCTAL_PERM=$(stat -f "%OLp" "$KEY_PATH" 2>/dev/null || stat -c "%a" "$KEY_PATH" 2>/dev/null)
  if [ "$OCTAL_PERM" = "400" ]; then
    pass "Key file $KEY_PATH has strictly locked permission 400."
  else
    fail "Key file $KEY_PATH has permission $OCTAL_PERM (expected 400)!"
  fi
fi

# Check git exclusion
if command -v git >/dev/null 2>&1 && [ -d .git ]; then
  if git check-ignore -q "$LAB_ENV_PATH"; then
    pass "lab.env is properly gitignored."
  else
    fail "lab.env is NOT ignored by git!"
  fi

  if git check-ignore -q "sample.pem"; then
    pass "*.pem pattern is properly gitignored."
  else
    fail "*.pem is NOT ignored by git!"
  fi
fi

# ------------------------------------------------------------------------------
# 3. Instance Configuration, CPU Credits & Resource Tags
# ------------------------------------------------------------------------------
info "[CHECK 3] Auditing EC2 Instances ($VICTIM_ID, $ATTACKER_ID, $CLIENT_ID)..."

INSTANCES_JSON=$(aws ec2 describe-instances \
  --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
  --region "$AWS_REGION" \
  --output json)

# 3a. Check running state
RUNNING_COUNT=$(echo "$INSTANCES_JSON" | jq '[.Reservations[].Instances[] | select(.State.Name == "running")] | length')
if [ "$RUNNING_COUNT" -eq 3 ]; then
  pass "All 3 instances are in 'running' state."
else
  fail "Expected 3 running instances, found $RUNNING_COUNT running."
fi

# 3b. Check CPU Credit Specification (must be standard)
CREDIT_JSON=$(aws ec2 describe-instance-credit-specifications \
  --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
  --region "$AWS_REGION" \
  --output json)

STANDARD_CREDITS=$(echo "$CREDIT_JSON" | jq '[.InstanceCreditSpecifications[] | select(.CpuCredits == "standard")] | length')
if [ "$STANDARD_CREDITS" -eq 3 ]; then
  pass "All 3 instances configured with CpuCredits=standard (zero burst charge risk)."
else
  fail "Non-standard CPU credit specifications detected! (Only $STANDARD_CREDITS/3 are standard)"
fi

# 3c. Check Resource Tags
PROJECT_TAG_COUNT=$(echo "$INSTANCES_JSON" | jq '[.Reservations[].Instances[].Tags[]? | select(.Key == "Project" and .Value == "tcp-flood-lab")] | length')
if [ "$PROJECT_TAG_COUNT" -eq 3 ]; then
  pass "All 3 instances tagged with Project=tcp-flood-lab."
else
  fail "Missing Project=tcp-flood-lab tag on one or more instances ($PROJECT_TAG_COUNT/3 tagged)!"
fi

# 3d. Check AZ alignment (must all be in ap-south-1a)
AZ_COUNT=$(echo "$INSTANCES_JSON" | jq '[.Reservations[].Instances[].Placement.AvailabilityZone | select(. == "ap-south-1a")] | length')
if [ "$AZ_COUNT" -eq 3 ]; then
  pass "All 3 instances co-located in ap-south-1a (zero cross-AZ latency jitter)."
else
  fail "Instances are placed in mismatched Availability Zones!"
fi

# ------------------------------------------------------------------------------
# 4. SSH Reachability & Non-Interactive Command Execution
# ------------------------------------------------------------------------------
info "[CHECK 4] Testing SSH Connectivity (Non-Interactive)..."

SSH_OPTS="-i $KEY_PATH -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=~/.ssh/known_hosts_tcp_flood_lab -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes"

for NODE in "victim:$VICTIM_PUB" "attacker:$ATTACKER_PUB" "client:$CLIENT_PUB"; do
  NAME="${NODE%%:*}"
  PUB_IP="${NODE##*:}"
  if ssh $SSH_OPTS ubuntu@"$PUB_IP" "hostname" >/dev/null 2>&1; then
    pass "SSH connection to $NAME ($PUB_IP) succeeded."
  else
    fail "SSH connection to $NAME ($PUB_IP) timed out or failed!"
  fi
done

# ------------------------------------------------------------------------------
# 5. Inter-Node Private ICMP Mesh Reachability
# ------------------------------------------------------------------------------
info "[CHECK 5] Testing Inter-Node Private ICMP Mesh..."

if ssh $SSH_OPTS ubuntu@"$ATTACKER_PUB" "ping -c 3 -W 2 $VICTIM_PRIVATE_IP" >/dev/null 2>&1; then
  pass "Attacker -> Victim private ping succeeded."
else
  fail "Attacker cannot reach Victim on private IP $VICTIM_PRIVATE_IP!"
fi

if ssh $SSH_OPTS ubuntu@"$CLIENT_PUB" "ping -c 3 -W 2 $VICTIM_PRIVATE_IP" >/dev/null 2>&1; then
  pass "Client -> Victim private ping succeeded."
else
  fail "Client cannot reach Victim on private IP $VICTIM_PRIVATE_IP!"
fi

if ssh $SSH_OPTS ubuntu@"$ATTACKER_PUB" "ping -c 3 -W 2 $CLIENT_PRIVATE_IP" >/dev/null 2>&1; then
  pass "Attacker -> Client private ping succeeded."
else
  fail "Attacker cannot reach Client on private IP $CLIENT_PRIVATE_IP!"
fi

# ------------------------------------------------------------------------------
# 6. External Exposure Negative Verification
# ------------------------------------------------------------------------------
info "[CHECK 6] Testing External Negative Exposure (Verifying Port 80 Blocked)..."

# Attempting HTTP connection to victim public IP from local machine
set +e
curl --connect-timeout 3 -s "http://$VICTIM_PUB/" >/dev/null 2>&1
CURL_CODE=$?
set -e

if [ "$CURL_CODE" -ne 0 ]; then
  pass "External HTTP probe to $VICTIM_PUB correctly blocked/timed out."
else
  fail "Port 80 on $VICTIM_PUB is reachable from the public Internet (UNEXPECTED LEAK)!"
fi

echo "========================================================================"
if [ "$FAILED" -eq 0 ]; then
  echo "🎉 ALL MILESTONE 1 SAFETY AND VERIFICATION CHECKS PASSED!"
  exit 0
else
  echo "🚨 MILESTONE 1 VERIFICATION FAILED: SEE LOGS ABOVE."
  exit 1
fi
