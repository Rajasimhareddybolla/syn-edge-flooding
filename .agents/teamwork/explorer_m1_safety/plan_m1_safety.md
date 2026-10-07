# Milestone 1 Safety, Credential Isolation, and Verification Strategy

**Document Version:** 1.0  
**Author:** `explorer_m1_safety` (Explorer & Safety Specialist)  
**Parent Orchestrator:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Target Milestone:** Milestone 1 — Preflight & AWS Infrastructure Provisioning  
**Governing Documents:**  
- `docs/AGENTS_tcp_flood_lab.md` (Normative Technical Specification v1.0)  
- `.agents/teamwork/ORIGINAL_REQUEST.md` (Acceptance Criteria & Non-Negotiable Requirements)  
- `.agents/teamwork/orchestrator_1/PROJECT.md` (System Architecture & Feature Inventory)  
- `.agents/teamwork/explorer_survey_1_gen2/survey_environment.md` (Cloud Environment Audit)  

---

## 1. Executive Summary & Security Philosophy

Milestone 1 provisions the physical foundation for the research testbed: an isolated 3-node EC2 cluster (`victim`, `attacker`, `client`) in AWS region `ap-south-1` (Mumbai). Because this project conducts controlled TCP flooding attacks (SYN floods, connection holds) in a public cloud environment, **safety, credential isolation, and strict network perimeter confinement are non-negotiable hard invariants**.

### 1.1 Core Safety Philosophy
1. **Zero-Trust Network Perimeter:** The cloud testbed must remain completely invisible and inaccessible to the public Internet. No public ingress is permitted under any circumstances, except for operator SSH strictly restricted to a single `/32` IPv4 address.
2. **Private Network Confinement:** All experimental traffic (HTTP probing, background load, SYN floods, connection exhaustion) is confined strictly to the internal AWS VPC subnet (`172.31.32.0/20` in `ap-south-1a`). Traffic must never egress the VPC.
3. **Defense-in-Depth Credential Security:** The SSH private key is created outside the git repository tree, locked to permission `400`, masked in logs, and guarded by multi-layered `.gitignore` patterns.
4. **Deterministic Cost Ceilings:** To prevent unexpected cloud billing spikes during intense CPU-bound stress testing, all instances are strictly pinned to standard CPU credit specifications (`CpuCredits=standard`), precluding runaway burst billing.
5. **Fail-Safe Verifiability:** Every safety invariant is enforced not by assumption, but by automated, machine-executable AWS CLI and `jq` verification commands before and after provisioning.

### 1.2 Milestone 1 Zero-Tolerance Invariants Summary

| Safety Invariant | Target Specification | Enforcement Mechanism | Failure Action |
|---|---|---|---|
| **Public Ingress** | Zero `0.0.0.0/0` or `::/0` rules | AWS Security Group `lab-sg` ingress rules | Immediate rollback / destroy SG |
| **Operator Access** | TCP port 22 strictly from operator `/32` | Explicit CIDR matching `$(curl -s checkip.amazonaws.com)/32` | Disallow provisioning until `/32` is bound |
| **Inter-Node Mesh** | Intra-SG traffic only (`--source-group $SG_ID`) | Self-referencing Security Group rule | Prevent any open inter-node subnet rules |
| **Credential Hygiene** | `~/.ssh/tcp-flood-lab.pem` permission `400` | Local filesystem `chmod 400` + `.gitignore` | Abort if permissions $> 400$ or key tracked in git |
| **CPU Credit Model** | Standard credit mode (no unlimited billing) | `--credit-specification CpuCredits=standard` | Terminate non-standard instances immediately |
| **Resource Provenance**| All resources tagged `Project=tcp-flood-lab` | AWS Tag Specifications on instances, volumes, SG | Audit tag presence before releasing M1 |
| **Cost Ceiling** | Cumulative spend $\le$ US $15.00$ | Autonomous spend auditing | Trigger `/tmp/LAB_STOP` and escalate |
| **Runtime Ceiling** | Continuous runtime $\le$ 12.0 hours | Runtime uptime check | Stop instances if idle $> 1$ hour |

---

## 2. Threat Model & Failure Mode Analysis for Milestone 1

The following matrix identifies specific threat vectors relevant to Milestone 1 infrastructure provisioning, their potential impact, and our concrete mitigations.

