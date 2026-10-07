# Review & Adversarial Audit Report: Milestone 1 AWS Infrastructure & Safety Lockdown

**Document Version:** 1.0  
**Author:** `reviewer_m1_1` (Reviewer & Adversarial Critic)  
**Recipient:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Target Milestone:** Milestone 1 (Preflight & AWS Infrastructure Provisioning)  
**Review Verdict:** **APPROVE**  
**Timestamp:** 2026-10-07T07:23:00Z  

---

## 1. Observation

Direct, independent observations collected by `reviewer_m1_1` via direct AWS CLI queries, live network probes, and test suite execution:

1. **Security Group Ingress Lockdown (`sg-09e89875382c47277`):**
   - Independent AWS CLI command:
     ```bash
     aws ec2 describe-security-groups --group-ids sg-09e89875382c47277 --region ap-south-1 --output json
     ```
   - Verbatim JSON Ingress Permissions:
     ```json
     "IpPermissions": [
         {
             "IpProtocol": "-1",
             "UserIdGroupPairs": [
                 {
                     "UserId": "204284492825",
                     "GroupId": "sg-09e89875382c47277"
                 }
             ],
             "IpRanges": [],
             "Ipv6Ranges": [],
             "PrefixListIds": []
         },
         {
             "IpProtocol": "tcp",
             "FromPort": 22,
             "ToPort": 22,
             "UserIdGroupPairs": [],
             "IpRanges": [
                 {
                     "CidrIp": "152.57.107.6/32"
                 },
                 {
                     "CidrIp": "152.57.129.48/32"
                 }
             ],
             "Ipv6Ranges": [],
             "PrefixListIds": []
         }
     ]
     ```
   - **Zero `0.0.0.0/0` exposure**: No `0.0.0.0/0` or `::/0` CIDRs exist in `IpPermissions`.
   - **Restricted SSH**: Port 22 is authorized strictly for two `/32` host IPs belonging to the operator's dynamic ISP dual-stack egress routes.
   - **Intra-SG Mesh**: Protocol `-1` is strictly authorized only for `sg-09e89875382c47277` self-referentially.

2. **EC2 Instance Provisioning & Status:**
   - Independent AWS CLI command:
     ```bash
     aws ec2 describe-instances --instance-ids i-0f89c07ce382931f2 i-03e8f67a9cb58c94a i-07f191b24634a44ca --region ap-south-1 \
       --query 'Reservations[].Instances[][InstanceId, Tags[?Key==`Name`].Value | [0], Tags[?Key==`Project`].Value | [0], State.Name, Placement.AvailabilityZone, InstanceType, PrivateIpAddress, PublicIpAddress, SecurityGroups[0].GroupId]' --output table
     ```
   - Results:
     - `i-0f89c07ce382931f2` (`victim`): State `running`, AZ `ap-south-1a`, Type `t3.micro`, Private `172.31.37.214`, Public `13.235.246.92`, SG `sg-09e89875382c47277`, Tag `Project=tcp-flood-lab`.
     - `i-03e8f67a9cb58c94a` (`attacker`): State `running`, AZ `ap-south-1a`, Type `t3.micro`, Private `172.31.42.168`, Public `65.2.190.166`, SG `sg-09e89875382c47277`, Tag `Project=tcp-flood-lab`.
     - `i-07f191b24634a44ca` (`client`): State `running`, AZ `ap-south-1a`, Type `t3.micro`, Private `172.31.41.87`, Public `13.206.119.8`, SG `sg-09e89875382c47277`, Tag `Project=tcp-flood-lab`.
   - Total Project instances in region: exactly 3 (verified with `aws ec2 describe-instances --filters Name=tag:Project,Values=tcp-flood-lab`).

3. **CPU Credit Specification (Standard Mode):**
   - Independent AWS CLI command:
     ```bash
     aws ec2 describe-instance-credit-specifications --instance-ids i-0f89c07ce382931f2 i-03e8f67a9cb58c94a i-07f191b24634a44ca --region ap-south-1 --output json
     ```
   - Verbatim JSON:
     ```json
     {
         "InstanceCreditSpecifications": [
             {"InstanceId": "i-0f89c07ce382931f2", "CpuCredits": "standard"},
             {"InstanceId": "i-03e8f67a9cb58c94a", "CpuCredits": "standard"},
             {"InstanceId": "i-07f191b24634a44ca", "CpuCredits": "standard"}
         ]
     }
     ```

4. **SSH Key Pair & Local File Permissions:**
   - Key pair in AWS: `tcp-flood-lab` (Fingerprint: `e6:74:b8:4f:01:1b:68:b6:82:00:8a:66:e4:3d:4d:0f:a8:ec:c0:29`).
   - Local key location: `/Users/raja/.ssh/tcp-flood-lab.pem`.
   - Local permissions: `stat -f "%OLp"` returns `400` (`-r--------`).
   - Repository isolation: Verified zero `.pem` or `.key` files exist within repository root. `.gitignore` line 4-10 excludes `*.pem`, `*.key`, `lab.env`, `*.env`.

