# Milestone 2 Specification Mining Report: Contracts, Schemas & Boundary Conditions

**Document Version:** 1.0  
**Author:** `spec_miner_m2_contracts` (Specification Miner)  
**Recipient:** `orchestrator_1_gen2` (`c915840f-b40f-4c6b-9b28-92a18579e73d`)  
**Target Milestone:** Milestone 2 (Victim Environment, Tooling & Safety Guardrails)  
**Status:** COMPLETE (Hard Handoff)  
**Timestamp:** 2026-10-07T08:00:00Z  

---

## 1. Observation

Direct observations extracted from authoritative project documentation, environment contracts, and active repository artifacts:

1. **`ORIGINAL_REQUEST.md` (lines 13–15, 30–33):**
   - **R1:** "Provision an isolated 3-node AWS EC2 testbed (victim, attacker, client; t3.micro Ubuntu 24.04 in default VPC) in accordance with the safety guardrails in docs/AGENTS_tcp_flood_lab.md. ... Attack tools must be bound by a fail-safe attack guard that strictly restricts target IP to victim private IP, duration <= 60 s, and SYN flood rate <= 10,000 pps."
   - **Acceptance Criteria (Infrastructure & Safety):**
     - "attack_guard.sh passes automated self-tests refusing unauthorized IPs, durations > 60 s, and rates > 10,000 pps."
     - "lab.env generated with private IPs; inter-node reachability verified via ICMP ping."

2. **`PROJECT.md` (lines 14–28, 66, 78–83, 112–126):**
   - **Features Inventory for M2:**
     - Feature 1: Target IP Verification (Strict enforcement that attack target matches `VICTIM_PRIVATE_IP`, source: survey_spec §12.1).
     - Feature 2: Duration Clamping (Enforce maximum duration <= 60s via timeout).
     - Feature 3: Rate Limiting (SYN) (Limit hping3 interval to >= u100 [<= 10,000 pps]).
     - Feature 4: Connection Hold Limit (Enforce max connection count <= 2,000).
     - Feature 5: Emergency Kill Switch (Host-wide kill switch via presence of `/tmp/LAB_STOP`).
     - Feature 10: RST Suppression Rule (Drop outbound kernel TCP RST on attacker for raw SYNs).
     - Feature 11: Sysctl Break/Fix Profiles (Toggle vulnerable vs mitigated kernel state).
     - Feature 12: Sysctl Defaults Snapshot (Snapshot original system kernel defaults).
     - Feature 13: Chrony Synchronization Check (Check clock offset across testbed nodes < 50ms).
   - **M2 Scope:** "Ubuntu package installs, Nginx setup with backlog=128, sysctl break/fix profiles, snapshot defaults, attacker iptables RST drop rule, `attack_guard.sh` and `guard_selftest.sh` verification."
   - **M2 -> M3 Interface Contract:**
     - "Victim responds with HTTP 200 to `curl http://$VICTIM_PRIVATE_IP/`."
     - "`set_profile.sh {break|fix}` toggles `tcp_syncookies`."
     - "Attacker drops RST to victim: `iptables -C OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP`."
     - "`attack_guard.sh` refuses invalid IP, duration > 60s, rate > 10,000 pps, conns > 2,000, or kill switch present."