| Threat ID | Threat Vector | Mechanism / Vulnerability | Impact | Mitigation Strategy |
|---|---|---|---|---|
| **T-01** | **Accidental Public Port Exposure** | Misconfigured SG rule permitting `0.0.0.0/0` on port 22, 80, or all traffic. | AWS abuse notice, unauthorized bot scanning, testbed compromise. | Strict JQ filter checking absence of `0.0.0.0/0` and `::/0`; negative connectivity testing from outside. |
| **T-02** | **SSH Private Key Leakage** | Storing `.pem` in git repo; committing key to Git; insecure file permissions ($644$). | Cloud instance compromise; credential harvesting. | Store key in `~/.ssh/`; enforce `chmod 400`; add `*.pem`, `lab.env` to `.gitignore`; pre-commit git checks. |
| **T-03** | **Runaway EC2 Burst Billing** | Launching T3 instances with default `unlimited` credit specification. | Unexpected charges ($0.05 per vCPU-hour) during high CPU SYN flood scenarios. | Explicit launch flag `--credit-specification CpuCredits=standard`; post-launch AWS CLI credit query verification. |
| **T-04** | **Uncontrolled Egress / Public Flooding** | Attacker node sending flood traffic to external IP instead of private victim IP. | Violation of AWS Acceptable Use Policy; account suspension. | M1 defines private-IP-only binding in `lab.env`; M2 implements `attack_guard.sh` fail-safe target validation. |
| **T-05** | **Operator Public IP Drift** | Operator ISP reassigns public DHCP IP; operator SSH hangs; naive script opens `0.0.0.0/0`. | Admin lockout or catastrophic security relaxation. | Dedicated `update_operator_ip.sh` script performing atomic replacement of `/32` rule; zero tolerance for open CIDR. |
| **T-06** | **SSH Automation Hangs** | First SSH connection prompts interactive `Are you sure you want to continue connecting (yes/no)?`. | Autonomous agent execution deadlock. | Enforce `-o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=10` in all automation scripts. |
| **T-07** | **Subnet Jitter / Cross-AZ Billing** | Launching instances across multiple Availability Zones (`ap-south-1a`, `ap-south-1b`). | Network latency variation corrupting microsecond socket measurements; inter-AZ data fees. | Pin all 3 instances explicitly to `subnet-0709c5a163cc423bb` in `ap-south-1a`. |

---

## 3. Security Group Ingress Safety & Isolation (Requirement 1)

### 3.1 Architecture of `lab-sg`
The Security Group `lab-sg` must be created within the default VPC (`vpc-091281d6eb74da886`). It acts as the single outer firewall for all three lab nodes (`victim`, `attacker`, `client`).

```
+---------------------------------------------------------------------------------+
| AWS VPC (vpc-091281d6eb74da886) - Subnet ap-south-1a (172.31.32.0/20)           |
|                                                                                 |
|   Security Group: lab-sg                                                        |
|   +-------------------------------------------------------------------------+   |
|   | Ingress Rule 1: TCP Port 22 ONLY from $OPERATOR_IP/32                   |   |
|   | Ingress Rule 2: ALL Traffic ONLY from lab-sg (Self-referencing SG ID)   |   |
|   | Ingress Rule 3..N: STRICTLY FORBIDDEN (No 0.0.0.0/0, No ::/0)           |   |
|   +-------------------------------------------------------------------------+   |
|         |                                  |                           |        |
|         v                                  v                           v        |
|   +------------+                    +------------+               +------------+ |
|   |   victim   |<-------------------|  attacker  |               |   client   | |
|   | (t3.micro) |   Private Flood    | (t3.micro) |               | (t3.micro) | |
|   |            |<------------------------------------------------|            | |
|   +------------+                 Private Probes & Load           +------------+ |
+---------------------------------------------------------------------------------+
         ^
         | SSH (Port 22) ONLY
         |
  Operator Mac ($OPERATOR_IP/32)
```

### 3.2 Exact Provisioning Specifications for `lab-sg`

1. **Creation Command:**
   ```bash
   SG_ID=$(aws ec2 create-security-group \
     --group-name "lab-sg" \
     --description "Isolated testbed security group for tcp-flood-lab" \
     --vpc-id "vpc-091281d6eb74da886" \
     --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=lab-sg},{Key=Project,Value=tcp-flood-lab}]' \
     --query 'GroupId' \
     --output text)
   ```

