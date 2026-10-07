#!/usr/bin/env bash
# ==============================================================================
# MILESTONE 1 PROVISIONING SCRIPT: Preflight & AWS Infrastructure Provisioning
# ==============================================================================
set -euo pipefail

LAB_ROOT="/Users/raja/Documents/syn-edge-flooding"
cd "$LAB_ROOT"

echo "======================================================================"
echo " Starting Milestone 1: Preflight & AWS Infrastructure Provisioning"
echo " Time: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "======================================================================"

# 1. Environment & Network Parameters
AWS_REGION="ap-south-1"
VPC_ID="vpc-091281d6eb74da886"
SUBNET_ID="subnet-0709c5a163cc423bb"
AMI_ID="ami-065d2b03fb493085a"
KEY_NAME="tcp-flood-lab"
KEY_PATH="$HOME/.ssh/tcp-flood-lab.pem"
SG_NAME="lab-sg"

# 2. Preflight Safety Check
echo "[Step 1/8] Verifying AWS Identity and Operator Public IP..."
CALLER_IDENTITY=$(aws sts get-caller-identity --output json)
echo "Authenticated Principal: $(echo "$CALLER_IDENTITY" | jq -r '.Arn')"

MYIP=$(curl -4 -s https://checkip.amazonaws.com | tr -d '[:space:]' || curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
if ! [[ "$MYIP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
  echo "❌ Error: Failed to resolve valid operator IPv4 address: '$MYIP'" >&2
  exit 1
fi
echo "✅ Operator IP verified: $MYIP/32"

# 3. Key Pair Setup
echo "[Step 2/8] Provisioning EC2 Key Pair ($KEY_NAME)..."
mkdir -p ~/.ssh && chmod 700 ~/.ssh

KEY_EXISTS=$(aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$AWS_REGION" --query 'KeyPairs[0].KeyName' --output text 2>/dev/null || echo "None")

if [[ "$KEY_EXISTS" == "$KEY_NAME" ]]; then
  echo "ℹ️ Key pair $KEY_NAME already exists in AWS."
  if [[ ! -s "$KEY_PATH" ]]; then
    echo "⚠️ Key exists in AWS but local file $KEY_PATH is missing. Recreating key pair..."
    aws ec2 delete-key-pair --key-name "$KEY_NAME" --region "$AWS_REGION"
    KEY_EXISTS="None"
  fi
fi

if [[ "$KEY_EXISTS" != "$KEY_NAME" ]]; then
  echo "Creating new key pair $KEY_NAME..."
  aws ec2 create-key-pair \
    --key-name "$KEY_NAME" \
    --key-type rsa \
    --key-format pem \
    --tag-specifications "ResourceType=key-pair,Tags=[{Key=Name,Value=$KEY_NAME},{Key=Project,Value=tcp-flood-lab}]" \
    --region "$AWS_REGION" \
    --query 'KeyMaterial' \
    --output text > "$KEY_PATH"
  chmod 400 "$KEY_PATH"
  echo "✅ Key pair created and saved to $KEY_PATH (chmod 400)"
else
  chmod 400 "$KEY_PATH"
  echo "✅ Local key file verified at $KEY_PATH (chmod 400)"
fi

aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$AWS_REGION" --output json > "$LAB_ROOT/infra/key_pair.json"

# 4. Security Group Setup & Lockdown
echo "[Step 3/8] Provisioning Security Group ($SG_NAME)..."
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
  --region "$AWS_REGION" \
  --query 'SecurityGroups[0].GroupId' \
  --output text 2>/dev/null || echo "None")

if [[ "$SG_ID" == "None" || -z "$SG_ID" ]]; then
  echo "Creating Security Group $SG_NAME in VPC $VPC_ID..."
  SG_ID=$(aws ec2 create-security-group \
    --group-name "$SG_NAME" \
    --description "TCP Flood Lab SG - Restricted to operator /32 SSH and intra-SG mesh" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$SG_NAME},{Key=Project,Value=tcp-flood-lab}]" \
    --region "$AWS_REGION" \
    --query 'GroupId' \
    --output text)
  echo "Created SG ID: $SG_ID"
fi

aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" --output json > "$LAB_ROOT/infra/sg_create.json"

echo "Configuring Security Group ingress rules..."
# Ingress Rule 1: Allow SSH strictly from operator /32
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 22 \
  --cidr "${MYIP}/32" \
  --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=operator-ssh},{Key=Project,Value=tcp-flood-lab}]" \
  --region "$AWS_REGION" 2>/dev/null || echo "SSH ingress rule already authorized."

# Ingress Rule 2: Intra-SG mesh
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol -1 \
  --source-group "$SG_ID" \
  --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=intra-lab-mesh},{Key=Project,Value=tcp-flood-lab}]" \
  --region "$AWS_REGION" 2>/dev/null || echo "Intra-SG mesh ingress rule already authorized."

aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" --output json > "$LAB_ROOT/infra/sg_described.json"