3. **`docs/AGENTS_tcp_flood_lab.md`:**
   - **§4.1 Scope (lines 93–96):**
     - "Attack tools MUST only target the victim private IP from the attacker instance. Nothing else, ever."
     - "No lab traffic may leave the VPC. No scanning, no third-party hosts."
   - **§4.2 Attack Guard (lines 98–105):**
     - "`attack_guard.sh <tool> <args>` on the attacker MUST refuse unless ALL hold:
       - target IP == `VICTIM_PRIVATE_IP` from `lab.env` (string-exact);
       - duration ≤ 60 s (enforced with `timeout`);
       - SYN rate ≤ 10,000 packets/s (hping3 interval ≥ `u100`); **never** use `--flood` or `--faster`;
       - connection-hold count ≤ 2,000;
       - a kill switch file `/tmp/LAB_STOP` is absent (checked before launch; all tools launched via `timeout`)."
   - **§4.3 Human Gates (lines 107–110):**
     - "G2 (before first attack run): Human confirms attack guard test output (`guard_selftest.txt`)."
   - **§4.4 Stop-and-Escalate Conditions (lines 112–114):**
     - "Stop all traffic (`touch /tmp/LAB_STOP` on attacker), write the reason in `LAB_LOG.md`, notify the human..."
   - **§6 Phase 2 — Victim and Tooling Setup (lines 236–250):**
     - Step 1: All hosts: `sudo apt-get update && sudo apt-get install -y python3-pip sysstat jq chrony tcpdump`.
     - Step 2: Victim: `sudo apt-get install -y nginx`. Replace default page with ~1 KB static `index.html`. Set `listen 80 backlog=128;` in default server block. Reload.
     - Step 3: Client: `sudo apt-get install -y apache2-utils wrk curl`.
     - Step 4: Attacker: `sudo apt-get install -y hping3`.
     - Step 5: Sysctl break configuration: applied via `/etc/sysctl.d/99-lab.conf` with named profiles toggled by `tools/set_profile.sh {break|fix|default}`:
       - `break`: `net.ipv4.tcp_syncookies=0`, `net.ipv4.tcp_max_syn_backlog=128`, `net.core.somaxconn=128`.
       - `fix`: `net.ipv4.tcp_syncookies=1` (others unchanged).
       - `default`: restores snapshot defaults.
     - Step 6: Attacker RST suppression: `sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP`. Save exact rule in `infra/attacker_rules.txt`; must be removed in Phase 10 teardown.
     - Step 7: Snapshot defaults before changing anything: `sysctl net.ipv4.tcp_syncookies net.ipv4.tcp_max_syn_backlog net.core.somaxconn net.ipv4.tcp_synack_retries net.ipv4.ip_local_port_range` → `infra/sysctl_defaults.txt`. Also `ulimit -n` on client.
     - Acceptance: "200 from client; both sysctl profiles switch correctly (verify with `sysctl` output); RST rule present on attacker; defaults file saved."
   - **§6 Phase 4 — Traffic Tools (lines 262–273):**
     - Step 1: `attack_guard.sh` per 4.2 plus `guard_selftest.sh` proving refusal for (a) non-victim IP, (b) duration 61 s, (c) interval below `u100`, (d) `--flood`, (e) 2,001 connections, (f) `/tmp/LAB_STOP`. Save output to `infra/guard_selftest.txt`. Wait for Human Gate G2.
     - Step 3: SYN flood tool invocation: `hping3 -S -p 80 -i u{INTERVAL} $VICTIM_PRIVATE_IP` wrapped in `timeout {D}`. Intensity levels: L=`u10000`, M=`u1000`, H=`u100`. Prohibition: Do not use `--rand-source`.
     - Step 4: Connection flood tool invocation: `tools/conn_hold.py --host $VICTIM_PRIVATE_IP --port 80 --n {N} --hold {D} --ramp 5`. Levels: L=100, M=500, H=2000.

4. **`lab.env` Configuration Values:**
   - `VICTIM_PRIVATE_IP="172.31.37.214"`
   - `ATTACKER_PRIVATE_IP="172.31.42.168"`
   - `CLIENT_PRIVATE_IP="172.31.41.87"`
   - `VICTIM_IFACE="ens5"`

---

## 2. Logic Chain

1. **Safety Enforcement as Fail-Closed State Machine (Linking Obs 1, 2, 3):**
   - The attack guard is the sole barrier preventing unauthorized packet transmission across or outside the AWS VPC.
   - Any failure to parse arguments, ambiguity in flags, absence of `VICTIM_PRIVATE_IP`, or presence of `/tmp/LAB_STOP` MUST immediately evaluate to a refusal state.
   - A fail-closed architecture dictates that `attack_guard.sh` refuses by default unless every parameter explicitly satisfies the bounding criteria.