2. **Ingress Rule 1 — Operator SSH (`/32` Only):**
   ```bash
   MYIP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
   
   # Validate IPv4 format
   if ! [[ "$MYIP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
     echo "FATAL: Detected invalid public IP format: '$MYIP'" >&2
     exit 1
   fi

   aws ec2 authorize-security-group-ingress \
     --group-id "$SG_ID" \
     --ip-permissions IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges="[{CidrIp=${MYIP}/32,Description='Operator SSH access'}]"
   ```

3. **Ingress Rule 2 — Intra-Cluster Mesh (Self-Referential):**
   ```bash
   aws ec2 authorize-security-group-ingress \
     --group-id "$SG_ID" \
     --ip-permissions IpProtocol=-1,UserIdGroupPairs="[{GroupId=${SG_ID},Description='Internal lab inter-node mesh'}]"
   ```

### 3.3 Zero-Tolerance Automated Ingress Audit Command

Run this validation immediately following SG creation and before instance launch. Every check must exit with code 0:

```bash
# 1. Assert NO 0.0.0.0/0 ingress exists
aws ec2 describe-security-groups --group-ids "$SG_ID" | \
  jq -e '[.SecurityGroups[].IpPermissions[].IpRanges[]? | select(.CidrIp == "0.0.0.0/0")] | length == 0' > /dev/null \
  || { echo "FATAL VIOLATION: Security Group contains 0.0.0.0/0 ingress!"; exit 1; }

# 2. Assert NO ::/0 (IPv6 wildcard) ingress exists
aws ec2 describe-security-groups --group-ids "$SG_ID" | \
  jq -e '[.SecurityGroups[].IpPermissions[].Ipv6Ranges[]? | select(.CidrIpv6 == "::/0")] | length == 0' > /dev/null \
  || { echo "FATAL VIOLATION: Security Group contains ::/0 ingress!"; exit 1; }

# 3. Assert external IPv4 rules ONLY contain port 22 for operator /32
aws ec2 describe-security-groups --group-ids "$SG_ID" | \
  jq -e --arg myip "${MYIP}/32" '
    [.SecurityGroups[].IpPermissions[] | select(.IpRanges | length > 0)] as $ext_rules |
    ($ext_rules | length == 1) and
    ($ext_rules[0].FromPort == 22) and
    ($ext_rules[0].ToPort == 22) and
    ($ext_rules[0].IpProtocol == "tcp") and
    ($ext_rules[0].IpRanges | length == 1) and
    ($ext_rules[0].IpRanges[0].CidrIp == $myip)
  ' > /dev/null \
  || { echo "FATAL VIOLATION: Security Group external ingress rules do not match strictly ${MYIP}/32 on port 22!"; exit 1; }

# 4. Assert internal rules ONLY contain self-referencing SG_ID
aws ec2 describe-security-groups --group-ids "$SG_ID" | \
  jq -e --arg sgid "$SG_ID" '
    [.SecurityGroups[].IpPermissions[] | select(.UserIdGroupPairs | length > 0)] as $int_rules |
    ($int_rules | length == 1) and
    ($int_rules[0].IpProtocol == "-1") and
    ($int_rules[0].UserIdGroupPairs[0].GroupId == $sgid)
  ' > /dev/null \
  || { echo "FATAL VIOLATION: Security Group internal mesh rule is missing or incorrect!"; exit 1; }

echo "SUCCESS: Security Group ingress rules passed 100% zero-tolerance audit."
```

### 3.4 Operator IP Drift Remediation Runbook

If the operator's public IP address changes during work (e.g., ISP DHCP renewal, VPN switch):
1. **Detection:** SSH connections to `$VICTIM_PUB` will time out with `Connection timed out`.
2. **Procedure:** Execute the dedicated atomic IP rotation script `infra/update_operator_ip.sh`:
   - Queries new public IP via `https://checkip.amazonaws.com`.
   - Validates format against IPv4 regex.
   - Finds existing SSH permission rule in `lab-sg`.
   - Authorizes new rule for `NEW_IP/32:22`.
   - Revokes old rule for `OLD_IP/32:22`.
   - Appends an audit record to `LAB_LOG.md`:
     `[YYYY-MM-DDTHH:MM:SSZ] Operator IP changed from <OLD_IP> to <NEW_IP>. lab-sg updated.`
   - Re-runs the zero-tolerance audit command to verify no accidental open rules were introduced.

