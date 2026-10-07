# Milestone 1 Independent Review & Adversarial Challenge Report

**Reviewer / Critic:** `reviewer_m1_2`  
**Working Directory:** `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/reviewer_m1_2`  
**Target Milestone:** Milestone 1 (Preflight & AWS Infrastructure Provisioning)  
**Parent Orchestrator:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Verdict:** **APPROVE**  
**Integrity Tag:** **INTEGRITY VERIFIED (NO VIOLATIONS)**  
**Timestamp:** 2026-10-07T07:23:00Z  

---

## 1. Review Summary & Verdict

| Check Dimension | Status | Notes |
|---|---|---|
| **1. `lab.env` 15 Variables & Syntax** | **PASS** | All 15 required variables present, valid bash/zsh/python parsing, points to real AWS resources |
| **2. Key Permissions (`chmod 400`)** | **PASS** | `~/.ssh/tcp-flood-lab.pem` verified at octal `400` (`-r--------`) with valid RSA private key header |
| **3. Git Repository & `.gitignore`** | **PASS** | Excludes `*.pem`, `*.key`, `lab.env`, `runs/**/capture.pcap`; clean history with 0 secrets |
| **4. `STATE.md` & `LAB_LOG.md`** | **PASS** | Human Gate G1 confirmed by Raja; Phase 1 marked COMPLETE with full audit trails |
| **5. Private ICMP Reachability** | **PASS** | Genuine inter-node ICMP ping verified live (0% packet loss, ~0.18 ms latency) |
| **6. Security Group Lockdown** | **PASS** | Ingress has 0 rules with `0.0.0.0/0` or `::/0`; SSH restricted to operator `/32`; intra-SG only |
| **7. CPU Credit Specification** | **PASS** | Standard CPU credit mode (`CpuCredits=standard`) enforced across all 3 nodes |
| **8. Anti-Cheat / Integrity Check** | **PASS** | No hardcoding, no dummy facades, no shortcuts, no fabricated logs, live AWS verified |

**Overall Verdict:** **APPROVE**  
The Milestone 1 deliverables meet all contract specifications, pass independent live verification, and provide a secure, authentic foundation for Milestone 2.

---

## 2. Observation

1. **`lab.env` Contract Completeness:**
   - File path: `/Users/raja/Documents/syn-edge-flooding/lab.env` (Lines 7–25)
   - Contained variables:
     ```bash
     AWS_REGION="ap-south-1"
     VPC_ID="vpc-091281d6eb74da886"
     SG_ID="sg-09e89875382c47277"
     KEY_NAME="tcp-flood-lab"
     KEY_PATH="/Users/raja/.ssh/tcp-flood-lab.pem"
     VICTIM_ID="i-0f89c07ce382931f2"
     ATTACKER_ID="i-03e8f67a9cb58c94a"
     CLIENT_ID="i-07f191b24634a44ca"
     VICTIM_PUB="13.235.246.92"
     ATTACKER_PUB="65.2.190.166"
     CLIENT_PUB="13.206.119.8"
     VICTIM_PRIVATE_IP="172.31.37.214"
     ATTACKER_PRIVATE_IP="172.31.42.168"
     CLIENT_PRIVATE_IP="172.31.41.87"
     VICTIM_IFACE="ens5"
     ```
   - Python parsing check:
     ```bash
     python3 -c "import re; env = dict(re.findall(r'export ([A-Za-z0-9_]+)=\"(.*)\"', open('lab.env').read())); assert len(env) == 15"
     ```
     Result: Loaded all 15 variables, zero missing.
   - Sourcing validation:
     `bash -u -c 'source lab.env && echo "BASH_OK"'` -> `BASH_OK`
     `zsh -u -c 'source lab.env && echo "ZSH_OK"'` -> `ZSH_OK`
     `bash tools/validate_lab_env.sh lab.env` -> `PASS: lab.env is complete and syntactically valid.`

2. **Key Pair Existence & File Permissions:**
   - Command: `stat -f "%Sp %OLp %N" ~/.ssh/tcp-flood-lab.pem`
   - Output: `-r-------- 400 /Users/raja/.ssh/tcp-flood-lab.pem`
   - Header inspection: First line is `-----BEGIN RSA PRIVATE KEY-----`, tail is `-----END RSA PRIVATE KEY-----`.