2. **Refusal Exit Code and Output Contract Derivation (Linking Obs 2, 3):**
   - In UNIX scripting and automated test harnesses (such as Python `unittest` and `pytest`), subshell assertions require deterministic exit codes:
     - Exit code `0` MUST exclusively denote authorized execution (or successful validation under `--dry-run`).
     - Refusal MUST return a non-zero exit code (standardized as exit code `1`).
     - If `timeout` terminates the tool upon reaching the execution deadline, standard `timeout` returns exit code `124`.
   - Error messages MUST be emitted to `stderr` with a machine-parseable prefix `❌ GUARD REFUSAL:` to enable unambiguous verification by `guard_selftest.sh` and test runners.

3. **Multi-Tool CLI Parsing Nuances (Linking Obs 2, 3):**
   - `hping3` and `conn_hold.py` have distinct CLI signatures:
     - `hping3` accepts interval as `-i u100`, `-i u1000`, `-i 1`, or `--interval u100`, with target IP as a positional argument anywhere in the argument vector. It also features dangerous flags `--flood`, `--faster`, and `--rand-source`.
     - `conn_hold.py` uses GNU-style named options: `--host <IP>`, `--port <PORT>`, `--n <COUNT>`, and `--hold <SECS>`.
   - Therefore, `attack_guard.sh` cannot assume a fixed positional argument index for the target IP or duration. It must iterate over all arguments, extract host candidates and duration values, and reject any unrecognized or non-compliant options.

4. **Kernel State Determinism (Linking Obs 2, 3):**
   - In Linux kernels (including Ubuntu 24.04 Noble), the effective listen backlog is bounded by `min(listen_backlog, net.core.somaxconn)`.
   - In Milestone 2, `listen 80 backlog=128;` in Nginx and `net.core.somaxconn=128` create a strictly deterministic accept queue limit of 128.
   - For `net.ipv4.tcp_max_syn_backlog=128`, the SYN queue capacity is strictly bounded.
   - Toggling `set_profile.sh break` disables SYN cookies (`tcp_syncookies=0`), making the server immediately vulnerable to SYN queue exhaustion. Toggling `set_profile.sh fix` enables cookies (`tcp_syncookies=1`), allowing the kernel to survive SYN floods without queue state exhaustion.
   - `set_profile.sh default` guarantees reproducible teardown and recovery by restoring original system defaults from `infra/sysctl_defaults.txt`.

5. **Human Gate G2 Non-Repudiation (Linking Obs 1, 3):**
   - `guard_selftest.sh` is an automated validation harness executed on the attacker node.
   - Saving its complete execution log to `infra/guard_selftest.txt` establishes the verifiable cryptographic and empirical evidence required for Human Gate G2 approval before any attack scenario (Phase 4/5) can execute.

---

## 3. Caveats

1. **Local vs Remote Execution Context:**
   - `tools/set_profile.sh` must execute on the `victim` node (or over SSH) with root permissions.
   - `tools/attack_guard.sh` and `tools/guard_selftest.sh` must execute on the `attacker` node where `hping3` and `iptables` reside.
   - `infra/sysctl_defaults.txt` combines outputs from `victim` (sysctl parameters) and `client` (`ulimit -n`).
2. **Dynamic Operator IP Drift (CGNAT):**
   - Operator public IP shifts require updating the `/32` SSH rule in `lab-sg` via `bash infra/update_sg_ip.sh` prior to issuing SSH commands to the nodes.
3. **No Code Implementation in Specification Mining:**
   - In accordance with the Spec Miner role instructions, this document formalizes interfaces, schemas, and contracts. It does not implement project code or create files outside `.agents/teamwork/`.

---

## 4. Conclusion

The specification mining investigation for Milestone 2 is complete. Authoritative requirements from `ORIGINAL_REQUEST.md`, `PROJECT.md`, `lab.env`, and `docs/AGENTS_tcp_flood_lab.md` have been extracted, synthesized, and formalized below.