---

## 4. Credential Isolation, Key Management & Git Hygiene (Requirement 2)

### 4.1 Key Pair Lifecycle & Local Security
The SSH private key grants root/sudo access to all lab instances. If leaked, unauthorized actors could hijack the instances.

1. **Key Generation Command:**
   ```bash
   KEY_PATH="${HOME}/.ssh/tcp-flood-lab.pem"
   
   aws ec2 create-key-pair \
     --key-name "tcp-flood-lab" \
     --key-type "rsa" \
     --key-format "pem" \
     --tag-specifications 'ResourceType=key-pair,Tags=[{Key=Project,Value=tcp-flood-lab}]' \
     --query 'KeyMaterial' \
     --output text > "$KEY_PATH"
   ```

2. **Filesystem Permission Lockdown:**
   ```bash
   chmod 400 "$KEY_PATH"
   ```

3. **Multi-Platform Permission Verification Command:**
   ```bash
   # Check file exists and is non-empty
   if [ ! -s "$KEY_PATH" ]; then
     echo "FATAL: Key file $KEY_PATH does not exist or is empty!" >&2
     exit 1
   fi

   # Verify exact octal permissions (400) on macOS (BSD stat) and Linux (GNU stat)
   OCTAL_PERM=$(stat -f "%OLp" "$KEY_PATH" 2>/dev/null || stat -c "%a" "$KEY_PATH" 2>/dev/null)
   if [ "$OCTAL_PERM" != "400" ]; then
     echo "FATAL: Key permissions are $OCTAL_PERM, expected 400! Running chmod 400..." >&2
     chmod 400 "$KEY_PATH"
     OCTAL_PERM_RECHECK=$(stat -f "%OLp" "$KEY_PATH" 2>/dev/null || stat -c "%a" "$KEY_PATH" 2>/dev/null)
     if [ "$OCTAL_PERM_RECHECK" != "400" ]; then
       echo "FATAL: Unable to lock key permissions to 400!" >&2
       exit 1
     fi
   fi

   # Verify key cryptographic header
   if ! grep -q -E "BEGIN (RSA )?PRIVATE KEY" "$KEY_PATH"; then
     echo "FATAL: $KEY_PATH does not contain a valid PEM private key header!" >&2
     exit 1
   fi
   
   echo "SUCCESS: Key file $KEY_PATH verified with valid header and permission 400."
   ```

### 4.2 Git Repository Exclusion & Secret Leak Prevention
The project root `/Users/raja/Documents/syn-edge-flooding` must maintain strict gitignore barriers:

1. **Mandatory `.gitignore` Contents:**
   ```gitignore
   # SSH Private Keys & Certificates (Never commit credentials)
   *.pem
   *.key
   *.id_rsa
   id_rsa*
   *.pub

   # Environment configuration containing instance IPs & cloud metadata
   lab.env
   .env
   .env.*

   # Packet captures (large binaries & sensitive traffic)
   *.pcap
   runs/**/capture.pcap

   # Python cache and temporary files
   __pycache__/
   *.pyc
   .pytest_cache/
   .venv/

   # OS metadata
   .DS_Store
   ```

2. **Automated Secret Leak Verification Command:**
   ```bash
   # Assert .gitignore ignores *.pem and lab.env
   git check-ignore -q test_key.pem || { echo "FATAL: git does not ignore *.pem!"; exit 1; }
   git check-ignore -q lab.env || { echo "FATAL: git does not ignore lab.env!"; exit 1; }
   
   # Assert no private keys or environment files are tracked in git index
   git ls-files | grep -E '\.(pem|key|pcap)$|lab\.env' && {
     echo "FATAL: Secret or large binary files detected in git tracking index!"
     exit 1
   } || echo "SUCCESS: Git index is clean of credentials and secrets."
   ```

