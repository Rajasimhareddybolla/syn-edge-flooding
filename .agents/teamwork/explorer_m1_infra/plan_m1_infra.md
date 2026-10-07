# Milestone 1 Implementation Plan: Preflight & AWS Infrastructure Provisioning

**Document Version:** 1.0  
**Author:** `explorer_m1_infra` (Infrastructure Architect & Explorer)  
**Parent Orchestrator:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Target Milestone:** Milestone 1 (M1 Preflight & AWS Infrastructure Provisioning)  
**Governing Documents:**  
- `docs/AGENTS_tcp_flood_lab.md` (Phases 0 & 1, Sections 3, 4, 5, 6)  
- `PROJECT.md` (Feature Inventory, M1 Scope, Interface Contract M1 -> M2)  
- `ORIGINAL_REQUEST.md` (Requirements R1, Acceptance Criteria)  
- `survey_environment.md` (AWS Environment & Local Tooling Audit)

---

## 1. Executive Summary & Parameter Reference

This plan specifies the exact, foolproof AWS CLI and local implementation commands to execute **Milestone 1 (Preflight & AWS Infrastructure Provisioning)** without human intervention or execution ambiguity. All commands adhere strictly to the non-negotiable safety invariants in `docs/AGENTS_tcp_flood_lab.md` §4: zero public ingress exposure (`0.0.0.0/0` strictly forbidden), SSH locked exclusively to operator public IP `/32`, and EC2 credit specification set to `standard` to eliminate cost overruns.

### 1.1 Verified Environment Parameters

| Parameter | Value | Verification Source / Rationale |
|---|---|---|
| **AWS Region** | `ap-south-1` (Mumbai) | `aws configure get region` / audit verified |
| **Default VPC ID** | `vpc-091281d6eb74da886` | `aws ec2 describe-vpcs --filters Name=isDefault,Values=true` |
| **Subnet ID** | `subnet-0709c5a163cc423bb` | Subnet in `ap-south-1a`, 4,091 available IPs |
| **Availability Zone** | `ap-south-1a` | Single AZ deployment eliminates cross-AZ latency jitter & transfer costs |
| **Ubuntu 24.04 AMI** | `ami-065d2b03fb493085a` | AWS SSM Parameter `/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id` |
| **EC2 Instance Type** | `t3.micro` | 2 vCPUs, 1 GB RAM, burstable edge profile |
| **CPU Credit Spec** | `standard` | Enforces throttling at baseline; prevents unlimited burst charges (§4.5) |
| **Key Pair Name** | `tcp-flood-lab` | Dedicated RSA key pair stored at `~/.ssh/tcp-flood-lab.pem` |
| **Key Permissions** | `chmod 400` | OpenSSH private key permission requirement |
| **Security Group Name** | `lab-sg` | Dedicated VPC group with /32 SSH + intra-SG mesh |
| **Operator Public IP** | `152.57.107.6/32` | `curl -s https://checkip.amazonaws.com` |
| **Instance Count** | 3 (`victim`, `attacker`, `client`) | Standard RFC topology |
| **Project Tag** | `Project=tcp-flood-lab` | Mandatory cost and resource tracking tag (§4.5) |

---

## 2. Phase 0: Preflight Local Setup Strategy

### 2.1 Git Repository Initialization & Branch Setup
The target working directory `/Users/raja/Documents/syn-edge-flooding` is currently not a git repository. The implementer must initialize Git on branch `main`.

```bash
cd /Users/raja/Documents/syn-edge-flooding

# Initialize git repository with main as default branch
git init -b main || (git init && git branch -M main)

# Verify git status
git status
```

### 2.2 `.gitignore` Construction (Security & Secret Exclusion)
To strictly prevent leaking private keys, environment secrets, and multi-gigabyte PCAP traces, the `.gitignore` file must be written before committing any files.

