# Milestone 1 Adversarial Challenge Report: Network Security & Host Reachability

**Document Version:** 1.0  
**Author:** `challenger_m1_1` (Empirical Challenger)  
**Recipient:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Target Milestone:** Milestone 1 (M1 Preflight & AWS Infrastructure Provisioning)  
**Status:** COMPLETE (Hard Handoff)  
**Empirical Verdict:** **APPROVE**  
**Timestamp:** 2026-10-07T07:21:00Z  

---

## 1. Observation

1. **AWS Security Group `lab-sg` (`sg-09e89875382c47277`):**
   - Command: `aws ec2 describe-security-groups --group-ids sg-09e89875382c47277 --region ap-south-1 --output json`
   - Ingress Permissions observed:
     - Rule 1 (Intra-SG Mesh): `IpProtocol: -1`, `UserIdGroupPairs: [{"GroupId": "sg-09e89875382c47277"}]`.
     - Rule 2 (SSH port 22): `IpProtocol: tcp`, `FromPort: 22`, `ToPort: 22`, `IpRanges: [{"CidrIp": "152.57.107.6/32"}, {"CidrIp": "152.57.129.48/32"}]`.
   - Ingress rule check for `0.0.0.0/0` and `::/0`: Zero matches.
   - Instance security group association: Every instance (`victim` `i-0f89c07ce382931f2`, `attacker` `i-03e8f67a9cb58c94a`, `client` `i-07f191b24634a44ca`) is attached strictly and exclusively to `sg-09e89875382c47277`.

2. **External Non-Permitted Port Exposure Probing:**
   - Probed non-permitted ports (`80`, `8080`, `443`, `8000`, `2222`, `3306`, `53`) against public IPs (`victim: 13.235.246.92`, `attacker: 65.2.190.166`, `client: 13.206.119.8`) with 2.0s TCP socket connect timeouts from operator host:
     - `VICTIM (13.235.246.92)`: All 7 ports returned `connect_ex == 35` (EWOULDBLOCK / ETIMEDOUT). Zero open ports.
     - `ATTACKER (65.2.190.166)`: All 7 ports returned `connect_ex == 35` (EWOULDBLOCK / ETIMEDOUT). Zero open ports.
     - `CLIENT (13.206.119.8)`: All 7 ports returned `connect_ex == 35` (EWOULDBLOCK / ETIMEDOUT). Zero open ports.
   - Probed HTTP port 80 via `curl -m 3 http://$IP/`:
     - Victim: `curl: (28) Connection timed out after 3006 milliseconds` (exit code: 28).
     - Attacker: `curl: (28) Connection timed out after 3006 milliseconds` (exit code: 28).
     - Client: `curl: (28) Connection timed out after 3006 milliseconds` (exit code: 28).
   - Probed external ICMP ping via `ping -c 2 -W 2000 $IP`:
     - Victim: 2 packets transmitted, 0 received, 100.0% packet loss (exit code: 2).
     - Attacker: 2 packets transmitted, 0 received, 100.0% packet loss (exit code: 2).
     - Client: 2 packets transmitted, 0 received, 100.0% packet loss (exit code: 2).

3. **Live Non-Interactive Batch SSH Reachability:**
   - Key file `/Users/raja/.ssh/tcp-flood-lab.pem`: octal permissions `400` (`-r--------`), valid `BEGIN RSA PRIVATE KEY` format.
   - Batch command:
     ```bash
     ssh -i ~/.ssh/tcp-flood-lab.pem -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 ubuntu@<IP> "hostname && whoami && ip -br addr"
     ```
   - Results:
     - `victim (13.235.246.92)`: returned `ip-172-31-37-214`, `ubuntu`, interface `ens5 UP 172.31.37.214/20`. Exit code 0.
     - `attacker (65.2.190.166)`: returned `ip-172-31-42-168`, `ubuntu`, interface `ens5 UP 172.31.42.168/20`. Exit code 0.
     - `client (13.206.119.8)`: returned `ip-172-31-41-87`, `ubuntu`, interface `ens5 UP 172.31.41.87/20`. Exit code 0.

4. **Inter-Node Private Mesh ICMP Reachability:**
   - Executed live `ping -c 3` across all 6 directional pairs within the private subnet:
     - `attacker -> victim (172.31.37.214)`: 3/3 packets received, 0% loss, rtt avg = 0.191 ms.
     - `attacker -> client (172.31.41.87)`: 3/3 packets received, 0% loss, rtt avg = 0.173 ms.
     - `client -> victim (172.31.37.214)`: 3/3 packets received, 0% loss, rtt avg = 0.206 ms.
     - `client -> attacker (172.31.42.168)`: 3/3 packets received, 0% loss, rtt avg = 0.172 ms.
     - `victim -> attacker (172.31.42.168)`: 3/3 packets received, 0% loss, rtt avg = 0.185 ms.
     - `victim -> client (172.31.41.87)`: 3/3 packets received, 0% loss, rtt avg = 0.186 ms.