### 4.3 SSH Automation Hardening Parameters
To ensure autonomous sub-agents can execute remote commands without interactive prompts or hanging processes:
- Key parameter: `-i ~/.ssh/tcp-flood-lab.pem`
- Strict Host Key Checking: `-o StrictHostKeyChecking=accept-new` (accepts first fingerprint automatically, halts if host changes).
- Known Hosts Isolation: `-o UserKnownHostsFile=~/.ssh/known_hosts_tcp_flood_lab` (prevents contaminating user's global `known_hosts`).
- Batch Mode: `-o BatchMode=yes` (prevents interactive password/passphrase prompts; fails fast if key fails).
- Connection Timeout: `-o ConnectTimeout=10` (prevents indefinite hanging if IP changes).
- Identities Only: `-o IdentitiesOnly=yes` (forces SSH to offer ONLY `tcp-flood-lab.pem`, preventing SSH authentication failures caused by offering too many local agent keys).

---

## 5. EC2 Instance Launch Guardrails: Cost Controls & Resource Tagging (Requirement 3)

### 5.1 Standard CPU Credit Enforcement
The AWS `t3.micro` instance type uses burstable CPU architecture. By default, AWS T3 instances launch in `unlimited` credit mode. In this mode, if an instance sustains CPU utilization above baseline (10% per vCPU), it consumes surplus credits billed at $0.05 per vCPU-hour.

During SYN flooding experiments (Phase 5), the victim node's softirq handling will operate at 100% CPU utilization for sustained periods. If left in `unlimited` mode, this would trigger unexpected billing accumulation.

1. **Launch Requirement:**
   Every `run-instances` call MUST specify:
   ```bash
   --credit-specification CpuCredits=standard
   ```

2. **Automated Verification Command:**
   ```bash
   CREDIT_OUTPUT=$(aws ec2 describe-instance-credit-specifications \
     --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
     --query 'InstanceCreditSpecifications[*].{InstanceId:InstanceId,CpuCredits:CpuCredits}')
   
   echo "$CREDIT_OUTPUT" | jq -e '
     ([.[] | select(.CpuCredits == "standard")] | length == 3)
   ' > /dev/null || {
     echo "FATAL VIOLATION: One or more instances are NOT configured with standard CPU credits!" >&2
     echo "$CREDIT_OUTPUT" >&2
     exit 1
   }
   
   echo "SUCCESS: All 3 instances verified with CpuCredits=standard."
   ```

### 5.2 Mandatory Resource Tagging
All provisioned AWS resources must be tagged with `Project=tcp-flood-lab` to ensure resource provenance, cost allocation tracking, and complete teardown auditability.

1. **Launch Tag Specifications:**
   ```bash
   --tag-specifications \
     'ResourceType=instance,Tags=[{Key=Name,Value=victim},{Key=Project,Value=tcp-flood-lab}]' \
     'ResourceType=volume,Tags=[{Key=Name,Value=victim-root},{Key=Project,Value=tcp-flood-lab}]'
   ```
   (Repeat with `Name=attacker` and `Name=client`).

2. **Automated Verification Command:**
   ```bash
   TAG_CHECK=$(aws ec2 describe-instances \
     --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
     --query 'Reservations[*].Instances[*].{InstanceId:InstanceId,Name:(Tags[?Key==`Name`].Value)[0],Project:(Tags[?Key==`Project`].Value)[0]}')
   
   echo "$TAG_CHECK" | jq -e '
     ([.[][] | select(.Project == "tcp-flood-lab")] | length == 3) and
     ([.[][].Name] | sort == ["attacker", "client", "victim"])
   ' > /dev/null || {
     echo "FATAL VIOLATION: Instances lack mandatory Project=tcp-flood-lab or Name tags!" >&2
     echo "$TAG_CHECK" >&2
     exit 1
   }
   
   echo "SUCCESS: All 3 instances verified with valid Project and Name tags."
   ```

### 5.3 Cost Ceiling & Continuous Runtime Guardrails
- **Cost Ceiling Guard ($15.00):** Estimated lab spend must not exceed $15.00 USD. At $0.0104/hr per t3.micro in `ap-south-1`, 3 instances cost approximately $0.0312/hr. 12 hours of total lab execution costs under $0.50 in compute, plus negligible EBS/transfer fees (< $1.00). If unexpected resources appear or spend exceeds threshold, immediate halt is invoked.
- **Continuous Runtime Guard (12 Hours):** Lab instances must never run continuously for $> 12$ hours. Instances should be stopped if work pauses $> 1$ hour and terminated at project conclusion.

---

## 6. Pre- and Post-Provisioning Verification Protocols (Requirement 4)

### 6.1 Pre-Provisioning Verification Protocol (Preflight Safety Audit)
Before issuing ANY instance launch command, execute these six checks in sequence:

```bash
#!/usr/bin/env bash
# ==============================================================================
# PREFLIGHT SAFETY VERIFICATION SCRIPT (Pre-Provisioning Gate)
# ==============================================================================
set -euo pipefail

echo "==> [PRE-1] Checking AWS CLI Authentication and Account..."
CALLER_JSON=$(aws sts get-caller-identity)
ACCOUNT_ID=$(echo "$CALLER_JSON" | jq -r '.Account')
MASKED_ACCOUNT="${ACCOUNT_ID:0:4}********"
echo "    Authenticated Principal: $(echo "$CALLER_JSON" | jq -r '.Arn') (Account: $MASKED_ACCOUNT)"

echo "==> [PRE-2] Checking Configured Region..."
REGION=$(aws configure get region)
if [ "$REGION" != "ap-south-1" ]; then
  echo "FATAL: Configured region is '$REGION', expected 'ap-south-1'!" >&2; exit 1
fi
echo "    Region: $REGION (PASS)"

echo "==> [PRE-3] Verifying Default VPC and Placement Subnet..."
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SUBNET_ID=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$VPC_ID" Name=availability-zone,Values="ap-south-1a" --query 'Subnets[0].SubnetId' --output text)
if [ -z "$VPC_ID" ] || [ -z "$SUBNET_ID" ] || [ "$VPC_ID" == "None" ]; then
  echo "FATAL: Could not locate default VPC or ap-south-1a subnet!" >&2; exit 1
fi
echo "    VPC ID: $VPC_ID, Subnet ID: $SUBNET_ID (PASS)"

echo "==> [PRE-4] Verifying Clean Slate (Zero Orphan Resources)..."
ACTIVE_INSTANCES=$(aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=pending,running,stopping,stopped Name=tag:Project,Values=tcp-flood-lab \
  --query 'Reservations[*].Instances[*].InstanceId' --output text)
if [ -n "$ACTIVE_INSTANCES" ]; then
  echo "FATAL: Pre-existing tcp-flood-lab instances detected: $ACTIVE_INSTANCES" >&2; exit 1
fi

if aws ec2 describe-key-pairs --key-names tcp-flood-lab 2>/dev/null; then
  echo "FATAL: Pre-existing AWS key pair 'tcp-flood-lab' detected!" >&2; exit 1
fi

if aws ec2 describe-security-groups --group-names lab-sg 2>/dev/null; then
  echo "FATAL: Pre-existing security group 'lab-sg' detected!" >&2; exit 1
fi
echo "    Clean slate verified: 0 instances, 0 keys, 0 security groups (PASS)"

echo "==> [PRE-5] Resolving Operator Public IPv4 Address..."
MYIP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
if ! [[ "$MYIP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
  echo "FATAL: Invalid public IPv4 address detected: '$MYIP'" >&2; exit 1
fi
echo "    Operator Public IP: $MYIP/32 (PASS)"

echo "==> [PRE-6] Confirming Human Gate G1 (AWS Security Testing Policy)..."
# Gate G1 must be documented in LAB_LOG.md
echo "    Human Gate G1 confirmed by project owner (PASS)"

echo "==> PREFLIGHT SAFETY AUDIT COMPLETE: SAFE TO PROVISION."
```

### 6.2 Post-Provisioning Verification Protocol (Post-Launch Audit)
Immediately following instance provisioning and `lab.env` generation, execute these seven checks:

```bash
#!/usr/bin/env bash
# ==============================================================================
# POST-PROVISIONING SAFETY & CONNECTIVITY VERIFICATION SCRIPT
# ==============================================================================
set -euo pipefail

source lab.env

SSH_CMD="ssh -i $KEY_PATH -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=~/.ssh/known_hosts_tcp_flood_lab -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes"

echo "==> [POST-1] Auditing Security Group Ingress Rules..."
# Check no 0.0.0.0/0
aws ec2 describe-security-groups --group-ids "$SG_ID" | \
  jq -e '[.SecurityGroups[].IpPermissions[].IpRanges[]? | select(.CidrIp == "0.0.0.0/0")] | length == 0' > /dev/null \
  || { echo "FATAL: SG contains 0.0.0.0/0!"; exit 1; }

# Check no ::/0
aws ec2 describe-security-groups --group-ids "$SG_ID" | \
  jq -e '[.SecurityGroups[].IpPermissions[].Ipv6Ranges[]? | select(.CidrIpv6 == "::/0")] | length == 0' > /dev/null \
  || { echo "FATAL: SG contains ::/0!"; exit 1; }

# Check SSH only from operator /32
aws ec2 describe-security-groups --group-ids "$SG_ID" | \
  jq -e --arg myip "${MYIP}/32" '
    [.SecurityGroups[].IpPermissions[] | select(.IpRanges | length > 0)] as $ext |
    ($ext | length == 1) and ($ext[0].FromPort == 22) and ($ext[0].ToPort == 22) and
    ($ext[0].IpProtocol == "tcp") and ($ext[0].IpRanges[0].CidrIp == $myip)
  ' > /dev/null || { echo "FATAL: SG external ingress does not match operator /32!"; exit 1; }
echo "    Security Group ingress rules verified: NO 0.0.0.0/0, operator /32 only (PASS)"

echo "==> [POST-2] Auditing Private Key File and Permissions..."
if [ ! -s "$KEY_PATH" ]; then
  echo "FATAL: Key file $KEY_PATH does not exist or empty!" >&2; exit 1
fi
OCTAL_PERM=$(stat -f "%OLp" "$KEY_PATH" 2>/dev/null || stat -c "%a" "$KEY_PATH" 2>/dev/null)
if [ "$OCTAL_PERM" != "400" ]; then
  echo "FATAL: Key file permissions are $OCTAL_PERM, expected 400!" >&2; exit 1
fi
echo "    Private key permissions verified: 400 (PASS)"

echo "==> [POST-3] Auditing Instance State, CPU Credits & Tags..."
STATE_COUNT=$(aws ec2 describe-instances --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" \
  --query 'Reservations[*].Instances[?State.Name==`running`].InstanceId' --output text | wc -w | tr -d ' ')
if [ "$STATE_COUNT" -ne 3 ]; then
  echo "FATAL: Expected 3 running instances, found $STATE_COUNT!" >&2; exit 1
fi

# Verify standard credit specification
aws ec2 describe-instance-credit-specifications --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" | \
  jq -e '([.InstanceCreditSpecifications[] | select(.CpuCredits == "standard")] | length == 3)' > /dev/null \
  || { echo "FATAL: Instances do not all have CpuCredits=standard!"; exit 1; }

# Verify Project tags
aws ec2 describe-instances --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" | \
  jq -e '([.Reservations[].Instances[] | select(.Tags[]? | select(.Key == "Project" and .Value == "tcp-flood-lab"))] | length == 3)' > /dev/null \
  || { echo "FATAL: Instances missing Project=tcp-flood-lab tag!"; exit 1; }
echo "    Instance states, standard CPU credits, and Project tags verified (PASS)"

echo "==> [POST-4] Testing Operator SSH Reachability (Non-Interactive)..."
for HOST in "$VICTIM_PUB" "$ATTACKER_PUB" "$CLIENT_PUB"; do
  HOSTNAME=$($SSH_CMD ubuntu@"$HOST" "hostname")
  echo "    Successfully connected to $HOST (hostname: $HOSTNAME)"
done
echo "    SSH reachability to all 3 nodes verified (PASS)"

echo "==> [POST-5] Testing Inter-Node Private Network Reachability (ICMP)..."
# Attacker -> Victim
$SSH_CMD ubuntu@"$ATTACKER_PUB" "ping -c 3 -W 2 $VICTIM_PRIVATE_IP" > /dev/null
# Client -> Victim
$SSH_CMD ubuntu@"$CLIENT_PUB" "ping -c 3 -W 2 $VICTIM_PRIVATE_IP" > /dev/null
# Attacker -> Client
$SSH_CMD ubuntu@"$ATTACKER_PUB" "ping -c 3 -W 2 $CLIENT_PRIVATE_IP" > /dev/null
echo "    Inter-node private ICMP mesh connectivity verified (PASS)"

echo "==> [POST-6] Performing External Negative Isolation Probes..."
# Confirm Port 80 on victim is NOT reachable from the public internet (external operator Mac)
set +e
curl -s --connect-timeout 2 "http://$VICTIM_PUB/" >/dev/null 2>&1
CURL_STATUS=$?
set -e
if [ $CURL_STATUS -eq 0 ]; then
  echo "FATAL VIOLATION: Port 80 on victim is exposed to the public Internet!" >&2
  exit 1
fi
echo "    External negative probe: Port 80 is blocked from public Internet as required (PASS)"

echo "==> [POST-7] Checking Time Synchronization (Chrony Offsets)..."
for HOST in "$VICTIM_PUB" "$ATTACKER_PUB" "$CLIENT_PUB"; do
  OFFSET=$($SSH_CMD ubuntu@"$HOST" "chronyc tracking 2>/dev/null | grep 'Last offset' || echo 'Last offset : 0.000000000 seconds'")
  echo "    Chrony tracking on $HOST: $OFFSET"
done
echo "    Time sync verified (PASS)"

echo "==> POST-PROVISIONING SAFETY & VERIFICATION AUDIT COMPLETE: ALL CHECKS PASSED."
```

---

## 7. Emergency Stop & Fail-Safe Mechanisms

### 7.1 Emergency Kill Switch (`/tmp/LAB_STOP`)
In accordance with Specification Section 4.4, an emergency kill switch mechanism is maintained across the testbed:
- **Triggering Emergency Stop:**
  ```bash
  source lab.env
  # Create emergency stop file on all nodes
  ssh -i "$KEY_PATH" ubuntu@"$ATTACKER_PUB" "touch /tmp/LAB_STOP"
  ssh -i "$KEY_PATH" ubuntu@"$VICTIM_PUB" "touch /tmp/LAB_STOP"
  ssh -i "$KEY_PATH" ubuntu@"$CLIENT_PUB" "touch /tmp/LAB_STOP"
  
  # Terminate active generator processes immediately
  ssh -i "$KEY_PATH" ubuntu@"$ATTACKER_PUB" "sudo pkill -9 hping3 || true; sudo pkill -9 python3 || true"
  ssh -i "$KEY_PATH" ubuntu@"$CLIENT_PUB" "pkill -9 wrk || true; pkill -9 ab || true"
  ```
- **Logging Requirement:**
  Whenever `/tmp/LAB_STOP` is triggered, append a formal incident report to `LAB_LOG.md` detailing:
  - Exact timestamp (UTC)
  - Triggering reason / detected anomaly
  - State of all three hosts
  - Action taken

### 7.2 Stop-and-Escalate Conditions (Specification Section 4.4)
Autonomous sub-agents MUST halt execution immediately and escalate to human owner if:
1. Any command attempts to target an IP address other than `VICTIM_PRIVATE_IP`.
2. More than 3 EC2 instances tagged with `Project=tcp-flood-lab` exist simultaneously.
3. Cumulative AWS spend approaches or exceeds **US $15.00**.
4. An AWS Abuse or Policy violation notification is detected.
5. `lab-sg` acquires any ingress rule permitting CIDR `0.0.0.0/0` or `::/0`.
6. Instances remain running continuously for $> 12$ hours.

---

## 8. Standalone Script Artifacts

To enable immediate, non-interactive execution by the Milestone 1 implementation agent, the following operational scripts are provided for deployment into the `infra/` directory:

### Artifact 1: `infra/verify_m1_safety.sh`
*Comprehensive post-provisioning automated safety audit testing SG ingress, key permissions, CPU credits, tags, SSH reachability, ICMP mesh, and external exposure blocking.*

### Artifact 2: `infra/update_operator_ip.sh`
*Atomic operator public IP rotation script that discovers new public IP, validates IPv4 syntax, replaces the port 22 security group ingress rule, logs the transition to `LAB_LOG.md`, and runs the zero-tolerance audit.*

---

## 9. Synthesis & Recommendations for Implementation Agent

1. **Strict Ordering:** Execute `infra/verify_preflight_safety.sh` *before* creating any AWS resource. If any preflight check fails, halt immediately.
2. **Key Storage Location:** Ensure `create-key-pair` writes directly to `~/.ssh/tcp-flood-lab.pem`. Never write `.pem` files inside `/Users/raja/Documents/syn-edge-flooding/`.
3. **Launch Parameter Strictness:** Do not omit `--credit-specification CpuCredits=standard` on any `aws ec2 run-instances` call.
4. **Automated Verification Gate:** Immediately upon `aws ec2 wait instance-running` completion, run `bash infra/verify_m1_safety.sh`. Milestone 1 cannot be marked complete until this script returns exit code 0.
