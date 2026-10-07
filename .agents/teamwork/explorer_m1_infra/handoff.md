# Handoff Report: Milestone 1 Infrastructure Provisioning Strategy

**Agent:** `explorer_m1_infra` (Explorer Archetype)  
**Parent Orchestrator:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Working Directory:** `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_infra`  
**Target Milestone:** Milestone 1 (Preflight & AWS Infrastructure Provisioning)  
**Deliverable File:** `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_infra/plan_m1_infra.md`  

---

## 1. Observation

1. **Working Directory & Git State:**
   - Command: `git status` in `/Users/raja/Documents/syn-edge-flooding`
   - Output: `fatal: not a git repository (or any of the parent directories): .git`
   - Target root lacks `.git`, `STATE.md`, `LAB_LOG.md`, `.gitignore`, and required directories (`infra/`, `tools/`, `detector/`, `runs/`, `analysis/`, `report/`, `handoffs/`, `tests/`).

2. **Python Environment & Dependencies:**
   - System Python: `/opt/homebrew/bin/python3` is Python 3.14.8.
   - Framework Python: `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` is Python 3.13.2.
   - `uv`: `/Library/Frameworks/Python.framework/Versions/3.13/bin/uv` is version 0.11.23.
   - Command: `uv pip list --python /Library/Frameworks/Python.framework/Versions/3.13/bin/python3`
   - Observed Packages: `pandas 3.0.5`, `numpy 2.5.1`, `scikit-learn 1.9.1`, `scipy 1.18.1`, `pyyaml 6.0.3`, `boto3 1.43.99`, `pytest 9.1.1` are present.
   - `matplotlib` is NOT installed in Python 3.13.

3. **AWS Cloud Configuration & Topology:**
   - Command: `aws configure get region` -> `ap-south-1`.
   - Command: `aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text` -> `vpc-091281d6eb74da886`.
   - Command: `aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-091281d6eb74da886" "Name=availability-zone,Values=ap-south-1a" --query 'Subnets[0].SubnetId' --output text` -> `subnet-0709c5a163cc423bb`.
   - Command: `aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id --query Parameter.Value --output text` -> `ami-065d2b03fb493085a`.
   - Command: `curl -s https://checkip.amazonaws.com` -> `152.57.107.6`.

4. **Clean Baseline Check:**
   - Command: `aws ec2 describe-key-pairs --key-names tcp-flood-lab` -> `InvalidKeyPair.NotFound`.
   - Command: `aws ec2 describe-security-groups --group-names lab-sg` -> `InvalidGroup.NotFound`.
   - Command: `aws ec2 describe-instances --filters "Name=tag:Project,Values=tcp-flood-lab" "Name=instance-state-name,Values=pending,running,stopping,stopped"` -> 0 instances found.
   - Local Key File: `/Users/raja/.ssh/tcp-flood-lab.pem` does not exist (`ls: No such file or directory`).

5. **AWS CLI Command Syntax Dry Run:**
   - Command: `aws ec2 run-instances --dry-run --image-id ami-065d2b03fb493085a --instance-type t3.micro --security-group-ids sg-0221386d1b9d1e9e8 --subnet-id subnet-0709c5a163cc423bb --credit-specification CpuCredits=standard --associate-public-ip-address`
   - Output: `aws: [ERROR]: An error occurred (DryRunOperation) when calling the RunInstances operation: Request would have succeeded, but DryRun flag is set.`
   - Verifies that `--associate-public-ip-address`, `--subnet-id`, `--security-group-ids`, and `--credit-specification` are mutually valid in AWS CLI v2.

---

## 2. Logic Chain

1. **Preflight Environment Readiness (Observations 1 & 2):**
   - Because Git is uninitialized, running `git init -b main` in the project root establishes the VCS boundary.
   - Because private keys (`*.pem`), environment credentials (`lab.env`), and packet captures (`runs/**/capture.pcap`) must never be leaked to version control (§4.6, §5.1), writing `.gitignore` before making any commits is an absolute prerequisite.
   - Because 4 of the 5 required analysis packages (`pandas`, `numpy`, `scikit-learn`, `pyyaml`) are already present in Python 3.13, running `uv pip install --python /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 matplotlib` provides an instant, zero-friction resolution for Phase 0 Step 3.