The deliverables are structured into:
1. **Features Discovered Table (18 features across 6 functional categories)**
2. **Edge Cases Table (15 edge cases with concrete observed behaviors)**
3. **M2 -> M3 Interface Contract Specification**
4. **Authoritative File Schemas (`sysctl_defaults.txt`, `attacker_rules.txt`, `guard_selftest.txt`)**
5. **Exact CLI Invocation Signatures and Exit Codes**
6. **Error Logging and Failure Recording Standards**

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Safety & Guard | Target IP Verification | Enforces target IP matches `VICTIM_PRIVATE_IP` exactly. | Target IP argument in command line. | Process proceeds to next check. | Stderr message `❌ GUARD REFUSAL`, exit code 1. | `docs/AGENTS_tcp_flood_lab.md` §4.2 |
| 2 | Safety & Guard | Duration Clamping | Enforces attack duration is ≤ 60 seconds. | `--duration`, `-d`, `timeout <N>`, or `--hold <N>`. | Tool execution wrapped in `timeout`. | Stderr message `❌ GUARD REFUSAL`, exit code 1 if > 60s. | `docs/AGENTS_tcp_flood_lab.md` §4.2 |
| 3 | Safety & Guard | SYN Rate Limiting | Restricts hping3 interval to ≥ `u100` (≤ 10,000 pps). | `-i u<N>`, `-i m<N>`, `-i <N>`, `--interval`. | Allowed if interval ≥ u100. | Stderr message `❌ GUARD REFUSAL`, exit code 1 if < u100. | `docs/AGENTS_tcp_flood_lab.md` §4.2 |
| 4 | Safety & Guard | Flood Flag Prohibition | Strictly blocks `--flood` and `--faster` in hping3. | Command line flags. | None. | Stderr message `❌ GUARD REFUSAL`, exit code 1. | `docs/AGENTS_tcp_flood_lab.md` §4.2 |
| 5 | Safety & Guard | Connection Hold Limit | Restricts connection hold count to ≤ 2,000 sockets. | `-n <N>`, `--n <N>`, `--conns <N>`, `--count <N>`. | Allowed if N ≤ 2000. | Stderr message `❌ GUARD REFUSAL`, exit code 1 if > 2000. | `docs/AGENTS_tcp_flood_lab.md` §4.2 |
| 6 | Safety & Guard | Emergency Kill Switch | Host-wide kill switch preventing execution when `/tmp/LAB_STOP` exists. | File presence check on `/tmp/LAB_STOP`. | If absent, proceed. | If present pre-launch, exit code 1; if created mid-run, kill child and exit 1. | `docs/AGENTS_tcp_flood_lab.md` §4.2, §4.4 |
| 7 | Safety & Guard | Guard Dry-Run / Validation | Evaluates command compliance without sending packets. | `--dry-run` or `--check` flag. | Stdout `[GUARD_AUTHORIZED]`, exit code 0. | Normal refusal stderr and exit code 1 if invalid. | `explorer_m2_guard` & Phase 4.1 |
| 8 | Networking | RST Suppression Rule | Drops attacker kernel outbound TCP RST to victim for SYN flood realism. | Victim private IP (`$VICTIM_PRIVATE_IP`). | Active iptables drop rule in OUTPUT chain. | If omitted, SYN_RECV entries clear prematurely on victim. | `docs/AGENTS_tcp_flood_lab.md` §246 |
| 9 | Networking | Rule Persistence & Check | Queries and records attacker iptables rule. | `iptables -C OUTPUT ...`. | Exit code 0 if present; exit code 1 if absent. | Returns exit code 1 when rule missing. | `docs/AGENTS_tcp_flood_lab.md` §246, `PROJECT.md` §81 |
| 10 | Kernel Configuration | Break Sysctl Profile | Sets victim kernel to vulnerable state (no cookies, backlog=128). | `tools/set_profile.sh break`. | Stdout confirmed settings (`tcp_syncookies=0`), exit code 0. | Stderr error, exit code 1 on bad argument or permission failure. | `docs/AGENTS_tcp_flood_lab.md` §243 |
| 11 | Kernel Configuration | Fix Sysctl Profile | Sets victim kernel to mitigated state (cookies on, backlog=128). | `tools/set_profile.sh fix`. | Stdout confirmed settings (`tcp_syncookies=1`), exit code 0. | Stderr error, exit code 1 on bad argument or permission failure. | `docs/AGENTS_tcp_flood_lab.md` §243 |
| 12 | Kernel Configuration | Default Sysctl Profile | Restores victim kernel parameters to pre-experiment snapshot. | `tools/set_profile.sh default`. | Stdout confirmed settings, exit code 0. | Stderr error, exit code 1 on failure. | `PROJECT.md` §26, `DISPATCH.md` |
| 13 | Telemetry & Audit | Sysctl Defaults Snapshot | Snapshots original system kernel parameters and client ulimit. | `sysctl` queries on victim and `ulimit -n` on client. | Writes `infra/sysctl_defaults.txt`. | Missing values fail snapshot generation. | `docs/AGENTS_tcp_flood_lab.md` §247 |
| 14 | Web Server | Nginx Backlog Configuration | Configures Nginx listen socket with accept backlog=128. | `/etc/nginx/sites-available/default`. | Nginx listens on port 80 with backlog 128. | Syntax error on `nginx -t` if malformed. | `docs/AGENTS_tcp_flood_lab.md` §240 |
| 15 | Web Server | Static Payload Serving | Deploys minimal ~1 KB static HTML page. | `/var/www/html/index.html`. | 1 KB static payload served with HTTP 200. | Missing file results in HTTP 404. | `docs/AGENTS_tcp_flood_lab.md` §240 |
| 16 | Time Synchronization | Chrony Offset Verification | Measures clock synchronization offset across testbed nodes. | `chronyc tracking`. | Offset value in milliseconds. | Offset > 50 ms triggers batch abort. | `docs/AGENTS_tcp_flood_lab.md` §181 |
| 17 | Validation & Self-Test | Automated Guard Self-Test | Regression suite verifying attack guard refusal on all invariant violations. | `tools/guard_selftest.sh`. | Writes `infra/guard_selftest.txt`, exit code 0. | Exit code 1 if any refusal fails or valid command fails. | `docs/AGENTS_tcp_flood_lab.md` §265 |
| 18 | Human Governance | Safety Gate G2 Attestation | Formal human approval of attack guard self-test evidence prior to attacks. | `infra/guard_selftest.txt`. | Status updated to CONFIRMED in `STATE.md`. | Attack execution blocked until G2 confirmed. | `docs/AGENTS_tcp_flood_lab.md` §109 |