# Strict safety verification: zero 0.0.0.0/0
PUBLIC_RULES=$(aws ec2 describe-security-groups \
  --group-ids "$SG_ID" \
  --region "$AWS_REGION" \
  --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' \
  --output text)

if [[ -n "$PUBLIC_RULES" ]]; then
  echo "❌ CRITICAL SAFETY ERROR: Public rule 0.0.0.0/0 or ::/0 detected in $SG_ID!" >&2
  exit 1
fi
echo "✅ Security Group lockdown verified: zero 0.0.0.0/0 exposure."

# 5. EC2 Instances Launch
echo "[Step 4/8] Provisioning EC2 instances in $SUBNET_ID ($AWS_REGION)..."

VICTIM_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=tcp-flood-lab" "Name=tag:Name,Values=victim" "Name=instance-state-name,Values=pending,running" \
  --region "$AWS_REGION" --query 'Reservations[0].Instances[0].InstanceId' --output text 2>/dev/null || echo "None")

if [[ "$VICTIM_ID" == "None" || -z "$VICTIM_ID" ]]; then
  echo "Launching victim instance..."
  VICTIM_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type t3.micro \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --subnet-id "$SUBNET_ID" \
    --credit-specification CpuCredits=standard \
    --associate-public-ip-address \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=victim},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=victim}]" "ResourceType=volume,Tags=[{Key=Name,Value=victim-root},{Key=Project,Value=tcp-flood-lab}]" \
    --region "$AWS_REGION" \
    --query 'Instances[0].InstanceId' \
    --output text)
fi

ATTACKER_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=tcp-flood-lab" "Name=tag:Name,Values=attacker" "Name=instance-state-name,Values=pending,running" \
  --region "$AWS_REGION" --query 'Reservations[0].Instances[0].InstanceId' --output text 2>/dev/null || echo "None")

if [[ "$ATTACKER_ID" == "None" || -z "$ATTACKER_ID" ]]; then
  echo "Launching attacker instance..."
  ATTACKER_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type t3.micro \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --subnet-id "$SUBNET_ID" \
    --credit-specification CpuCredits=standard \
    --associate-public-ip-address \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=attacker},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=attacker}]" "ResourceType=volume,Tags=[{Key=Name,Value=attacker-root},{Key=Project,Value=tcp-flood-lab}]" \
    --region "$AWS_REGION" \
    --query 'Instances[0].InstanceId' \
    --output text)
fi

CLIENT_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=tcp-flood-lab" "Name=tag:Name,Values=client" "Name=instance-state-name,Values=pending,running" \
  --region "$AWS_REGION" --query 'Reservations[0].Instances[0].InstanceId' --output text 2>/dev/null || echo "None")

if [[ "$CLIENT_ID" == "None" || -z "$CLIENT_ID" ]]; then
  echo "Launching client instance..."
  CLIENT_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type t3.micro \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --subnet-id "$SUBNET_ID" \
    --credit-specification CpuCredits=standard \
    --associate-public-ip-address \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=client},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=client}]" "ResourceType=volume,Tags=[{Key=Name,Value=client-root},{Key=Project,Value=tcp-flood-lab}]" \
    --region "$AWS_REGION" \
    --query 'Instances[0].InstanceId' \
    --output text)
fi

echo "Identified Instance IDs:"
echo "  Victim:   $VICTIM_ID"
echo "  Attacker: $ATTACKER_ID"
echo "  Client:   $CLIENT_ID"

# 6. Wait for Instances
echo "[Step 5/8] Waiting for instances to become running and healthy..."
aws ec2 wait instance-running --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION"
echo "✅ All 3 instances are running."

echo "Waiting for 2/2 status checks ok..."
aws ec2 wait instance-status-ok --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION"
echo "✅ All 3 instances passed status checks."

aws ec2 describe-instances --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION" --output json > "$LAB_ROOT/infra/instances_described.json"

# 7. Extract IPs and Generate lab.env
echo "[Step 6/8] Extracting IP topology and generating lab.env..."
VICTIM_PUB=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
VICTIM_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