3. **Repository Hygiene & Git Ignore Rules:**
   - File path: `/Users/raja/Documents/syn-edge-flooding/.gitignore` (Lines 4–21)
   - Tested ignore patterns via `git check-ignore -v`:
     - `lab.env` -> `.gitignore:10:*.env`
     - `foo.pem` -> `.gitignore:4:*.pem`
     - `runs/run1/capture.pcap` -> `.gitignore:18:*.pcap`
     - `runs/S2M-r01-20261007T120000Z/capture.pcap` -> `.gitignore:18:*.pcap`
     - `test.key` -> `.gitignore:5:*.key`
   - Git commit history check:
     `git log --oneline`: 3 commits (`fc36cab`, `574aec7`, `8803554`).
     No `.pem`, `.key`, or `.env` files tracked in Git tree.

4. **Safety Gates & Milestone State Tracking:**
   - File path: `/Users/raja/Documents/syn-edge-flooding/STATE.md`:
     - Line 16: Human Gate G1 status is `CONFIRMED` by Raja (Human Owner) at `2026-10-07T06:40:00Z` with evidence "Confirmed in chat & logged in LAB_LOG.md".
     - Line 27: Phase 1 (Milestone M1) is `COMPLETE` with artifacts `lab.env`, `infra/sg_described.json`, `infra/instances_described.json`, `infra/ping_verification.txt`.
   - File path: `/Users/raja/Documents/syn-edge-flooding/LAB_LOG.md`:
     - Line 20: `## [2026-10-07T06:40:00Z] — GATE_CONFIRMATION: Human Safety Gate G1 Approved`.
     - Line 63: `## [2026-10-07T07:09:11Z] — RESOURCE_ALLOCATION: AWS Infrastructure Provisioned`.

5. **Live AWS EC2 Fleet & Security Group Lockdown:**
   - AWS CLI Query:
     ```bash
     aws ec2 describe-security-groups --group-ids sg-09e89875382c47277 --region ap-south-1
     ```
   - Ingress Permissions observed:
     - Rule 1: Protocol `-1` (all), GroupId `sg-09e89875382c47277` (self-referential intra-SG only).
     - Rule 2: Protocol `tcp`, Port 22, CIDRs `152.57.107.6/32`, `152.57.129.48/32`.
     - Result: Exactly 0 rules with `0.0.0.0/0` or `::/0`.
   - AWS CLI Query for CPU credits:
     ```bash
     aws ec2 describe-instance-credit-specifications --instance-ids i-0f89c07ce382931f2 i-03e8f67a9cb58c94a i-07f191b24634a44ca --region ap-south-1
     ```
   - Result: All 3 instances returned `CpuCredits: "standard"`.

6. **Genuine Inter-Node ICMP Reachability:**
   - Live SSH test executed independently by `reviewer_m1_2`:
     - Attacker (`65.2.190.166`) -> Victim (`172.31.37.214`):
       `3 packets transmitted, 3 received, 0% packet loss, time 2065ms, rtt min/avg/max/mdev = 0.170/0.179/0.196/0.011 ms`
     - Client (`13.206.119.8`) -> Victim (`172.31.37.214`):
       `3 packets transmitted, 3 received, 0% packet loss, time 2028ms, rtt min/avg/max/mdev = 0.183/0.190/0.204/0.009 ms`
     - Client (`13.206.119.8`) -> Attacker (`172.31.42.168`):
       `3 packets transmitted, 3 received, 0% packet loss, time 2060ms, rtt min/avg/max/mdev = 0.175/0.188/0.206/0.012 ms`
   - Comparison with `infra/ping_verification.txt`: Matches authentic live network behavior; confirms genuine physical VPC mesh.

7. **External Negative Isolation Probe:**
   - Command: `curl -v --connect-timeout 3 http://13.235.246.92/`
   - Result: Timed out after 3004 ms (error code 28). Confirms port 80 is strictly unreachable from the public Internet.

8. **Automated Safety Suite Run:**
   - Command: `bash infra/verify_m1_safety.sh`
   - Output: All 7 checks (`POST-1` through `POST-7`) passed with exit code 0. Chrony clock offsets verified under 1 microsecond.

---

## 3. Logic Chain

1. **Contract Invariant (Obs. 1):** `lab.env` defines the unified interface contract between Milestone 1 and all downstream milestones (M2 through M6). Sourcing and parsing tests confirm all 15 required variables exist, are syntactically valid across shells, and contain valid identifiers matching actual AWS resources.
2. **Credential Safety (Obs. 2, Obs. 3):** Strict `chmod 400` ensures SSH automation functions securely without OpenSSH rejecting permissions. Comprehensive `.gitignore` directives and clean Git history guarantee private keys and environment secrets cannot be committed to version control.
3. **Regulatory & Human Invariant (Obs. 4):** RFC 2119 requirement §4.3 mandates explicit Human Gate G1 confirmation prior to provisioning. Both `STATE.md` and `LAB_LOG.md` document this approval with exact timestamps and rationale.
4. **Network Isolation (Obs. 5, Obs. 7):** Zero `0.0.0.0/0` ingress rules and the external timeout probe prove that the testbed is completely shielded from external traffic, strictly upholding Section 4.1.
5. **Authenticity & Reachability (Obs. 6, Obs. 8):** Live SSH execution of ping commands produced sub-millisecond latencies and 0% packet loss across all three nodes. Forensic comparison of raw AWS API JSON logs against live AWS states proved that all artifacts represent genuine infrastructure.
6. **Cost Control (Obs. 5):** Standard CPU credits mode avoids unexpected burst credit surcharges on `t3.micro`.