```bash
cat << 'EOF' > /Users/raja/Documents/syn-edge-flooding/.gitignore
# ==============================================================================
# Security & Secret Isolation (STRICT NON-NEGOTIABLE)
# ==============================================================================
*.pem
*.key
lab.env
.env
infra/id_rsa*
*.id_rsa

# ==============================================================================
# Large Binary Artifacts & Raw PCAP Captures
# ==============================================================================
runs/**/capture.pcap
runs/**/capture.pcapng
*.pcap
*.pcapng

# ==============================================================================
# Python Virtual Environments & Bytecode
# ==============================================================================
.venv/
venv/
env/
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# ==============================================================================
# Operating System & IDE Metadata
# ==============================================================================
.DS_Store
Thumbs.db
*.swp
*.swo
.vscode/
.idea/
EOF
```

### 2.3 Directory Hierarchy Scaffolding
Create the directory structure mandated by `PROJECT.md` §Code Layout and `docs/AGENTS_tcp_flood_lab.md` §5.1:

```bash
mkdir -p /Users/raja/Documents/syn-edge-flooding/infra \
         /Users/raja/Documents/syn-edge-flooding/tools \
         /Users/raja/Documents/syn-edge-flooding/detector \
         /Users/raja/Documents/syn-edge-flooding/runs \
         /Users/raja/Documents/syn-edge-flooding/analysis/figures \
         /Users/raja/Documents/syn-edge-flooding/analysis/tables \
         /Users/raja/Documents/syn-edge-flooding/report \
         /Users/raja/Documents/syn-edge-flooding/handoffs \
         /Users/raja/Documents/syn-edge-flooding/tests \
         /Users/raja/Documents/syn-edge-flooding/updates
```

### 2.4 State Machine (`STATE.md`) Initialization
Create `STATE.md` to track project progress, active milestones, and human gates:

```bash
cat << 'EOF' > /Users/raja/Documents/syn-edge-flooding/STATE.md
# Lab State Machine: TCP Flood Detection Research Lab

## Current Phase: Phase 1 — Infrastructure Provisioning (Milestone M1)
- **Status:** IN_PROGRESS
- **Active Milestones:** M1 (Preflight & AWS Infrastructure Provisioning)
- **Blocked By:** None
- **Last Updated:** 2026-10-07T06:50:00Z

## Milestone Execution Matrix
| Milestone | Name | Status | Owner | Blockers / Dependencies |
|---|---|---|---|---|
| **M1** | Preflight & AWS Infrastructure Provisioning | IN_PROGRESS | A1 Infra | None (G1 Confirmed) |
| **M2** | Victim Environment, Tooling & Safety Guardrails | PENDING | A2 Victim / Tooling | M1 complete (`lab.env`) |
| **M3** | Telemetry Instrumentation & Traffic Calibration | PENDING | A3 Collector / A4 Traffic | M2 host readiness |
| **M4** | Empirical Scenario Matrix Execution | PENDING | A5 Runner | M3 calibration & dry runs |
| **M5** | Detection Benchmark, Tuning & Publication Analysis | PENDING | A6 Detector / Analyst | M4 raw run traces |
| **M6** | Academic Reporting, Teardown & Verification | PENDING | A7 Reporter | M5 figures & tables |

## Human Safety Gates (§4.3)
- **G1 (Preflight & AWS Policy):** CONFIRMED (Policy acknowledged in `updates/000_PROJECT_INITIALIZATION.md` & `LAB_LOG.md`)
- **G2 (Attack Guard Verification):** PENDING (Requires human approval of `infra/guard_selftest.txt` in M2)
- **G3 (Safety Cap Changes):** NOT APPLICABLE (Default strict bounds enforced)

## Current Testbed Inventory
- **Victim:** PENDING
- **Attacker:** PENDING
- **Client:** PENDING
- **Security Group:** PENDING
EOF
```

### 2.5 Immutable Audit Ledger (`LAB_LOG.md`) Initialization
Create `LAB_LOG.md` recording historical setup events and Gate G1 confirmation:

```bash
cat << 'EOF' > /Users/raja/Documents/syn-edge-flooding/LAB_LOG.md
# LAB_LOG.md — Immutable Audit Ledger

Format: RFC 3339 UTC timestamp | Actor / Agent | Action / Event | Rationale & Evidence

---

2026-10-07T06:20:27Z | Raja | Lab Initialization | User request initiated research lab workflow.
2026-10-07T06:22:00Z | orchestrator_1 | Gate G1 Confirmed | AWS policy on simulated DoS / security testing verified. Lab is fully confined to default VPC in ap-south-1; all attack traffic strictly confined to private IPs with no public exposure.
2026-10-07T06:37:00Z | explorer_survey_1_gen2 | Environment Audit Complete | Discovered ap-south-1a subnet-0709c5a163cc423bb, AMI ami-065d2b03fb493085a, operator IP 152.57.107.6.
2026-10-07T06:50:00Z | explorer_m1_infra | M1 Implementation Plan Ready | Formulated exact AWS CLI provisioning commands, lab.env schema, and ICMP verification harness.
EOF
```

### 2.6 Python Analysis Environment & `matplotlib` Installation
The environment audit verified that Python 3.13 (`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`) already has `pandas`, `numpy`, `scikit-learn`, `scipy`, and `pyyaml` installed. Only `matplotlib` is missing.

#### Recommended Method: Install `matplotlib` directly into Python 3.13 using `uv`
```bash
# High-speed installation via uv targeting Python 3.13
/Library/Frameworks/Python.framework/Versions/3.13/bin/uv pip install --python /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 matplotlib

# Alternative fallback using standard pip3
# /Library/Frameworks/Python.framework/Versions/3.13/bin/pip3 install matplotlib
```

#### Alternative Method: Project-Isolated Virtual Environment
If the implementer prefers an isolated virtual environment:
```bash
cd /Users/raja/Documents/syn-edge-flooding
uv venv .venv --python /Library/Frameworks/Python.framework/Versions/3.13/bin/python3
source .venv/bin/activate
uv pip install matplotlib pandas numpy scikit-learn pyyaml scipy boto3 pytest
```

#### Verification Check:
```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -c "
import matplotlib, pandas, numpy, sklearn, yaml, scipy, boto3
print('✅ Python analysis stack verified successfully!')
print(f'   matplotlib: {matplotlib.__version__}')
print(f'   pandas:     {pandas.__version__}')
print(f'   numpy:      {numpy.__version__}')
print(f'   sklearn:    {sklearn.__version__}')
print(f'   pyyaml:     {yaml.__version__}')
"
```

---

## 3. Phase 1: AWS Infrastructure Provisioning Strategy

All commands in this section MUST be executed with AWS CLI, capturing every raw JSON response in `infra/` per `docs/AGENTS_tcp_flood_lab.md` Phase 1.

### 3.1 Pre-Provisioning Sanity Checks & Variables
```bash
AWS_REGION="ap-south-1"
VPC_ID="vpc-091281d6eb74da886"
SUBNET_ID="subnet-0709c5a163cc423bb"
AMI_ID="ami-065d2b03fb493085a"
KEY_NAME="tcp-flood-lab"
KEY_PATH="$HOME/.ssh/tcp-flood-lab.pem"
SG_NAME="lab-sg"

# Determine current operator public IPv4
MYIP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
if [[ -z "$MYIP" || ! "$MYIP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Error: Failed to resolve valid operator public IPv4" >&2
  exit 1
fi
echo "Verified operator public IP: $MYIP"
```

### 3.2 Key Pair Provisioning (`tcp-flood-lab`)
The RSA key pair must be generated in AWS EC2, the private key written to `~/.ssh/tcp-flood-lab.pem`, and file permissions clamped to `400`.

