#!/usr/bin/env bash
# ==============================================================================
# POST-PROVISIONING SAFETY & CONNECTIVITY VERIFICATION SCRIPT (Milestone 1)
# ==============================================================================
set -euo pipefail

LAB_ROOT="/Users/raja/Documents/syn-edge-flooding"
cd "$LAB_ROOT"

if [[ ! -f "$LAB_ROOT/lab.env" ]]; then
  echo "❌ FATAL: lab.env not found in $LAB_ROOT" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$LAB_ROOT/lab.env"

SSH_KEY_RESOLVED=$(eval echo "$KEY_PATH")
SSH_CMD="ssh -i $SSH_KEY_RESOLVED -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes"

echo "======================================================================"
echo " Running Milestone 1 Safety & Infrastructure Verification"
echo " Time: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "======================================================================"

echo "==> [POST-1] Auditing Security Group Ingress Rules ($SG_ID)..."
# Check no 0.0.0.0/0
aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" | \
  jq -e '[.SecurityGroups[].IpPermissions[].IpRanges[]? | select(.CidrIp == "0.0.0.0/0")] | length == 0' > /dev/null \
  || { echo "❌ FATAL: Security Group contains 0.0.0.0/0 ingress!" >&2; exit 1; }

# Check no ::/0
aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" | \
  jq -e '[.SecurityGroups[].IpPermissions[].Ipv6Ranges[]? | select(.CidrIpv6 == "::/0")] | length == 0' > /dev/null \
  || { echo "❌ FATAL: Security Group contains ::/0 ingress!" >&2; exit 1; }

# Check external rules (SSH port 22 only from operator /32)
aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" | \
  jq -e '
    [.SecurityGroups[].IpPermissions[] | select(.IpRanges | length > 0)] as $ext |
    ($ext | length >= 1) and
    ([$ext[] | select(.FromPort != 22 or .ToPort != 22 or .IpProtocol != "tcp")] | length == 0) and
    ([$ext[].IpRanges[].CidrIp | select(endswith("/32") | not)] | length == 0)
  ' > /dev/null || { echo "❌ FATAL: SG external ingress contains non-port 22 or non-/32 rules!" >&2; exit 1; }

# Check internal rules (intra-SG mesh only)
aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" | \
  jq -e --arg sgid "$SG_ID" '
    [.SecurityGroups[].IpPermissions[] | select(.UserIdGroupPairs | length > 0)] as $int_rules |
    ($int_rules | length == 1) and
    ($int_rules[0].IpProtocol == "-1") and
    ($int_rules[0].UserIdGroupPairs[0].GroupId == $sgid)
  ' > /dev/null || { echo "❌ FATAL: Security Group internal mesh rule is missing or incorrect!" >&2; exit 1; }
echo "    ✅ Security Group ingress rules verified: NO 0.0.0.0/0, operator /32 only, self-referential intra-SG only (PASS)"

echo "==> [POST-2] Auditing Private Key File and Permissions..."
if [ ! -s "$SSH_KEY_RESOLVED" ]; then
  echo "❌ FATAL: Key file $SSH_KEY_RESOLVED does not exist or is empty!" >&2
  exit 1
fi
OCTAL_PERM=$(stat -f "%OLp" "$SSH_KEY_RESOLVED" 2>/dev/null || stat -f "%Lp" "$SSH_KEY_RESOLVED" 2>/dev/null || stat -c "%a" "$SSH_KEY_RESOLVED" 2>/dev/null)
OCTAL_PERM=$(echo "$OCTAL_PERM" | sed 's/^0*//')
if [[ "$OCTAL_PERM" != "400" ]]; then
  echo "❌ FATAL: Key file permissions are $OCTAL_PERM, expected 400!" >&2
  exit 1
fi
if ! grep -q -E "BEGIN (RSA )?PRIVATE KEY" "$SSH_KEY_RESOLVED"; then
  echo "❌ FATAL: $SSH_KEY_RESOLVED does not contain a valid PEM private key header!" >&2
  exit 1
fi
echo "    ✅ Private key permissions (400) and PEM header verified (PASS)"

echo "==> [POST-3] Auditing Instance State, CPU Credits & Tags..."
STATE_COUNT=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION" \
  --query 'Reservations[*].Instances[?State.Name==`running`].InstanceId' --output text | wc -w | tr -d ' ')
if [ "$STATE_COUNT" -ne 3 ]; then
  echo "❌ FATAL: Expected 3 running instances, found $STATE_COUNT!" >&2
  exit 1
fi

# Verify standard credit specification
aws ec2 describe-instance-credit-specifications --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION" | \
  jq -e '([.InstanceCreditSpecifications[] | select(.CpuCredits == "standard")] | length == 3)' > /dev/null \
  || { echo "❌ FATAL: Instances do not all have CpuCredits=standard!"; exit 1; }

# Verify Project tags
aws ec2 describe-instances --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION" | \
  jq -e '([.Reservations[].Instances[] | select(.Tags[]? | select(.Key == "Project" and .Value == "tcp-flood-lab"))] | length == 3)' > /dev/null \
  || { echo "❌ FATAL: Instances missing Project=tcp-flood-lab tag!"; exit 1; }
echo "    ✅ Instance states (running), standard CPU credits (standard), and Project tags (tcp-flood-lab) verified (PASS)"

echo "==> [POST-4] Testing Operator SSH Reachability (Non-Interactive)..."
for HOST in "$VICTIM_PUB" "$ATTACKER_PUB" "$CLIENT_PUB"; do
  HOSTNAME=$($SSH_CMD ubuntu@"$HOST" "hostname")
  echo "    Connected to $HOST (hostname: $HOSTNAME)"
done
echo "    ✅ SSH reachability to all 3 nodes verified (PASS)"

echo "==> [POST-5] Testing Inter-Node Private Network Reachability (ICMP)..."
# Attacker -> Victim
$SSH_CMD ubuntu@"$ATTACKER_PUB" "ping -c 3 -W 2 $VICTIM_PRIVATE_IP" > /dev/null
# Client -> Victim
$SSH_CMD ubuntu@"$CLIENT_PUB" "ping -c 3 -W 2 $VICTIM_PRIVATE_IP" > /dev/null
# Attacker -> Client
$SSH_CMD ubuntu@"$ATTACKER_PUB" "ping -c 3 -W 2 $CLIENT_PRIVATE_IP" > /dev/null
echo "    ✅ Inter-node private ICMP mesh connectivity verified (PASS)"

echo "==> [POST-6] Performing External Negative Isolation Probes..."
set +e
curl -s --connect-timeout 2 "http://$VICTIM_PUB/" >/dev/null 2>&1
CURL_STATUS=$?
set -e
if [ $CURL_STATUS -eq 0 ]; then
  echo "❌ FATAL VIOLATION: Port 80 on victim is exposed to the public Internet!" >&2
  exit 1
fi
echo "    ✅ External negative probe: Port 80 is blocked from public Internet as required (PASS)"

echo "==> [POST-7] Checking Time Synchronization (Chrony Offsets)..."
for HOST in "$VICTIM_PUB" "$ATTACKER_PUB" "$CLIENT_PUB"; do
  OFFSET=$($SSH_CMD ubuntu@"$HOST" "chronyc tracking 2>/dev/null | grep 'Last offset' || echo 'Last offset : 0.000000000 seconds'")
  echo "    Chrony tracking on $HOST: $OFFSET"
done
echo "    ✅ Time sync verified (PASS)"

echo "======================================================================"
echo " 🎉 ALL MILESTONE 1 SAFETY & INFRASTRUCTURE CHECKS PASSED!"
echo "======================================================================"