2. **Security & Boundary Enforcement (Observations 3 & 4):**
   - Specification §4.1 mandates that no rule with source `0.0.0.0/0` or `::/0` may exist.
   - By creating `lab-sg` in `vpc-091281d6eb74da886` and granting port 22 access strictly to `152.57.107.6/32`, operator SSH connectivity is guaranteed while preventing any inbound internet scanning.
   - By adding a self-referential ingress rule (`--protocol -1 --source-group $SG_ID`), all 3 cluster instances can communicate freely across all protocols (including ICMP ping, HTTP port 80, and raw flood traffic) over their private VPC IPs.

3. **Topology Co-location & Cost Prevention (Observations 3 & 5):**
   - Launching all three instances (`victim`, `attacker`, `client`) in the exact same subnet (`subnet-0709c5a163cc423bb`) in `ap-south-1a` eliminates cross-AZ latency variation and intra-region data transfer fees.
   - Passing `--credit-specification CpuCredits=standard` ensures `t3.micro` nodes throttle CPU to baseline when burst credits are exhausted, rather than incurring unlimited burst surcharge fees (§4.5).
   - Passing `--associate-public-ip-address` allows the operator to reach each node via SSH using public IPs while keeping inter-node traffic strictly private.

4. **Contract Adherence & Inter-Node Verification (Observations 1, 3, 4):**
   - The M1 -> M2 interface contract requires 15 exported variables in `lab.env`: `AWS_REGION`, `VPC_ID`, `SG_ID`, `KEY_NAME`, `KEY_PATH`, `VICTIM_ID`, `ATTACKER_ID`, `CLIENT_ID`, `VICTIM_PUB`, `ATTACKER_PUB`, `CLIENT_PUB`, `VICTIM_PRIVATE_IP`, `ATTACKER_PRIVATE_IP`, `CLIENT_PRIVATE_IP`, `VICTIM_IFACE`.
   - Running non-interactive SSH with `-o StrictHostKeyChecking=accept-new` dynamically discovers `VICTIM_IFACE` (e.g., `ens5`).
   - Executing `ping -c 3 $VICTIM_PRIVATE_IP` from client and attacker validates that the intra-SG mesh functions before any subsequent workload or instrumentation is deployed.

---

## 3. Caveats

1. **Dynamic Operator Public IP:**
   - If the operator's ISP changes the public IP (e.g., mobile hotspot reconnect), SSH connections will time out.
   - *Mitigation:* The plan provides `infra/update_sg_ip.sh`, which automatically detects the shifted IP and updates the security group rule.
2. **Cloud-init Initialization Latency:**
   - Newly launched Ubuntu 24.04 AMIs require 45–90 seconds for cloud-init and sshd to reach an active listening state.
   - *Mitigation:* The provisioning script incorporates `aws ec2 wait instance-status-ok` and SSH retry flags to eliminate race conditions.
3. **No Unaccounted Variables:**
   - The 15 variables in `lab.env` match the exact names expected by `PROJECT.md` and downstream Milestone 2 scripts.

---

## 4. Conclusion

Milestone 1 is completely solvable via a single, idempotent, and hardened automation script (`infra/provision_m1.sh`) backed by exact AWS CLI commands. All security boundaries (zero `0.0.0.0/0`, `/32` restriction), cost controls (`CpuCredits=standard`), and contract schemas (`lab.env`) have been fully specified and documented in `plan_m1_infra.md`.

---

## 5. Verification Method

To verify the strategy independently, the implementer or orchestrator can execute:

1. **Inspect Plan Artifact:**
   ```bash
   cat /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_infra/plan_m1_infra.md
   ```
2. **Execute Milestone 1 Provisioning:**
   ```bash
   bash /Users/raja/Documents/syn-edge-flooding/infra/provision_m1.sh
   ```
3. **Validate Acceptance Criteria:**
   - Ingress lockdown: `aws ec2 describe-security-groups --group-ids $(grep SG_ID lab.env | cut -d'"' -f2) --query 'SecurityGroups[0].IpPermissions[].IpRanges[].CidrIp' --output text` (MUST be only `152.57.107.6/32`).
   - Contract verification: `source lab.env && echo "$VICTIM_PRIVATE_IP $ATTACKER_PRIVATE_IP $CLIENT_PRIVATE_IP"` (MUST output 3 distinct `172.31.x.x` addresses).
   - Ping verification: `cat /Users/raja/Documents/syn-edge-flooding/infra/ping_verification.txt` (MUST show 0% packet loss).