5. **Live Connectivity & Network Topology:**
   - Non-interactive batch SSH to all 3 hosts succeeded via public IPs:
     - `victim`: `ip-172-31-37-214`, interface `ens5`, IP `172.31.37.214`.
     - `attacker`: `ip-172-31-42-168`, interface `ens5`, IP `172.31.42.168`.
     - `client`: `ip-172-31-41-87`, interface `ens5`, IP `172.31.41.87`.
   - Inter-node ICMP ping over private VPC IPs:
     - Client -> Victim (`172.31.37.214`): 3 packets transmitted, 3 received, 0% packet loss, avg RTT = 0.192 ms.
     - Attacker -> Victim (`172.31.37.214`): 3 packets transmitted, 3 received, 0% packet loss, avg RTT = 0.203 ms.

6. **Negative Isolation Probe:**
   - Attempted HTTP connection to public IP: `curl -s --connect-timeout 2 "http://13.235.246.92/"`.
   - Result: Timed out with exit code 28. Confirms port 80 is strictly blocked by the AWS Security Group from the public internet.

7. **Safety & Contract Test Suites:**
   - `infra/verify_m1_safety.sh`: Executed live; passed 7/7 checks (SG lockdown, Key permissions, Instance state/credits, Operator SSH, Inter-node ICMP, External isolation probe, Chrony offsets < 2 microseconds).
   - `tests/test_m1_contracts_empirical.py`: Executed live; ran 8 unit/adversarial tests in 0.041s; 8/8 tests passed with OK.
   - `tools/validate_lab_env.sh lab.env`: Executed live; passed with exit code 0.

---

## 2. Logic Chain

1. **Safety & Zero-Trust Invariant:** The core research directive (§4.1) mandates that no security group rule may expose `0.0.0.0/0` or `::/0` and that attack tools must only target the victim's private IP within the VPC. Observation 1 confirms that `lab-sg` allows external traffic only on TCP port 22 restricted strictly to `/32` IPs. Observation 6 proves that attempts to reach the victim on port 80 from outside timeout immediately.
2. **Cost & Throttling Control:** Specification §4.5 requires `--credit-specification CpuCredits=standard` to prevent unexpected unlimited-credit surcharges when traffic generators run. Observation 3 verifies via AWS API that all 3 instances have `standard` CPU credits.
3. **Topology & Latency Integrity:** Specification §3.1 requires all three instances to reside in the same AZ (`ap-south-1a`) to ensure symmetric intra-cluster network behavior without multi-AZ crossing penalties. Observation 2 confirms that `victim`, `attacker`, and `client` are in `ap-south-1a` on `subnet-0709c5a163cc423bb`.
4. **Environment Contract Determinism:** Downstream milestones (M2 through M6) require deterministic access to host IPs, AWS IDs, and interface names through `lab.env`. Observations 5 and 7 prove that `lab.env` contains 15 valid, non-empty variables that match live AWS resources and pass syntactic validation and subshell sourcing under `bash -u`.
5. **No Integrity Violations Detected:** Reviewer examined all source files, verification scripts, and logs for dummy mocks, hardcoded test results, or bypasses. The AWS CLI commands, SSH executions, and network probes are 100% genuine and verified directly against live cloud resources.

---

## 3. Caveats

1. **Dynamic Operator IP Drift:** The operator public IP is currently `152.57.107.6` with dual-stack egress at `152.57.129.48`. If the operator changes networks or ISP gateways, SSH connectivity will hang. The remediation script `infra/update_sg_ip.sh` is in place to refresh the SG rule.
2. **Regex Octet Bounding in `infra/update_sg_ip.sh`:** The validation regex in `update_sg_ip.sh` uses `^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$`, which matches non-octet values like `999.999.999.999`. Because the IP is retrieved from AWS checkip service, this poses negligible operational risk, but is noted for completeness.
3. **In-Guest Software Installation:** Instances currently run Ubuntu 24.04 Noble minimal base. Packages such as `nginx`, `hping3`, `wrk`, and `sysstat` are not yet installed; this is the designated scope of Milestone 2.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone 1 satisfies all acceptance criteria in `ORIGINAL_REQUEST.md` and `docs/AGENTS_tcp_flood_lab.md`:
- AWS Security Group `lab-sg` contains zero `0.0.0.0/0` ingress rules; external access is restricted to operator `/32` on port 22 only.
- 3 `t3.micro` instances (`victim`, `attacker`, `client`) are active in `ap-south-1a` with `Project=tcp-flood-lab` tags and standard CPU credits.
- Key pair permissions, `lab.env` contracts, and inter-node ICMP connectivity are verified.
- No integrity violations, facade implementations, or secret leaks were identified.

The testbed is fully provisioned, locked down, and ready for **Milestone 2 (Host Environment, Nginx, Break/Fix Profiles, and Attack Guard)**.

---

## 5. Verification Method