---

## Edge Cases

| # | Feature | Input / Scenario | Observed / Specified Behavior |
|---|---------|------------------|-------------------------------|
| 1 | Target IP Verification | Hostname or URL: `http://172.31.37.214` or `victim.local` | Refused. Strict string-exact match against `VICTIM_PRIVATE_IP` IPv4 literal required. Exit code 1. |
| 2 | Target IP Verification | CIDR notation: `172.31.37.214/32` or subnet `172.31.37.0/24` | Refused. String does not match literal IP `172.31.37.214`. Exit code 1. |
| 3 | Target IP Verification | Victim Public IP: `13.235.246.92` | Refused. Only private VPC IP allowed. Exit code 1. |
| 4 | Target IP Position | Target IP in middle of arguments: `hping3 -S 172.31.37.214 -p 80 -i u1000` | Allowed. Parser inspects entire argument vector for target IP match. |
| 5 | SYN Rate Limiting | Microsecond boundary: `hping3 -S -p 80 -i u100 172.31.37.214` | Permitted. Interval `u100` equals exactly 10,000 pps, which is within the allowed limit. |
| 6 | SYN Rate Limiting | Microsecond boundary violation: `hping3 -S -p 80 -i u99 172.31.37.214` | Refused. Interval `u99` (~10,101 pps) exceeds the 10,000 pps cap. Stderr warning, exit code 1. |
| 7 | SYN Rate Limiting | Interval flag variations: `-iu100`, `-i u100`, `--interval=u100`, `--interval u100` | Parser normalizes attached and separate argument formats; correctly extracts interval. |
| 8 | Forbidden Flags | `--flood` flag passed to hping3 | Refused immediately. Stderr explains unmetered flood is prohibited. Exit code 1. |
| 9 | Forbidden Flags | `--faster` flag passed to hping3 | Refused immediately. Stderr explains `--faster` (1 µs interval) is prohibited. Exit code 1. |
| 10 | Duration Clamping | Duration boundary: `--duration 60` vs `--duration 61` | 60 s permitted; 61 s refused with error message indicating duration cap violation. Exit code 1. |
| 11 | Duration Clamping | Duration via `timeout` prefix: `attack_guard.sh timeout 61 hping3 ...` | Refused. Guard parses duration from `timeout` prefix and enforces <= 60 s limit. Exit code 1. |
| 12 | Connection Hold Limit | Count boundary: `conn_hold.py --n 2000` vs `--n 2001` | 2,000 permitted; 2,001 refused with error indicating max connection cap exceeded. Exit code 1. |
| 13 | Pre-Launch Kill Switch | `/tmp/LAB_STOP` exists prior to calling `attack_guard.sh` | Refused immediately before reading arguments or launching child process. Exit code 1. |
| 14 | Mid-Flight Kill Switch | `/tmp/LAB_STOP` created while attack process is actively executing | Live watchdog loop detects file within 200 ms, sends SIGTERM then SIGKILL, exits 1. |
| 15 | Environment Absence | `lab.env` missing or `VICTIM_PRIVATE_IP` unset in shell | Fail-closed. Emits error stating unable to resolve `VICTIM_PRIVATE_IP`, exits 1. |