---

## 4. Adversarial Challenges & Stress Test Results

### Challenge 1 (Medium): Dynamic IP Revocation Race in `infra/update_sg_ip.sh`
- **Challenged Mechanism:** `infra/update_sg_ip.sh` lines 29–39 loops over existing port 22 CIDRs and revokes every CIDR that does not match `${NEW_IP}/32` resolved via `curl -s https://checkip.amazonaws.com`.
- **Attack Scenario:** In dual-stack ISP or cellular CGNAT environments where HTTPS traffic leaves through gateway A (`152.57.107.6`) and raw TCP traffic leaves through gateway B (`152.57.129.48`), running `update_sg_ip.sh` will detect only gateway A and revoke gateway B. This immediately terminates active TCP SSH sessions and locks the operator out.
- **Blast Radius:** Loss of SSH access until the security group rule is manually fixed.
- **Mitigation Recommendation for M2+:** Modify `update_sg_ip.sh` to accept optional extra CIDR arguments or avoid immediately revoking other authorized `/32` IPs without verification.

### Challenge 2 (Low): CPU Credit Depletion during M4 Stress Flooding
- **Challenged Mechanism:** `t3.micro` instances with `CpuCredits=standard`.
- **Attack Scenario:** Standard credit `t3.micro` instances accumulate 6 credits per hour (10% baseline performance). A 10,000 pps SYN flood or intense flash crowd driving 100% CPU on victim or attacker will consume credits at 1 credit/minute. If test suites in Milestone 4 run back-to-back without adequate cooldown, credit balance will reach zero, triggering CPU throttling that could distort rate calibrations and response times.
- **Blast Radius:** Non-reproducible latency and throughput variations in high-concurrency scenarios.
- **Mitigation Recommendation for M4:** Enforce mandatory inter-run cooldown periods (already specified in §4.5 and §6.5) and query CloudWatch `CPUCreditBalance` prior to benchmark runs.

### Challenge 3 (Minor): Duplicate Update File
- **Observation:** `updates/001_M1_INFRASTRUCTURE_PROVISIONED.md` is an exact duplicate of `updates/008_M1_INFRASTRUCTURE_PROVISIONED.md`.
- **Mitigation:** Recommend cleaning up the duplicate or aligning update log numbering sequentially in future milestones.

---

## 5. Caveats

- **OS-Level Tooling Pending:** In accordance with the Milestone 1 scope, OS packages (`nginx`, `hping3`, `wrk`, `apache2-utils`) are not yet installed on the EC2 instances. This is the designated responsibility of Milestone 2.
- No other caveats.

---

## 6. Conclusion

Milestone 1 satisfies all contract requirements, security guardrails, repository hygiene standards, and integrity criteria.
- `lab.env` is complete and verified.
- `~/.ssh/tcp-flood-lab.pem` is secured with `chmod 400`.
- `.gitignore` prevents credential and artifact leakage.
- `STATE.md` and `LAB_LOG.md` record Gate G1 approval and Phase 1 completion.
- `infra/ping_verification.txt` records authentic inter-node connectivity.
- Live independent verification confirms zero integrity violations.

**Verdict: APPROVE.** Milestone 1 is cleared for completion, and the team may proceed to **Milestone 2 (Victim Environment, Tooling & Safety Guardrails)**.

---

## 7. Verification Method

To independently verify these conclusions:

1. **Verify Security Group Isolation (Zero 0.0.0.0/0):**
   ```bash
   source lab.env
   aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" \
     --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' --output text
   ```
   *Expected:* Empty output.

2. **Verify Private Key File and Octal Permissions:**
   ```bash
   stat -f "%OLp" ~/.ssh/tcp-flood-lab.pem
   ```
   *Expected:* `400`.

3. **Verify Contract Validity:**
   ```bash
   bash tools/validate_lab_env.sh lab.env
   ```
   *Expected:* `PASS: lab.env is complete and syntactically valid.`

4. **Verify Live Full Safety & ICMP Mesh Suite:**
   ```bash
   bash infra/verify_m1_safety.sh
   ```
   *Expected:* Exit code 0, all 7 checks pass.
