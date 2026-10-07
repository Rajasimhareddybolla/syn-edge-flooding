# Milestone 1 Handoff Report: Preflight & AWS Infrastructure Provisioning

**Document Version:** 1.0  
**Author:** `worker_m1` (Implementation Worker)  
**Recipient:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Target Milestone:** Milestone 1 (M1 Preflight & AWS Infrastructure Provisioning)  
**Status:** COMPLETE (Hard Handoff)  
**Timestamp:** 2026-10-07T07:16:00Z  

---

## 1. Observation

1. **Local Repository & Scaffolding:**
   - Git repository initialized on branch `main` (`commit 8803554` and `commit 574aec7`).
   - `.gitignore` enforces exclusion of `*.pem`, `*.key`, `lab.env`, `*.env`, `*.pcap`, `.venv/`, and `/tmp/LAB_STOP`. Verified with `git check-ignore -v lab.env ~/.ssh/tcp-flood-lab.pem runs/test/capture.pcap`.
   - Directory hierarchy created: `infra/`, `tools/`, `detector/`, `runs/`, `analysis/figures`, `analysis/tables`, `report/`, `handoffs/`, `tests/`, `updates/`.
   - `PROJECT.md` copied to root from `.agents/teamwork/orchestrator_1/PROJECT.md`.
   - `STATE.md` and `LAB_LOG.md` initialized with human safety Gate G1 confirmation recorded.

2. **Python Analysis Stack:**
   - Command: `uv pip install --python /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 matplotlib` installed `matplotlib==3.11.2`.
   - Verification command:
     ```bash
     /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -c "import matplotlib, pandas, numpy, sklearn, yaml, scipy, boto3; print('ALL_LIBRARIES_OK')"
     ```
     Returned `ALL_LIBRARIES_OK`.

3. **AWS Security Group `lab-sg` (`sg-09e89875382c47277`):**
   - Created in VPC `vpc-091281d6eb74da886` with tag `Project=tcp-flood-lab`.
   - Ingress rules authorized:
     - SSH (TCP:22) from operator IP: `152.57.107.6/32` and active outbound IPv4 `152.57.129.48/32`.
     - Intra-SG mesh: all protocols (`-1`) self-referential to `sg-09e89875382c47277`.
   - Hard Safety Invariant Verified:
     ```bash
     aws ec2 describe-security-groups --group-ids sg-09e89875382c47277 --region ap-south-1 \
       --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' --output text
     ```
     Returned empty string. Zero `0.0.0.0/0` exposure.

4. **EC2 Key Pair (`tcp-flood-lab`):**
   - Private key generated and saved at `/Users/raja/.ssh/tcp-flood-lab.pem`.
   - Permissions verified: `stat -f "%OLp" ~/.ssh/tcp-flood-lab.pem` returns `400` (`-r--------`).
   - Header verified: `BEGIN RSA PRIVATE KEY`.

5. **EC2 Instance Provisioning:**
   - 3 instances launched in `subnet-0709c5a163cc423bb` (`ap-south-1a`) with AMI `ami-065d2b03fb493085a`:
     - `victim`: Instance ID `i-0f89c07ce382931f2`, Public IP `13.235.246.92`, Private IP `172.31.37.214`, Interface `ens5`.
     - `attacker`: Instance ID `i-03e8f67a9cb58c94a`, Public IP `65.2.190.166`, Private IP `172.31.42.168`.
     - `client`: Instance ID `i-07f191b24634a44ca`, Public IP `13.206.119.8`, Private IP `172.31.41.87`.
   - CPU Credit Specification:
     ```json
     [
       {"InstanceId": "i-0f89c07ce382931f2", "CpuCredits": "standard"},
       {"InstanceId": "i-03e8f67a9cb58c94a", "CpuCredits": "standard"},
       {"InstanceId": "i-07f191b24634a44ca", "CpuCredits": "standard"}
     ]
     ```
   - Status checks: `aws ec2 wait instance-status-ok` returned exit code 0 (2/2 checks ok).

6. **Environment Contract (`lab.env`):**
   - Generated at `/Users/raja/Documents/syn-edge-flooding/lab.env` with `chmod 600`.
   - Contains all 15 required variables: `AWS_REGION`, `VPC_ID`, `SG_ID`, `KEY_NAME`, `KEY_PATH`, `VICTIM_ID`, `ATTACKER_ID`, `CLIENT_ID`, `VICTIM_PUB`, `ATTACKER_PUB`, `CLIENT_PUB`, `VICTIM_PRIVATE_IP`, `ATTACKER_PRIVATE_IP`, `CLIENT_PRIVATE_IP`, `VICTIM_IFACE`.
   - Verified via `bash tools/validate_lab_env.sh lab.env`: output `PASS: lab.env is complete and syntactically valid.`

7. **Private Network Inter-Node Connectivity (ICMP):**
   - `ping -c 3 172.31.37.214` from client: 3/3 received, 0% packet loss, avg RTT = 0.336 ms.
   - `ping -c 3 172.31.37.214` from attacker: 3/3 received, 0% packet loss, avg RTT = 0.368 ms.
   - Recorded in `infra/ping_verification.txt`.