---

## M2 -> M3 Interface Contract Specification

### 1. Host Readiness Contract
Prior to transitioning from Milestone 2 to Milestone 3:
- **Package Installation:**
  - `victim`: `python3-pip`, `sysstat`, `jq`, `chrony`, `tcpdump`, `nginx`.
  - `attacker`: `python3-pip`, `sysstat`, `jq`, `chrony`, `tcpdump`, `hping3`.
  - `client`: `python3-pip`, `sysstat`, `jq`, `chrony`, `tcpdump`, `apache2-utils`, `wrk`, `curl`.
- **Clock Synchronization:**
  - `chronyc tracking` on all three nodes must report clock offset < 50 ms.
- **Inter-Node Reachability:**
  - Private ICMP ping and HTTP reachability between all nodes verified.

### 2. Nginx Response Format Contract
- **Listen Configuration:** `/etc/nginx/sites-available/default` must contain:
  ```nginx
  listen 80 backlog=128;
  ```
- **Static Payload:** `/var/www/html/index.html` must exist with file size approximately 1,024 bytes (1 KB).
- **Service Verification Command:**
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 "http://$VICTIM_PRIVATE_IP/"
  ```
- **Expected Output:**
  - Stdout: `200`
  - Exit code: `0`

### 3. Sysctl Profile Toggling Contract (`tools/set_profile.sh`)
- **CLI Signature:**
  ```bash
  tools/set_profile.sh {break|fix|default}
  ```
- **Profile Parameters:**
  - `break`:
    - `net.ipv4.tcp_syncookies = 0`
    - `net.ipv4.tcp_max_syn_backlog = 128`
    - `net.core.somaxconn = 128`
  - `fix`:
    - `net.ipv4.tcp_syncookies = 1`
    - `net.ipv4.tcp_max_syn_backlog = 128`
    - `net.core.somaxconn = 128`
  - `default`:
    - Restores values recorded in `infra/sysctl_defaults.txt`.
- **Output Behavior:**
  - Stdout displays applied profile and queried values from `sysctl net.ipv4.tcp_syncookies net.ipv4.tcp_max_syn_backlog net.core.somaxconn`.
  - Exit code `0` on success.
  - Invalid argument or non-root invocation prints usage to stderr and exits with code `1`.

### 4. Attacker IPTables Rule Contract (`infra/attacker_rules.txt`)
- **Rule Specification:**
  ```bash
  sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d "$VICTIM_PRIVATE_IP" -j DROP
  ```
- **Active Rule Verification:**
  ```bash
  sudo iptables -C OUTPUT -p tcp --tcp-flags RST RST -d "$VICTIM_PRIVATE_IP" -j DROP
  ```
  Must return exit code `0`.
- **Scope Restriction:** The rule MUST specify `-d $VICTIM_PRIVATE_IP`. Global RST drops are strictly forbidden.
- **Teardown Deletion Command:**
  ```bash
  sudo iptables -D OUTPUT -p tcp --tcp-flags RST RST -d "$VICTIM_PRIVATE_IP" -j DROP
  ```

### 5. Attack Guard Contract (`tools/attack_guard.sh`)
- **CLI Signature:**
  ```bash
  tools/attack_guard.sh [--dry-run] [--duration <secs>] <tool> <tool_args...>
  ```
- **Safety Invariants Enforced (Fail-Closed):**
  1. Target IP matches `VICTIM_PRIVATE_IP` from `lab.env` exactly.
  2. Duration ≤ 60 seconds (enforced via system `timeout`).
  3. SYN flood rate ≤ 10,000 pps (`interval >= u100`; no `--flood` or `--faster`).
  4. Connection hold count ≤ 2,000 sockets.
  5. Emergency kill switch `/tmp/LAB_STOP` absent.
- **Refusal Behavior:**
  - Immediately rejects execution without spawning attack traffic.
  - Emits error message to `stderr`: `❌ GUARD REFUSAL: <detailed_reason>`.
  - Appends refusal log entry with UTC timestamp to `/tmp/attack_guard.log`.
  - Exits with non-zero exit code `1`.
- **Authorization Behavior:**
  - With `--dry-run`: prints `[GUARD_AUTHORIZED]` summary and exits with code `0`.
  - Standard invocation: launches command wrapped in `timeout`, runs live watchdog checking for `/tmp/LAB_STOP`, returns command exit code.

---

## Authoritative File Schemas

### 1. `infra/sysctl_defaults.txt` Schema
Format: Key-value lines separated by `=` matching standard `sysctl` output format, followed by client ulimit.
```ini
# Baseline System Defaults Captured Pre-Modification
# Host: victim (172.31.37.214) / client (172.31.41.87)
# Timestamp: 2026-10-07T07:16:00Z
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 512
net.core.somaxconn = 4096
net.ipv4.tcp_synack_retries = 5
net.ipv4.ip_local_port_range = 32768	60999
client_ulimit_n = 1024
```
**Parser Regex:** `^([a-z0-9_.]+)\s*=\s*(.+)$`

### 2. `infra/attacker_rules.txt` Schema
Format: Documented shell commands for rule application, verification, and teardown.
```ini
# Attacker Output RST Suppression Rule
# Target: 172.31.37.214 (VICTIM_PRIVATE_IP)
# Description: Drops outbound kernel TCP RST packets to victim to prevent closing half-open connections.

