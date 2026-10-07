# Handoff Report — Milestone 1 Safety, Credential Isolation & Verification Strategy

**Author:** `explorer_m1_safety`  
**Role:** Explorer & Safety Specialist  
**Working Directory:** `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety`  
**Target Recipient:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Handoff Type:** Hard (Task Complete)  

---

## 1. Observation

Direct observations and evidence gathered from the repository, normative specifications, and live cloud environment:

1. **Safety Invariants in Normative Specification (`docs/AGENTS_tcp_flood_lab.md`):**
   - **Lines 93–96 (Section 4.1 Scope):**  
     > "The security group MUST NOT contain any rule with source `0.0.0.0/0` or `::/0`. SSH is allowed only from the operator's current public IP `/32`. No lab traffic may leave the VPC. No scanning, no third-party hosts."
   - **Lines 115–117 (Section 4.5 Cost Control):**  
     > "Tag everything `Project=tcp-flood-lab`. Use `--credit-specification CpuCredits=standard` on t3 instances to avoid surprise unlimited-credit charges (note: CPU may throttle; record `CPUCreditBalance` in the run metadata)."
   - **Lines 224–234 (Section 6 Phase 1 Steps & Acceptance):**  
     > "3. Create SG `lab-sg` in that VPC (tag Project). Ingress: TCP 22 from `$MYIP/32`; all protocols from `lab-sg` itself (`--source-group`). Nothing else."  
     > "4. Key pair: `aws ec2 create-key-pair --key-name tcp-flood-lab --query KeyMaterial --output text > ~/.ssh/tcp-flood-lab.pem && chmod 400 ~/.ssh/tcp-flood-lab.pem`."  
     > "Acceptance. (a) `aws ec2 describe-security-groups` shows no `0.0.0.0/0` rule; (b) 3 instances tagged and running; (c) pings succeed; (d) `lab.env` complete."

2. **Acceptance Criteria in Original User Request (`ORIGINAL_REQUEST.md`):**
   - **Lines 30–34:**  
     > "AWS Security Group contains no 0.0.0.0/0 ingress rules; SSH allowed only from current operator /32."  
     > "`lab.env` generated with private IPs; inter-node reachability verified via ICMP ping."

3. **Current Live Cloud Baseline (`ap-south-1`):**
   - `aws sts get-caller-identity`: Principal `arn:aws:iam::2042********:root` authenticated.
   - `aws configure get region`: Region `ap-south-1` confirmed.
   - `aws ec2 describe-instances --filters Name=tag:Project,Values=tcp-flood-lab`: Returned empty string (0 active instances).
   - `aws ec2 describe-key-pairs --key-names tcp-flood-lab`: Returned error code 254 (`InvalidKeyPair.NotFound`).
   - `aws ec2 describe-security-groups --group-names lab-sg`: Returned error code 254 (`InvalidGroup.NotFound`).
   - `curl -s https://checkip.amazonaws.com`: Operator public IP is `152.57.107.6`.
   - `aws ec2 describe-subnets --filters Name=availability-zone,Values=ap-south-1a`: Subnet `subnet-0709c5a163cc423bb` in default VPC `vpc-091281d6eb74da886` with 4,091 available IP addresses confirmed.

4. **Local Host Environment & Tool Verification:**
   - macOS BSD stat syntax confirmed: `stat -f "%OLp" ~/.ssh` returned `700`.
   - `jq -e` validation logic tested on mock security group data:
     - `[.SecurityGroups[].IpPermissions[].IpRanges[]? | select(.CidrIp == "0.0.0.0/0")] | length == 0` returned `true` (exit code 0) on compliant SG, and caught violations (exit code 1) when `0.0.0.0/0` was present.

---

## 2. Logic Chain

From the direct observations above, the safety and verification requirements are established through the following reasoning steps:

1. **Security Group Ingress Boundary (From Obs 1 & 2):**  
   Because the lab will generate intentional TCP flooding traffic on port 80 and high-rate SYN packets, allowing open ingress (`0.0.0.0/0`) would expose the web server to Internet botnets, triggering false alarm corruption or external abuse. Restricting external ingress exclusively to operator port 22 (`152.57.107.6/32`) and restricting port 80/inter-node traffic strictly to the security group itself (`--source-group $SG_ID`) creates an impermeable outer boundary. An automated JQ assertion script is required to enforce this zero-tolerance policy.