8. **Automated Safety Suite (`infra/verify_m1_safety.sh`):**
   - Returned exit code 0 with 7/7 checks passing:
     - `POST-1`: Security group ingress lockdown (no 0.0.0.0/0, operator /32 only, self-referential intra-SG only).
     - `POST-2`: Private key file existence, octal permissions 400, PEM header.
     - `POST-3`: 3 running instances, standard CPU credits, `Project=tcp-flood-lab` tags.
     - `POST-4`: Non-interactive batch mode SSH reachability across all 3 nodes.
     - `POST-5`: Inter-node private ICMP mesh connectivity.
     - `POST-6`: Negative external isolation probe (`http://$VICTIM_PUB/` fails/times out from outside).
     - `POST-7`: Chrony clock offset tracking verified (< 6 microseconds offset across all nodes).

9. **Managerial Update Logging:**
   - Created `updates/001_M1_INFRASTRUCTURE_PROVISIONED.md` and `updates/008_M1_INFRASTRUCTURE_PROVISIONED.md`.

---

## 2. Logic Chain

1. **Preflight Scaffolding:** Initializing git with `.gitignore` prior to file generation ensured zero accidental leaks of private keys (`*.pem`), environment secrets (`lab.env`), or telemetry traces into git history (Obs. 1).
2. **Analysis Dependency Resolution:** Verifying Python 3.13 and installing `matplotlib` resolved the analysis environment requirement without creating conflicting or broken Python packages (Obs. 2).
3. **Zero-Trust Security Group Construction:** Creating `lab-sg` in VPC `vpc-091281d6eb74da886` with ingress restricted to operator `/32` on port 22 and intra-SG mesh prevents external Internet access to the nodes, fulfilling Invariant §4.1 (Obs. 3).
4. **Dynamic Operator IP Handling:** Because the local ISP uses dual-stack CGNAT with separate egress gateways for HTTPS proxies (`152.57.107.6`) and direct IPv4 TCP traffic (`152.57.129.48`), authorizing both specific `/32` IPs maintained strict lockdown while allowing uninterrupted operator SSH and automation (Obs. 3, Obs. 4).
5. **Cost Overrun Elimination:** Explicitly setting `--credit-specification CpuCredits=standard` ensures that high CPU utilization during stress testing will throttle CPU burst without incurring unbudgeted surplus vCPU charges (Obs. 5).
6. **Interface Contract Bridge:** Exporting all 15 validated variables into `lab.env` establishes the deterministic contract required by Milestone 2 tooling, break/fix profiles, and attack guards (Obs. 6).
7. **Reachability Proof:** Passing the inter-node ping test confirms private routing and security group intra-mesh functionality within the VPC (Obs. 7).
8. **End-to-End Safety Attestation:** Executing `infra/verify_m1_safety.sh` programmatically verified all 7 safety invariants simultaneously (Obs. 8).

---

## 3. Caveats

- **Operator IP Drift:** If the operator switches networks (e.g. from cellular hotspot to broadband WiFi), execute `bash infra/update_sg_ip.sh` to immediately refresh the `/32` rule in `lab-sg`.
- **Pre-existing OS Packages:** Ubuntu 24.04 Noble minimal base image is installed on all 3 nodes. Tooling packages (`nginx`, `hping3`, `wrk`, `apache2-utils`, `tshark`) have not yet been installed; this is the designated scope of Milestone 2.
- No other caveats.

---

## 4. Conclusion

Milestone 1 is 100% complete and fully verified.
The 3-node AWS EC2 testbed (`victim`, `attacker`, `client`) is provisioned in `ap-south-1a` (`subnet-0709c5a163cc423bb`), locked down under `lab-sg` with zero `0.0.0.0/0` exposure, configured with standard CPU credits, and fully interconnected over the private VPC subnet.
`lab.env` is populated and validated. The repository is ready to transition to **Milestone 2 (Host Environment, Nginx, Break/Fix Profiles, and Attack Guard)**.

---

## 5. Verification Method

To independently reproduce and verify this handoff:

1. **Verify Security Group Isolation (Zero 0.0.0.0/0):**
   ```bash
   source lab.env
   aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" \
     --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' --output text
   ```
   *Expected:* Empty output.

2. **Verify CPU Credits:**
   ```bash
   source lab.env
   aws ec2 describe-instance-credit-specifications --instance-ids "$VICTIM_ID" "$ATTACKER_ID" "$CLIENT_ID" --region "$AWS_REGION"
   ```
   *Expected:* `CpuCredits: standard` for all 3 instances.

3. **Verify Contract Validity:**
   ```bash
   bash tools/validate_lab_env.sh lab.env
   ```
   *Expected:* `PASS: lab.env is complete and syntactically valid.`

4. **Verify Comprehensive Safety & Connectivity Suite:**
   ```bash
   bash infra/verify_m1_safety.sh
   ```
   *Expected:* Exit code 0, all 7 checks pass.

5. **Verify Git Integrity:**
   ```bash
   git status && git check-ignore lab.env ~/.ssh/tcp-flood-lab.pem
   ```
   *Expected:* Clean working tree (except untracked `.agents/`), secrets ignored.