ATTACKER_PUB=$(aws ec2 describe-instances --instance-ids "$ATTACKER_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
ATTACKER_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$ATTACKER_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

CLIENT_PUB=$(aws ec2 describe-instances --instance-ids "$CLIENT_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
CLIENT_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$CLIENT_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

echo "IP Topology:"
echo "  Victim:   Public=$VICTIM_PUB, Private=$VICTIM_PRIVATE_IP"
echo "  Attacker: Public=$ATTACKER_PUB, Private=$ATTACKER_PRIVATE_IP"
echo "  Client:   Public=$CLIENT_PUB, Private=$CLIENT_PRIVATE_IP"

SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=15 -o IdentitiesOnly=yes)

echo "Detecting primary network interface on victim..."
VICTIM_IFACE=$(ssh "${SSH_OPTS[@]}" ubuntu@"$VICTIM_PUB" "ip -o -4 route show to default | awk '{print \$5}'" 2>/dev/null || echo "ens5")
if [[ -z "$VICTIM_IFACE" ]]; then
  VICTIM_IFACE="ens5"
fi
echo "Discovered VICTIM_IFACE: $VICTIM_IFACE"

# Record host telemetry details
ssh "${SSH_OPTS[@]}" ubuntu@"$VICTIM_PUB" "hostname; ip -br a; timedatectl" > "$LAB_ROOT/infra/victim_info.txt" 2>/dev/null || true
ssh "${SSH_OPTS[@]}" ubuntu@"$ATTACKER_PUB" "hostname; ip -br a; timedatectl" > "$LAB_ROOT/infra/attacker_info.txt" 2>/dev/null || true
ssh "${SSH_OPTS[@]}" ubuntu@"$CLIENT_PUB" "hostname; ip -br a; timedatectl" > "$LAB_ROOT/infra/client_info.txt" 2>/dev/null || true

cat << ENV_EOF > "$LAB_ROOT/lab.env"
# ==============================================================================
# lab.env — TCP Flooding Detection Research Lab Environment Configuration
# Generated by Milestone 1 Infrastructure Provisioning
# DO NOT COMMIT TO VERSION CONTROL (Enforced by .gitignore)
# ==============================================================================

export AWS_REGION="${AWS_REGION}"
export VPC_ID="${VPC_ID}"
export SG_ID="${SG_ID}"
export KEY_NAME="${KEY_NAME}"
export KEY_PATH="${KEY_PATH}"

export VICTIM_ID="${VICTIM_ID}"
export ATTACKER_ID="${ATTACKER_ID}"
export CLIENT_ID="${CLIENT_ID}"

export VICTIM_PUB="${VICTIM_PUB}"
export ATTACKER_PUB="${ATTACKER_PUB}"
export CLIENT_PUB="${CLIENT_PUB}"

export VICTIM_PRIVATE_IP="${VICTIM_PRIVATE_IP}"
export ATTACKER_PRIVATE_IP="${ATTACKER_PRIVATE_IP}"
export CLIENT_PRIVATE_IP="${CLIENT_PRIVATE_IP}"

export VICTIM_IFACE="${VICTIM_IFACE}"
ENV_EOF

chmod 600 "$LAB_ROOT/lab.env"
echo "✅ lab.env written with 15 mandatory variables."

# Validate lab.env
bash "$LAB_ROOT/tools/validate_lab_env.sh" "$LAB_ROOT/lab.env"

# 8. Private Ping Verification
echo "[Step 7/8] Verifying private ICMP connectivity across lab-sg mesh..."
CLIENT_PING=$(ssh "${SSH_OPTS[@]}" ubuntu@"$CLIENT_PUB" "ping -c 3 $VICTIM_PRIVATE_IP")
ATTACKER_PING=$(ssh "${SSH_OPTS[@]}" ubuntu@"$ATTACKER_PUB" "ping -c 3 $VICTIM_PRIVATE_IP")

cat << PING_EOF > "$LAB_ROOT/infra/ping_verification.txt"
=== Client -> Victim Private IP ICMP Ping ($VICTIM_PRIVATE_IP) ===
$CLIENT_PING

=== Attacker -> Victim Private IP ICMP Ping ($VICTIM_PRIVATE_IP) ===
$ATTACKER_PING
PING_EOF
echo "✅ Private ICMP ping verified and saved to infra/ping_verification.txt"

# 9. Update State & Ledger
echo "[Step 8/8] Updating STATE.md and LAB_LOG.md..."
sed -i '' 's/Status:\ IN_PROGRESS/Status:\ COMPLETE/g' "$LAB_ROOT/STATE.md" 2>/dev/null || sed -i 's/Status:\ IN_PROGRESS/Status:\ COMPLETE/g' "$LAB_ROOT/STATE.md" 2>/dev/null || true

cat << LOG_EOF >> "$LAB_ROOT/LAB_LOG.md"

## [$(date -u +"%Y-%m-%dT%H:%M:%SZ")] — RESOURCE_ALLOCATION: AWS Infrastructure Provisioned
- **Phase:** Phase 1 (Infrastructure Provisioning)
- **Agent / Actor:** worker_m1
- **Category:** [RESOURCE_ALLOCATION]
- **Description:** Provisioned Security Group $SG_ID (/32 SSH only), Key Pair $KEY_NAME, and 3 t3.micro instances (victim=$VICTIM_ID, attacker=$ATTACKER_ID, client=$CLIENT_ID) in $SUBNET_ID with CpuCredits=standard.
- **Rationale / Justification:** Establishing physical multi-node isolated research testbed for Milestone 1.
- **Evidence Artifacts:** infra/sg_described.json, infra/instances_described.json, lab.env, infra/ping_verification.txt.
- **Impact Analysis:** Testbed is fully operational and safely locked down.
- **Human Authorization:** Covered under Gate G1 approval.
LOG_EOF

echo "======================================================================"
echo " Milestone 1 Provisioning Script Completed Successfully!"
echo "======================================================================"