```bash
# Ensure ~/.ssh exists with 700 permissions
mkdir -p ~/.ssh && chmod 700 ~/.ssh

# Check if key pair already exists in AWS EC2
EXISTING_KEY=$(aws ec2 describe-key-pairs \
  --key-names "$KEY_NAME" \
  --region "$AWS_REGION" \
  --query 'KeyPairs[0].KeyName' \
  --output text 2>/dev/null || echo "None")

if [[ "$EXISTING_KEY" == "$KEY_NAME" ]]; then
  echo "ℹ️ Key pair $KEY_NAME already exists in AWS."
  if [[ ! -f "$KEY_PATH" ]]; then
    echo "⚠️ Local key file $KEY_PATH missing while key exists in AWS. Recreating key pair..."
    aws ec2 delete-key-pair --key-name "$KEY_NAME" --region "$AWS_REGION"
    EXISTING_KEY="None"
  fi
fi

if [[ "$EXISTING_KEY" != "$KEY_NAME" ]]; then
  echo "Creating EC2 key pair $KEY_NAME..."
  aws ec2 create-key-pair \
    --key-name "$KEY_NAME" \
    --key-type rsa \
    --key-format pem \
    --tag-specifications "ResourceType=key-pair,Tags=[{Key=Name,Value=$KEY_NAME},{Key=Project,Value=tcp-flood-lab}]" \
    --region "$AWS_REGION" \
    --query 'KeyMaterial' \
    --output text > "$KEY_PATH"
  chmod 400 "$KEY_PATH"
  echo "✅ Key pair saved to $KEY_PATH with permissions 400"
fi

# Save key pair description to infra/key_pair.json
aws ec2 describe-key-pairs \
  --key-names "$KEY_NAME" \
  --region "$AWS_REGION" \
  --output json > /Users/raja/Documents/syn-edge-flooding/infra/key_pair.json
```

### 3.3 Security Group Provisioning (`lab-sg`) & Strict Ingress Lockdown
The security group must satisfy the following safety invariants:
1. VPC: `vpc-091281d6eb74da886`.
2. Tags: `Name=lab-sg`, `Project=tcp-flood-lab`.
3. Ingress Rule 1: SSH (port 22) allowed ONLY from operator IP `${MYIP}/32`.
4. Ingress Rule 2: Intra-SG mesh: all protocols (`-1`) allowed between members of `lab-sg` (`--source-group`).
5. **ZERO PUBLIC EXPOSURE:** Ingress `0.0.0.0/0` and `::/0` are strictly forbidden.

```bash
# Check if lab-sg already exists
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

# Save raw SG creation state
aws ec2 describe-security-groups \
  --group-ids "$SG_ID" \
  --region "$AWS_REGION" \
  --output json > /Users/raja/Documents/syn-edge-flooding/infra/sg_create.json

# Ingress Rule 1: Allow SSH (port 22) exclusively from operator /32
echo "Authorizing SSH ingress from $MYIP/32..."
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 22 \
  --cidr "${MYIP}/32" \
  --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=operator-ssh},{Key=Project,Value=tcp-flood-lab}]" \
  --region "$AWS_REGION" 2>/dev/null || echo "SSH rule already authorized."

# Ingress Rule 2: Allow all traffic between instances in lab-sg (intra-SG mesh)
echo "Authorizing intra-SG all-traffic mesh..."
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol -1 \
  --source-group "$SG_ID" \
  --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=intra-lab-mesh},{Key=Project,Value=tcp-flood-lab}]" \
  --region "$AWS_REGION" 2>/dev/null || echo "Intra-SG mesh rule already authorized."

# Snapshot described security group
aws ec2 describe-security-groups \
  --group-ids "$SG_ID" \
  --region "$AWS_REGION" \
  --output json > /Users/raja/Documents/syn-edge-flooding/infra/sg_described.json

# Hard Invariant Verification: Ensure NO 0.0.0.0/0 or ::/0 ingress rules exist
PUBLIC_RULES=$(aws ec2 describe-security-groups \
  --group-ids "$SG_ID" \
  --region "$AWS_REGION" \
  --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' \
  --output text)

if [[ -n "$PUBLIC_RULES" ]]; then
  echo "❌ CRITICAL SAFETY VIOLATION: Public 0.0.0.0/0 or ::/0 rule detected in $SG_ID! Aborting!" >&2
  exit 1
else
  echo "✅ Security Group invariant verified: 0.0.0.0/0 strictly absent."
fi
```