2. **Credential Isolation and Least Privilege (From Obs 1 & 4):**  
   Because the SSH key grants root execution capability across all 3 nodes, generating the key file directly to `~/.ssh/tcp-flood-lab.pem` isolates it completely from the project git repository `/Users/raja/Documents/syn-edge-flooding`. Applying `chmod 400` restricts read access strictly to the owner. Setting `.gitignore` rules for `*.pem` and `lab.env` ensures that even if temporary keys or environment dumps are created locally, they cannot be committed to Git.
3. **Financial Protection and Burst Credit Throttling (From Obs 1):**  
   AWS T3 instances launch with `unlimited` credit specification by default, billing $0.05 per vCPU-hour when CPU credits exhaust. During SYN floods (e.g., scenario S2H at 10,000 pps), the victim instance will run at 100% CPU utilization. Setting `--credit-specification CpuCredits=standard` at launch time guarantees that the instance merely throttles rather than accumulating variable monetary charges, ensuring project spend stays strictly within the $15.00 ceiling. Tagging all instances with `Project=tcp-flood-lab` ensures tracking and clean teardown.
4. **Automated Verification Harness (From Obs 1, 2, 3 & 4):**  
   Manual inspection is error-prone. By packaging the pre-provisioning checks into `verify_preflight_safety.sh` and post-provisioning checks into `verify_m1_safety.sh`, the orchestrator and implementer can deterministically gate Milestone 1 completion with exit code 0. Furthermore, an external negative test (verifying that `curl http://$VICTIM_PUB/` times out from the public internet) provides empirical proof that port 80 is not exposed.

---

## 3. Caveats

1. **Operator Public IP Drift:** Home broadband and mobile connections frequently rotate public IP addresses. If the operator's public IP changes, SSH connections will hang. To remediate this safely without opening wide CIDRs, `proposed_update_operator_ip.sh` provides an atomic rule rotation that preserves the strict `/32` restriction.
2. **CPU Credit Throttling Impact on Research:** By selecting `standard` credit specification, instances will experience CPU throttling if run continuously at high load. This is a known, expected trade-off documented in `docs/AGENTS_tcp_flood_lab.md` (Section 4.5). Instance `CPUCreditBalance` must be recorded in run metadata in later milestones.
3. **AWS VPC Anti-Spoofing Behavior:** As noted in specification Section 4.1, AWS VPC infrastructure drops spoofed-source packets (`--rand-source`). All attacks will originate from the attacker node's private IP (`172.31.xx.xx`). This is an inherent cloud environment constraint to be documented in threats to validity.

---

## 4. Conclusion

Milestone 1 safety and credential verification is fully formulated, mathematically bounded, and operationalized. 

The safety strategy is detailed in:
- **`plan_m1_safety.md`** — Comprehensive Safety, Credential Isolation, and Verification Strategy report.
- **`proposed_verify_m1_safety.sh`** — Standalone post-provisioning verification script covering all 6 verification dimensions (Security Group, Private Key, CPU Credits, Tags, SSH Reachability, Inter-Node ICMP, and Negative External Exposure).
- **`proposed_update_operator_ip.sh`** — Standalone operator public IP rotation script for resilient operations.

Milestone 1 implementation can safely proceed immediately under these specifications.

---

## 5. Verification Method

To independently verify this strategy and ensure the testbed meets all acceptance criteria:

1. **Inspect Artifacts:**
   - View `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety/plan_m1_safety.md`
   - View `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety/proposed_verify_m1_safety.sh`
   - View `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety/proposed_update_operator_ip.sh`

2. **Preflight Verification Command (Before Provisioning):**
   ```bash
   aws sts get-caller-identity
   aws configure get region
   aws ec2 describe-instances --filters Name=tag:Project,Values=tcp-flood-lab
   ```
   *Expected result:* Account authenticated, region is `ap-south-1`, zero instances returned.

3. **Post-Provisioning Verification Command (After Provisioning):**
   ```bash
   bash /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety/proposed_verify_m1_safety.sh
   ```
   *Expected result:* Script outputs `🎉 ALL MILESTONE 1 SAFETY AND VERIFICATION CHECKS PASSED!` and exits with code 0.

4. **Invalidation Conditions:**
   - Any rule with `0.0.0.0/0` or `::/0` appears in `lab-sg`.
   - Any instance has `CpuCredits == "unlimited"`.
   - Private key file permissions are anything other than `400`.
   - External curl to `http://$VICTIM_PUB/` returns HTTP 200 (indicating port 80 is leaking to the public Internet).