5. **Safety Constraints & Cost Controls:**
   - Credit specification: All 3 instances return `CpuCredits: standard`.
   - Resource tags: All 3 instances tagged with `Project=tcp-flood-lab`.
   - Comprehensive safety suite `bash infra/verify_m1_safety.sh`: 7/7 checks passed (exit code 0).

---

## 2. Logic Chain

1. **Security Group Ingress Lockdown (Obs. 1, Obs. 2):**
   - The Security Group `sg-09e89875382c47277` authorizes TCP port 22 strictly from operator `/32` addresses and all traffic strictly within the self-referential group ID.
   - Empirical port probes against ports 80, 8080, 443, 8000, 2222, 3306, and 53 across all public IPs proved that any inbound attempt from outside is dropped at the AWS hypervisor level before reaching the hosts (Obs. 2).
   - Negative external HTTP probes and external ICMP probes confirmed 100% timeout and packet loss, proving zero unintended surface exposure.

2. **Host Accessibility & Automation Reliability (Obs. 3):**
   - Automated test runners require non-interactive, passwordless, prompt-free SSH.
   - Batch SSH test using `~/.ssh/tcp-flood-lab.pem` connected to all 3 nodes without terminal prompts, confirming key validity, correct permissions (`400`), and operational SSH daemons.

3. **Subnet Mesh Connectivity (Obs. 4):**
   - The research protocol requires high-speed, direct communication between attacker, client, and victim over the private VPC subnet (`172.31.0.0/20`).
   - The 6-way ICMP mesh test demonstrated 0% packet loss and sub-millisecond latencies (<0.21 ms avg RTT) across all node pairs, confirming intra-SG security group rules and VPC routing operate without impediment.

4. **Safety & Budget Invariants (Obs. 5):**
   - Standard CPU credits guarantee that sustained synthetic workload execution will not incur uncapped burst billing charges.

---

## 3. Caveats

- **Operator Public IP Changes:** If the operator workstation shifts network interfaces or connects through a different public egress, SSH access will time out until `bash infra/update_sg_ip.sh` is invoked to update the authorized `/32` rule.
- **Milestone Boundary:** Nginx, attack tools (`hping3`), generators (`wrk`), and kernel profiling are deliberately uninstalled in M1; their installation and validation are scoped to Milestone 2.

---

## 4. Conclusion

Empirical Verdict: **APPROVE**

Milestone 1 network security and host reachability have been rigorously and adversarially tested. All acceptance criteria for Milestone 1 are completely satisfied:
- Zero public ingress exposure (`0.0.0.0/0`) exists in the AWS Security Group.
- Non-permitted ports (80, 8080, 443, etc.) and external ICMP pings are 100% blocked and dropped.
- Batch SSH is fully functional and non-interactive across all 3 nodes.
- Full mesh inter-node ICMP reachability is confirmed with 0% packet loss and <0.25 ms latency.
- Standard CPU credit configuration is enforced on all instances.

The testbed is fully qualified to proceed to **Milestone 2**.

---

## 5. Verification Method

To independently reproduce the empirical findings in this report:

1. **Verify Security Group Isolation (Zero 0.0.0.0/0 ingress):**
   ```bash
   source lab.env
   aws ec2 describe-security-groups --group-ids "$SG_ID" --region "$AWS_REGION" \
     --query 'SecurityGroups[0].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) || contains(Ipv6Ranges[].CidrIpv6, `::/0`)]' --output text
   ```
   *Expected:* Empty output.

2. **Probe Non-Permitted External Ports (Empirical SG Drop Test):**
   ```bash
   source lab.env
   for port in 80 8080 443; do
     nc -z -w 2 "$VICTIM_PUB" "$port" || echo "Port $port blocked as expected (exit: $?)"
   done
   ```
   *Expected:* Connection timeout / exit code != 0.

3. **Verify Batch SSH Reachability:**
   ```bash
   source lab.env
   for ip in "$VICTIM_PUB" "$ATTACKER_PUB" "$CLIENT_PUB"; do
     ssh -i "$KEY_PATH" -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 ubuntu@"$ip" "hostname"
   done
   ```
   *Expected:* Output prints `ip-172-31-37-214`, `ip-172-31-42-168`, `ip-172-31-41-87` with exit code 0.

4. **Verify Intra-Mesh ICMP Ping:**
   ```bash
   source lab.env
   ssh -i "$KEY_PATH" -o BatchMode=yes -o StrictHostKeyChecking=accept-new ubuntu@"$ATTACKER_PUB" "ping -c 3 $VICTIM_PRIVATE_IP"
   ssh -i "$KEY_PATH" -o BatchMode=yes -o StrictHostKeyChecking=accept-new ubuntu@"$CLIENT_PUB" "ping -c 3 $VICTIM_PRIVATE_IP"
   ```
   *Expected:* 3 packets transmitted, 3 received, 0% packet loss.

5. **Run Comprehensive Safety Test Suite:**
   ```bash
   bash infra/verify_m1_safety.sh
   ```
   *Expected:* Exit code 0, 7/7 checks passed.