### 3.4 Dynamic Operator IP Shift Handler (`infra/update_sg_ip.sh`)
If the operator's public IP shifts during the lab execution, SSH connections will time out. Feature #8 (`Dynamic IP SG Update`) is implemented via this standalone utility script:

```bash
cat << 'EOF' > /Users/raja/Documents/syn-edge-flooding/infra/update_sg_ip.sh
#!/usr/bin/env bash
set -euo pipefail

LAB_ENV="/Users/raja/Documents/syn-edge-flooding/lab.env"
if [[ -f "$LAB_ENV" ]]; then
  source "$LAB_ENV"
else
  echo "Error: lab.env not found" >&2
  exit 1
fi

NEW_IP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
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

echo "✅ Security Group SSH ingress updated to ${NEW_IP}/32"
EOF
chmod +x /Users/raja/Documents/syn-edge-flooding/infra/update_sg_ip.sh
```

### 3.5 EC2 Instance Launching (`victim`, `attacker`, `client`)
Launch the 3 instances in `ap-south-1a` (`subnet-0709c5a163cc423bb`), tagging each instance with its role and enforcing `--credit-specification CpuCredits=standard`.

```bash
echo "Launching victim instance..."
VICTIM_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --credit-specification CpuCredits=standard \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=victim},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=victim}]" \
  --region "$AWS_REGION" \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Launching attacker instance..."
ATTACKER_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --credit-specification CpuCredits=standard \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=attacker},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=attacker}]" \
  --region "$AWS_REGION" \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Launching client instance..."
CLIENT_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --credit-specification CpuCredits=standard \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=client},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=client}]" \
  --region "$AWS_REGION" \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Launched instances:"
echo "  Victim:   $VICTIM_ID"
echo "  Attacker: $ATTACKER_ID"
echo "  Client:   $CLIENT_ID"
```

### 3.6 Instance State Wait & Readiness Verification
Wait until all three instances are running and system status checks pass:

```bash
echo "Waiting for instances to reach 'running' state..."
aws ec2 wait instance-running \
  --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
  --region "$AWS_REGION"
echo "✅ All instances are running."

echo "Waiting for system status checks (instance-status-ok)..."
aws ec2 wait instance-status-ok \
  --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
  --region "$AWS_REGION"
echo "✅ All instances passed status checks."

# Snapshot described instances
aws ec2 describe-instances \
  --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
  --region "$AWS_REGION" \
  --output json > /Users/raja/Documents/syn-edge-flooding/infra/instances_described.json
```

---

## 4. IP Topology Extraction & `lab.env` Generation

### 4.1 IP Extraction
Extract public and private IPs for each node:

```bash
VICTIM_PUB=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
VICTIM_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

ATTACKER_PUB=$(aws ec2 describe-instances --instance-ids "$ATTACKER_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
ATTACKER_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$ATTACKER_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

CLIENT_PUB=$(aws ec2 describe-instances --instance-ids "$CLIENT_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
CLIENT_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$CLIENT_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
```

### 4.2 Non-Interactive SSH Verification & Primary Interface Discovery
To discover `VICTIM_IFACE` dynamically and accept host fingerprints non-interactively:

```bash
SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o BatchMode=yes)

echo "Connecting to victim to detect primary network interface..."
VICTIM_IFACE=$(ssh "${SSH_OPTS[@]}" ubuntu@"$VICTIM_PUB" "ip -o -4 route show to default | awk '{print \$5}'" 2>/dev/null || echo "ens5")
if [[ -z "$VICTIM_IFACE" ]]; then
  VICTIM_IFACE="ens5"
fi
echo "Discovered VICTIM_IFACE: $VICTIM_IFACE"

# Record node hostname and initial chrony/time state
ssh "${SSH_OPTS[@]}" ubuntu@"$VICTIM_PUB" "hostname; ip -br a; timedatectl" > /Users/raja/Documents/syn-edge-flooding/infra/victim_info.txt
ssh "${SSH_OPTS[@]}" ubuntu@"$ATTACKER_PUB" "hostname; ip -br a; timedatectl" > /Users/raja/Documents/syn-edge-flooding/infra/attacker_info.txt
ssh "${SSH_OPTS[@]}" ubuntu@"$CLIENT_PUB" "hostname; ip -br a; timedatectl" > /Users/raja/Documents/syn-edge-flooding/infra/client_info.txt
```