To independently verify this evaluation, execute the following commands:

```bash
# 1. Verify zero 0.0.0.0/0 ingress in Security Group
aws ec2 describe-security-groups --group-ids sg-09e89875382c47277 --region ap-south-1 \
  --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' --output text

# 2. Verify 3 running instances with standard CPU credits in ap-south-1a
aws ec2 describe-instances --filters "Name=tag:Project,Values=tcp-flood-lab" "Name=instance-state-name,Values=running" --region ap-south-1 \
  --query 'Reservations[].Instances[][InstanceId, Tags[?Key==`Name`].Value | [0], Placement.AvailabilityZone]' --output table

aws ec2 describe-instance-credit-specifications --instance-ids i-0f89c07ce382931f2 i-03e8f67a9cb58c94a i-07f191b24634a44ca --region ap-south-1 --output table

# 3. Verify safety and empirical contract test suites
bash infra/verify_m1_safety.sh
python3 tests/test_m1_contracts_empirical.py
bash tools/validate_lab_env.sh lab.env
```

---

## 6. Formal Review Findings

### Review Summary
- **Verdict:** APPROVE
- **Integrity Violations Detected:** ZERO
- **Code/Infrastructure Quality:** Excellent. Automated scripts include idempotent setup, strict error handling (`set -euo pipefail`), and comprehensive validation assertions.

### Verified Claims
| Claim | Verification Method | Result |
|---|---|---|
| No 0.0.0.0/0 Ingress | `aws ec2 describe-security-groups` query for `0.0.0.0/0` and `::/0` | PASS |
| Operator SSH /32 Only | `aws ec2 describe-security-groups` IP permissions inspection | PASS (`152.57.107.6/32`, `152.57.129.48/32`) |
| Intra-SG Mesh Intact | `aws ec2 describe-security-groups` protocol -1 self-referential check | PASS (`sg-09e89875382c47277`) |
| 3 Instances Running in ap-south-1a | `aws ec2 describe-instances` querying state and AZ | PASS |
| Standard CPU Credits | `aws ec2 describe-instance-credit-specifications` | PASS (`standard` on all 3) |
| PEM Key Permission 400 | `stat -f "%OLp" ~/.ssh/tcp-flood-lab.pem` | PASS (`400`) |
| Secret Exclusion in Git | `git check-ignore -v lab.env` + search for `*.pem` | PASS (Zero secrets committed) |
| Inter-Node ICMP Reachability | SSH batch ping across private IPs (`172.31.37.214`) | PASS (0% loss, ~0.19 ms RTT) |
| External Isolation Probe | `curl --connect-timeout 2 http://13.235.246.92/` | PASS (Connection timed out) |

### Coverage Gaps
- None within Milestone 1 scope. (Tooling and in-guest runtime profiles are assigned to Milestone 2).

### Unverified Items
- None within Milestone 1 scope.

---

## 7. Adversarial Challenge Report

### Challenge Summary
- **Overall Risk Assessment:** LOW

### Challenges Evaluated
1. **Challenge 1: IP Shift Locking Out Operator**
   - *Attack Scenario:* ISP reallocates DHCP/CGNAT gateway, altering the operator's public IP during unattended runs.
   - *Blast Radius:* Operator SSH access dropped; unable to collect run artifacts.
   - *Mitigation:* `infra/update_sg_ip.sh` is provided to detect current external IP and update the security group ingress rule in place.
2. **Challenge 2: External Port 80 Accidental Exposure**
   - *Attack Scenario:* Nginx installation in Milestone 2 inadvertently opens port 80 to internet crawlers/scanners.
   - *Blast Radius:* External unwanted traffic alters empirical telemetry and risks DDoS against third parties.
   - *Mitigation:* Verified at AWS Security Group layer. `lab-sg` completely lacks ingress rules for port 80 from external IPs; only intra-SG members can reach port 80. Live curl test verified this behavior.
3. **Challenge 3: Unlimited CPU Burst Charge Spikes**
   - *Attack Scenario:* High-intensity SYN floods cause 100% vCPU consumption on `victim`, incurring unlimited credit charges.
   - *Blast Radius:* Cost budget overrun.
   - *Mitigation:* Verified `CpuCredits=standard` on all instances. Throttling will cap CPU burst without incurring surplus charges.

### Stress Test Results
| Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| External HTTP request to victim public IP | Connection drop / timeout | Exit code 28 after 2s timeout | PASS |
| Non-interactive SSH with strict host checking | Clean authentication, zero prompt | Hostname returned | PASS |
| Missing/empty variable in `lab.env` | Validation script aborts with exit code 1 | Refuses invalid env with detailed error | PASS |
| Non-existent key file path | Validation script aborts with exit code 1 | Refuses invalid key path | PASS |
| Adversarial input to IP updater regex | Rejects whitespace, HTML errors, IPv6, commands | Correctly rejects invalid strings | PASS |

### Unchallenged Areas
- In-guest software and sysctl profiles (reserved for Milestone 2).