# Rule Application:
iptables -A OUTPUT -p tcp --tcp-flags RST RST -d 172.31.37.214 -j DROP

# Rule Verification (Exit code 0 if active):
iptables -C OUTPUT -p tcp --tcp-flags RST RST -d 172.31.37.214 -j DROP

# Rule Teardown (Milestone 6 / Phase 10):
iptables -D OUTPUT -p tcp --tcp-flags RST RST -d 172.31.37.214 -j DROP
```

### 3. `infra/guard_selftest.txt` Schema
Format: Structured human-readable test log containing header, individual test cases with command, result, exit code, and final Gate G2 summary.
```text
================================================================================
ATTACK GUARD AUTOMATED SELF-TEST REPORT (HUMAN SAFETY GATE G2)
================================================================================
Timestamp: <ISO-8601-UTC>
Host: attacker (172.31.42.168)
Target Authorized IP: 172.31.37.214 (VICTIM_PRIVATE_IP)
Script Under Test: tools/attack_guard.sh
Runner: tools/guard_selftest.sh
================================================================================

TEST 1: Non-victim unauthorized IP refusal
Command:   tools/attack_guard.sh hping3 -S -p 80 -i u1000 10.0.0.1
Result:    REFUSED (Exit Code: 1)
Output:    ❌ GUARD REFUSAL: Unauthorized target IP '10.0.0.1' does not match VICTIM_PRIVATE_IP (172.31.37.214).
Status:    PASS

TEST 2: Duration exceeding 60 seconds refusal (duration 61s)
Command:   tools/attack_guard.sh --duration 61 hping3 -S -p 80 -i u1000 172.31.37.214
Result:    REFUSED (Exit Code: 1)
Output:    ❌ GUARD REFUSAL: Duration 61s exceeds maximum allowed cap of 60s.
Status:    PASS

TEST 3: SYN flood rate exceeding 10,000 pps refusal (interval < u100)
Command:   tools/attack_guard.sh hping3 -S -p 80 -i u99 172.31.37.214
Result:    REFUSED (Exit Code: 1)
Output:    ❌ GUARD REFUSAL: SYN rate exceeds limit. Interval 'u99' (< u100) exceeds 10,000 pps.
Status:    PASS