### 4.3 `lab.env` Contract Specification & Generation
The `lab.env` file must strictly fulfill the interface contract mandated by `PROJECT.md` §Interface Contracts (M1 -> M2) and `docs/AGENTS_tcp_flood_lab.md` §5.2. It must export exactly 15 variables:

```bash
cat << EOF > /Users/raja/Documents/syn-edge-flooding/lab.env
# ==============================================================================
# TCP Flood Detection Lab Environment Configuration (M1 -> M2 Contract)
# Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
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
EOF
chmod 600 /Users/raja/Documents/syn-edge-flooding/lab.env
```

---

## 5. Private IP ICMP Reachability Verification

Per `docs/AGENTS_tcp_flood_lab.md` Phase 1 step 9 and Acceptance Criteria (c), private connectivity between nodes must be verified via ICMP ping across the intra-SG mesh.

```bash
SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)

echo "Testing ICMP reachability from client -> victim ($VICTIM_PRIVATE_IP)..."
CLIENT_PING=$(ssh "${SSH_OPTS[@]}" ubuntu@"$CLIENT_PUB" "ping -c 3 $VICTIM_PRIVATE_IP")
echo "$CLIENT_PING"

echo "Testing ICMP reachability from attacker -> victim ($VICTIM_PRIVATE_IP)..."
ATTACKER_PING=$(ssh "${SSH_OPTS[@]}" ubuntu@"$ATTACKER_PUB" "ping -c 3 $VICTIM_PRIVATE_IP")
echo "$ATTACKER_PING"

# Persist verification proof
cat << EOF > /Users/raja/Documents/syn-edge-flooding/infra/ping_verification.txt
=== Client -> Victim Private IP ICMP Ping ($VICTIM_PRIVATE_IP) ===
$CLIENT_PING

=== Attacker -> Victim Private IP ICMP Ping ($VICTIM_PRIVATE_IP) ===
$ATTACKER_PING
EOF
```

---

## 6. End-to-End Turnkey Provisioning Script (`infra/provision_m1.sh`)

To enable single-command, reproducible execution, the implementer can save and run this unified script:

```bash
cat << 'EOF' > /Users/raja/Documents/syn-edge-flooding/infra/provision_m1.sh
#!/usr/bin/env bash
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

# 2. Operator IP Resolution
echo "[Step 1/8] Detecting operator public IP..."
MYIP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
if [[ -z "$MYIP" || ! "$MYIP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Error: Failed to resolve valid operator IPv4 address." >&2
  exit 1
fi
echo "✅ Operator IP verified: $MYIP/32"

# 3. Key Pair Setup
echo "[Step 2/8] Provisioning EC2 Key Pair ($KEY_NAME)..."
mkdir -p ~/.ssh && chmod 700 ~/.ssh
if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
  aws ec2 create-key-pair \
    --key-name "$KEY_NAME" \
    --key-type rsa \
    --key-format pem \
    --tag-specifications "ResourceType=key-pair,Tags=[{Key=Name,Value=$KEY_NAME},{Key=Project,Value=tcp-flood-lab}]" \
    --region "$AWS_REGION" \
    --query 'KeyMaterial' \
    --output text > "$KEY_PATH"
  chmod 400 "$KEY_PATH"
  echo "✅ Key pair created at $KEY_PATH"
else
  echo "ℹ️ Key pair $KEY_NAME already exists in AWS."
  if [[ ! -f "$KEY_PATH" ]]; then
    echo "❌ Error: Key exists in AWS but local file $KEY_PATH is missing. Manually reconcile or delete key pair in AWS." >&2
    exit 1
  fi
  chmod 400 "$KEY_PATH"
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

# Ingress Rules
echo "Configuring SG ingress rules..."
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 22 \
  --cidr "${MYIP}/32" \
  --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=operator-ssh},{Key=Project,Value=tcp-flood-lab}]" \
  --region "$AWS_REGION" 2>/dev/null || echo "SSH ingress rule already exists."

aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol -1 \
  --source-group "$SG_ID" \
  --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=intra-lab-mesh},{Key=Project,Value=tcp-flood-lab}]" \
  --region "$AWS_REGION" 2>/dev/null || echo "Intra-SG ingress rule already exists."

aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" --output json > "$LAB_ROOT/infra/sg_described.json"

# Safety Verification
PUBLIC_RULES=$(aws ec2 describe-security-groups \
  --group-ids "$SG_ID" \
  --region "$AWS_REGION" \
  --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' \
  --output text)

if [[ -n "$PUBLIC_RULES" ]]; then
  echo "❌ CRITICAL SAFETY ERROR: Public rule 0.0.0.0/0 detected!" >&2
  exit 1
fi
echo "✅ SG verified: zero 0.0.0.0/0 ingress."

# 5. EC2 Instances Launch
echo "[Step 4/8] Launching 3 EC2 t3.micro instances in $SUBNET_ID..."
VICTIM_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --credit-specification CpuCredits=standard \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=victim},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=victim}]" \
  --region "$AWS_REGION" \
  --query 'Instances[0].InstanceId' \
  --output text)

ATTACKER_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --credit-specification CpuCredits=standard \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=attacker},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=attacker}]" \
  --region "$AWS_REGION" \
  --query 'Instances[0].InstanceId' \
  --output text)

CLIENT_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --credit-specification CpuCredits=standard \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=client},{Key=Project,Value=tcp-flood-lab},{Key=Role,Value=client}]" \
  --region "$AWS_REGION" \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Launched Instance IDs:"
echo "  victim:   $VICTIM_ID"
echo "  attacker: $ATTACKER_ID"
echo "  client:   $CLIENT_ID"

# 6. Wait for Instances
echo "[Step 5/8] Waiting for instances to become running and healthy..."
aws ec2 wait instance-running --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION"
echo "Instances running. Waiting for 2/2 status checks ok..."
aws ec2 wait instance-status-ok --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION"
echo "✅ All 3 instances passed status checks."
aws ec2 describe-instances --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION" --output json > "$LAB_ROOT/infra/instances_described.json"

# 7. Extract IPs and Generate lab.env
echo "[Step 6/8] Extracting IP addresses and generating lab.env..."
VICTIM_PUB=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
VICTIM_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

ATTACKER_PUB=$(aws ec2 describe-instances --instance-ids "$ATTACKER_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
ATTACKER_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$ATTACKER_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

CLIENT_PUB=$(aws ec2 describe-instances --instance-ids "$CLIENT_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
CLIENT_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$CLIENT_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o BatchMode=yes)
echo "Querying primary interface from victim..."
VICTIM_IFACE=$(ssh "${SSH_OPTS[@]}" ubuntu@"$VICTIM_PUB" "ip -o -4 route show to default | awk '{print \$5}'" 2>/dev/null || echo "ens5")
if [[ -z "$VICTIM_IFACE" ]]; then VICTIM_IFACE="ens5"; fi
echo "Discovered VICTIM_IFACE: $VICTIM_IFACE"

cat << ENV_EOF > "$LAB_ROOT/lab.env"
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
echo "✅ lab.env generated successfully."

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
echo "✅ Private ICMP ping verified and written to infra/ping_verification.txt"

# 9. Update State Machine & Log
echo "[Step 8/8] Updating STATE.md and LAB_LOG.md..."
sed -i '' 's/Status:\ IN_PROGRESS/Status:\ COMPLETE/g' "$LAB_ROOT/STATE.md" 2>/dev/null || true
echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | A1 Infra | Milestone 1 Provisioning Complete | 3 nodes launched, lab.env created, ICMP verified." >> "$LAB_ROOT/LAB_LOG.md"

echo "======================================================================"
echo " Milestone 1 Provisioning Successfully Completed!"
echo "======================================================================"
EOF
chmod +x /Users/raja/Documents/syn-edge-flooding/infra/provision_m1.sh
```