TEST 4: Forbidden flag --flood refusal
Command:   tools/attack_guard.sh hping3 -S -p 80 --flood 172.31.37.214
Result:    REFUSED (Exit Code: 1)
Output:    ❌ GUARD REFUSAL: Forbidden flag --flood detected. Attack rate exceeds safety bounds.
Status:    PASS

TEST 5: Forbidden flag --faster refusal
Command:   tools/attack_guard.sh hping3 -S -p 80 --faster 172.31.37.214
Result:    REFUSED (Exit Code: 1)
Output:    ❌ GUARD REFUSAL: Forbidden flag --faster detected. Attack rate exceeds safety bounds.
Status:    PASS

TEST 6: Connection hold count exceeding 2,000 refusal (2,001 connections)
Command:   tools/attack_guard.sh conn_hold.py --host 172.31.37.214 --port 80 --n 2001 --hold 30
Result:    REFUSED (Exit Code: 1)
Output:    ❌ GUARD REFUSAL: Connection count 2001 exceeds maximum allowed cap of 2,000.
Status:    PASS

TEST 7: Emergency kill switch file /tmp/LAB_STOP presence refusal
Command:   touch /tmp/LAB_STOP && tools/attack_guard.sh hping3 -S -p 80 -i u1000 172.31.37.214
Result:    REFUSED (Exit Code: 1)
Output:    ❌ GUARD REFUSAL: Emergency kill switch active (/tmp/LAB_STOP exists).
Status:    PASS

TEST 8: Authorized valid bounded invocation authorization (Dry Run)
Command:   tools/attack_guard.sh --dry-run hping3 -S -p 80 -i u1000 172.31.37.214
Result:    PERMITTED (Exit Code: 0)
Output:    [GUARD_AUTHORIZED] All safety invariants verified.
Status:    PASS

================================================================================
SUMMARY: 8/8 CHECKS PASSED. ZERO INVARIANT VIOLATIONS PERMITTED.
HUMAN GATE G2 READY: Awaiting operator confirmation prior to Phase 4/5 attacks.
================================================================================
```

---

## 5. Verification Method

To independently verify this specification report:

1. **Verify M2 Contract Alignment with AGENTS.md:**
   ```bash
   grep -E "(backlog=128|set_profile|attack_guard|guard_selftest|RST)" docs/AGENTS_tcp_flood_lab.md
   ```
   *Expected:* Matches §4.2, §6 Phase 2, and §6 Phase 4 clauses quoted in this report.

2. **Verify Parameter Limits in `ORIGINAL_REQUEST.md`:**
   ```bash
   grep -E "(victim private IP|60 s|10,000 pps)" .agents/teamwork/ORIGINAL_REQUEST.md
   ```
   *Expected:* Identical boundaries (Target == VICTIM_PRIVATE_IP, Duration <= 60s, Rate <= 10,000 pps).

3. **Verify Environment Coordinates in `lab.env`:**
   ```bash
   source lab.env && echo "VICTIM=$VICTIM_PRIVATE_IP ATTACKER=$ATTACKER_PRIVATE_IP CLIENT=$CLIENT_PRIVATE_IP"
   ```
   *Expected:* `VICTIM=172.31.37.214 ATTACKER=172.31.42.168 CLIENT=172.31.41.87`.

4. **Verify Exit Code Determinism:**
   - Test suites verifying `attack_guard.sh` must assert `exit_code != 0` (or `exit_code == 1`) on refusal.
   - Test suites verifying `set_profile.sh` must assert `exit_code == 0` on `{break|fix|default}`.

5. **Invalidation Conditions:**
   This specification would be invalidated if:
   - Any tool allows `--flood` or intervals `< u100` without human approval recorded in `LAB_LOG.md` (Gate G3).
   - `attack_guard.sh` executes any traffic when `/tmp/LAB_STOP` exists.
   - `attack_guard.sh` targets a public IP or an IP other than `VICTIM_PRIVATE_IP`.
   - `set_profile.sh break` fails to set `net.ipv4.tcp_syncookies=0`.