---

## 7. Milestone 1 Acceptance Verification Checklist

The implementer must verify each of the following acceptance criteria prior to reporting M1 completion:

| Acceptance Criterion | Verification Method | Expected Result | Pass / Fail |
|---|---|---|---|
| **AC-M1.1: Git Repository Initialized** | `git status` | Clean status or untracked expected scaffolding files on `main` branch | [ ] |
| **AC-M1.2: Secret & Pcap Exclusion** | `git check-ignore ~/.ssh/tcp-flood-lab.pem lab.env runs/test/capture.pcap` | All three files ignored | [ ] |
| **AC-M1.3: Python Analysis Stack Ready** | `python3 -c "import matplotlib, pandas, numpy, sklearn, yaml"` | Exit code 0, all modules loaded | [ ] |
| **AC-M1.4: Zero Public SG Ingress** | `aws ec2 describe-security-groups --group-ids $SG_ID --query 'SecurityGroups[0].IpPermissions[].IpRanges[].CidrIp'` | Only `152.57.107.6/32` returned; NO `0.0.0.0/0` | [ ] |
| **AC-M1.5: Intra-SG Mesh Allowed** | `aws ec2 describe-security-groups --group-ids $SG_ID --query 'SecurityGroups[0].IpPermissions[].UserIdGroupPairs[].GroupId'` | Exactly `$SG_ID` returned | [ ] |
| **AC-M1.6: Key Pair Created & chmod 400** | `ls -l ~/.ssh/tcp-flood-lab.pem` | Permissions `-r--------` (400) | [ ] |
| **AC-M1.7: 3 Instances Running & Tagged** | `aws ec2 describe-instances --filters "Name=tag:Project,Values=tcp-flood-lab" "Name=instance-state-name,Values=running"` | Exactly 3 instances (`victim`, `attacker`, `client`) | [ ] |
| **AC-M1.8: Standard CPU Credit Spec** | `aws ec2 describe-instance-credit-specifications --instance-ids $VICTIM_ID $ATTACKER_ID $CLIENT_ID` | `CpuCredits: standard` for all 3 nodes | [ ] |
| **AC-M1.9: Complete `lab.env`** | `grep -E '^(export )?[A-Z_]+=' lab.env \| wc -l` | Exactly 15 required variables present | [ ] |
| **AC-M1.10: Private ICMP Ping Success** | Inspect `infra/ping_verification.txt` | 0% packet loss from client and attacker to victim private IP | [ ] |
| **AC-M1.11: Non-interactive SSH Ready** | `ssh -i $KEY_PATH -o BatchMode=yes ubuntu@$VICTIM_PUB "echo ok"` | Returns `ok` with 0 exit code | [ ] |

---

## 8. Failure Modes & Automated Recovery Runbook

| Failure Mode | Root Cause | Automated Remediation |
|---|---|---|
| **SSH Connection Timeout** | Operator public IP shifted (ISP dynamic DHCP / cellular change) | Run `infra/update_sg_ip.sh` to refresh the `/32` rule in `lab-sg`. |
| **InvalidKeyPair.Duplicate** | Key pair exists in AWS but `.pem` file is missing locally | Script checks if key file exists; if missing, deletes existing AWS key pair and regenerates new `.pem`. |
| **InvalidGroup.Duplicate** | `lab-sg` already exists from previous partial run | Script queries existing SG ID by name (`lab-sg`) and updates rules rather than recreating. |
| **EC2 Status Check Lag** | Nitro instance cloud-init takes >60s | `aws ec2 wait instance-status-ok` provides built-in polling; retry SSH loop with 15s timeout. |
| **StrictHostKeyChecking Prompt** | Fresh host key not recognized by OpenSSH | Enforce `-o StrictHostKeyChecking=accept-new -o BatchMode=yes` on all automated commands. |
| **Burst Credit Surcharges** | Default t3 unlimited credit setting | Explicit `--credit-specification CpuCredits=standard` on `aws ec2 run-instances` ensures throttling rather than monetary overage. |
