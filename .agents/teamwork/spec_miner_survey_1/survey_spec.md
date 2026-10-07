# Comprehensive Specification & Requirements Inventory: Socket-Level Lightweight Detection of TCP Flooding Attacks in Edge Networks

**Document Version:** 1.0  
**Author:** `spec_miner_survey_1` (Specification Mining Agent)  
**Parent Orchestrator:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Target Repository:** `/Users/raja/Documents/syn-edge-flooding`  
**Primary Specification Sources:**
- `ORIGINAL_REQUEST.md` (Formal User Request & Acceptance Criteria)
- `docs/AGENTS_tcp_flood_lab.md` (Normative Technical & Operational Specification v1.0)
- `docs/design.md` (Abstract & Architectural Motivation)
- `updates/000_PROJECT_INITIALIZATION.md` & `updates/001_DISPATCH_AND_SENTINEL.md` (Managerial Directives)

---

## 1. Executive Summary & Research Framework

### 1.1 Core Research Question
*Can a small set of socket-state features, read cheaply from the Linux kernel on an edge-class machine (e.g., AWS EC2 t3.micro), detect TCP flooding attacks accurately and quickly, while remaining quiet during legitimate flash crowds?*

### 1.2 Story Analogy (System Mental Model)
- **The Restaurant Model:** An edge server acts like a modest restaurant with a limited table count (connection capacity).
- **SYN Flood:** A malicious prankster books many tables without showing up (half-open connection state `SYN_RECV` accumulates, consuming kernel backlog queues).
- **Flash Crowd:** A large wedding party arrives suddenly: volume spikes dramatically, but patrons promptly take their seats (handshakes complete rapidly to `ESTABLISHED`).
- **Socket-Level Detector:** An efficient restaurant manager who glances at table counters once per second (`/proc/net/tcp`), never intercepting or reading customer conversations (zero packet inspection).

### 1.3 Hypotheses
- **Hypothesis H1:** Alarming on **abnormal volume AND poor handshake completion** separates SYN floods from flash crowds significantly better than a naive volume-only threshold rule.
- **Hypothesis H2:** A socket-level detector incurs substantially lower CPU utilization and memory footprint (RSS) compared to packet-level deep inspection (e.g., Suricata IDS).
- **Hypothesis H3 (Expected Partial Invalidation):** Connection floods complete TCP handshakes; therefore, handshake completion ratio alone will *not* flag them. A secondary socket signal (established connection growth rate paired with source IP concentration) is required.

### 1.4 Scope Boundaries
- **In-Scope:**
  - SYN flood attacks (variable rates: 100 pps, 1,000 pps, 10,000 pps).
  - TCP connection hold / exhaustion attacks (100, 500, 2,000 concurrent sockets).
  - Legitimate flash crowds (25%, 50%, 100% of calibrated server capacity).
  - Superimposed attacks (SYN flood concurrent with a flash crowd).
  - Kernel SYN-cookie mitigation effects (`net.ipv4.tcp_syncookies = 1`).
  - Kernel socket inspection via `/proc/net/tcp`, `/proc/net/snmp`, `/proc/net/netstat`.
  - Edge resource constraints on AWS `t3.micro` instances.
- **Out-of-Scope:**
  - Spoofed-source IP evasion (AWS VPC infrastructure drops spoofed packets).
  - Traffic egress outside the isolated lab VPC.
  - Deep packet payload inspection (DPI) or L7 filtering.
  - ACK floods, RST floods, UDP floods, ICMP floods (retained as optional future extensions).

---

## 2. Safety Guardrails, Cost Constraints, and Ethical Controls

### 2.1 Non-Negotiable Safety Invariants
1. **Target Confinement:** All attack traffic generated from `attacker` MUST string-strictly target the victim's private IPv4 address (`VICTIM_PRIVATE_IP` loaded from `lab.env`).
2. **Security Group Isolation:** 
   - The security group (`lab-sg`) MUST NOT contain any ingress rule with CIDR `0.0.0.0/0` or `::/0`.
   - SSH (TCP port 22) is restricted exclusively to the operator's current public IP address `/32`.
   - Inter-node communication (TCP, UDP, ICMP) is allowed strictly from the security group to itself (`--source-group lab-sg`).
3. **No External Egress:** Under no circumstances shall test or flood traffic exit the designated VPC. No scanning or probing of third-party hosts.

### 2.2 Attack Guard Enforcement (`attack_guard.sh`)
Every attack execution on the `attacker` node MUST pass through the wrapper script `attack_guard.sh <tool> <args>`. The guard MUST refuse execution with a non-zero exit code if ANY of the following conditions are violated:
- **Target IP Check:** Target IP does not exactly match `VICTIM_PRIVATE_IP`.
- **Duration Cap:** Duration exceeds 60 seconds (`timeout <= 60`).
- **Rate Limit:** SYN packet rate exceeds 10,000 pps (for `hping3`, interval must satisfy `-i u{INTERVAL}` where `INTERVAL >= 100`).
- **Prohibited Flags:** Explicit refusal if `--flood` or `--faster` is passed.
- **Connection Cap:** TCP connection hold count exceeds 2,000 concurrent sockets.
- **Emergency Stop:** The kill switch file `/tmp/LAB_STOP` exists on the host.

### 2.3 Human Approval Gates
- **Gate G1 (Pre-Infrastructure):** Human confirmation of AWS security testing and simulated DoS policy compliance prior to Phase 1.
- **Gate G2 (Pre-Attack):** Human review and approval of the automated attack guard test report (`infra/guard_selftest.txt`) prior to Phase 5.
- **Gate G3 (Cap Escalation):** Explicit human authorization recorded in `LAB_LOG.md` before raising any threshold in Section 2.2.

### 2.4 Stop-and-Escalate Triggers
Immediate execution halt (`touch /tmp/LAB_STOP` on attacker, notify human, document in `LAB_LOG.md`) if:
1. Any command attempts to target a non-lab or external IP address.
2. More than 3 EC2 instances exist tagged with `Project=tcp-flood-lab`.
3. Estimated cumulative AWS spend exceeds **US $15.00**.
4. An AWS Abuse or Policy violation notification is received.
5. The lab security group acquires any public (`0.0.0.0/0`) ingress rule.
6. Lab instances run continuously for more than 12 hours.

### 2.5 Cost Management Controls
- Tag all AWS resources with `Project=tcp-flood-lab`.
- Launch instances with `--credit-specification CpuCredits=standard` to prevent unexpected unlimited burst credit billing.
- Track instance `CPUCreditBalance` in run metadata.
- Stop (do not terminate) instances if pausing work for > 1 hour; terminate completely during Phase 10 teardown.

### 2.6 Data Integrity Controls
- Raw artifacts under `runs/` are immutable and MUST NEVER be deleted or edited.
- Derived metrics belong exclusively in `analysis/`.
- Aborted or failed runs must remain logged in `runs/INDEX.csv` with their corresponding abort reasons.

---

## 3. Testbed Topology & Node Configurations

### 3.1 Node Definitions
All 3 nodes reside in the default VPC within the same Availability Zone:

| Node Name | EC2 Instance Type | OS Image | Role & Software Components |
|---|---|---|---|
| **victim** | `t3.micro` (2 vCPU, 1 GiB RAM) | Ubuntu 24.04 LTS (gp3) | Nginx (target web server), socket sampler (`sampler.py`), detector (`detector.py`), tcpdump (header capture) |
| **attacker** | `t3.micro` (2 vCPU, 1 GiB RAM) | Ubuntu 24.04 LTS (gp3) | `hping3`, `conn_hold.py`, `attack_guard.sh`, iptables RST drop rule |
| **client** | `t3.micro` (2 vCPU, 1 GiB RAM) | Ubuntu 24.04 LTS (gp3) | `wrk` (baseline load), `ab` (flash crowd load), `probe.sh` (1 Hz HTTP prober) |

### 3.2 Network Interface & Security Group
- Interface: Primary network interface `ens5`.
- Security Group `lab-sg`:
  - Ingress TCP 22: Operator Public IP `/32`.
  - Ingress All: Self-referential `sg-xxxxxxxx`.

### 3.3 Victim Web Server & Kernel Tuning Profiles
- **Nginx Configuration:**
  - Serves static `index.html` (~1 KB).
  - Listener configuration: `listen 80 backlog=128;`.
- **Kernel Sysctl Profiles (`set_profile.sh {break|fix}`):**
  - **`break` Profile (Vulnerable Baseline):**
    - `net.ipv4.tcp_syncookies = 0`
    - `net.ipv4.tcp_max_syn_backlog = 128`
    - `net.core.somaxconn = 128`
  - **`fix` Profile (Mitigated Baseline):**
    - `net.ipv4.tcp_syncookies = 1`
    - `net.ipv4.tcp_max_syn_backlog = 128`
    - `net.core.somaxconn = 128`
- **Initial Baseline Snapshot:** Record defaults prior to alteration into `infra/sysctl_defaults.txt`:
  - `tcp_syncookies`, `tcp_max_syn_backlog`, `somaxconn`, `tcp_synack_retries`, `ip_local_port_range`, and client `ulimit -n`.

### 3.4 Attacker RST Suppression (Crucial Realism Mechanism)
Because `hping3` crafts raw SYN packets in user-space without kernel socket awareness, the Linux kernel on the attacker host sends an automatic TCP RST upon receiving the victim's SYN-ACK. This causes the victim to immediately tear down the half-open connection, masking the attack.
- **Mandatory Iptables Rule:**
  ```bash
  sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP
  ```
- Store exact rule in `infra/attacker_rules.txt`; must be removed during teardown.

### 3.5 Time Synchronization
- All nodes must run `chrony`.
- Before each test batch, verify clock offset using `chronyc tracking`.
- Abort batch if clock offset between any pair exceeds **50 ms**.

---

## 4. Instrumentation & Data Schemas

### 4.1 Environment Configuration (`lab.env`)
Exported by infrastructure setup and sourced by all operational scripts:
```bash
AWS_REGION=<region>
VPC_ID=<vpc-id>
SG_ID=<sg-id>
KEY_NAME=tcp-flood-lab
KEY_PATH=~/.ssh/tcp-flood-lab.pem
VICTIM_ID=<i-...>
ATTACKER_ID=<i-...>
CLIENT_ID=<i-...>
VICTIM_PUB=<ip>
ATTACKER_PUB=<ip>
CLIENT_PUB=<ip>
VICTIM_PRIVATE_IP=<ip>
ATTACKER_PRIVATE_IP=<ip>
CLIENT_PRIVATE_IP=<ip>
VICTIM_IFACE=ens5
```

### 4.2 Run Identifier Naming Convention
Format: `<scenario>-r<rep:02d>-<UTC yyyymmddThhmmssZ>`  
Example: `S2M-r03-20261008T101500Z`

### 4.3 Mandatory Run Artifacts (`runs/<run_id>/`)
Every scenario run directory MUST contain exactly the following 10 artifacts:

1. `events.json`: Ground truth start/end timestamps and operational metadata.
2. `victim_metrics.csv`: 1 Hz kernel and socket metrics emitted by `sampler.py`.
3. `probe.csv`: 1 Hz HTTP probe latencies and success flags from `client`.
4. `load_client.txt`: Raw console output from `wrk` / `ab`.
5. `attack_attacker.txt`: Raw console output from `hping3` / `conn_hold.py`.
6. `sysctl_snapshot.txt`: Kernel parameters active at run initialization.
7. `nginx_access.log`: Web server access logs recorded during the test window.
8. `victim_cpu_pidstat.txt`: `pidstat -u -r -p ALL 1` recording per-process CPU & RAM.
9. `capture.pcap`: Packet headers (`-s 96`) on port 80 (collected on **rep 1 only** of each scenario).
10. `notes.md`: Runner log of system anomalies, environmental factors, or abort details.

### 4.4 Master Run Index (`runs/INDEX.csv`)
Header: `run_id,scenario,rep,aborted,notes`

### 4.5 Data Schemas

#### 4.5.1 `events.json` Schema
```json
{
  "run_id": "S2M-r03-20261008T101500Z",
  "scenario": "S2M",
  "rep": 3,
  "params": {
    "tool": "hping3",
    "interval_us": 1000,
    "duration_s": 30
  },
  "syncookies": 0,
  "t_start_epoch_ms": 1791454500000,
  "t_end_epoch_ms": 1791454530000,
  "sampler_start_epoch_ms": 1791454440000,
  "sampler_stop_epoch_ms": 1791454590000,
  "aborted": false,
  "abort_reason": null,
  "clock_offset_ms": {
    "victim": 0.42,
    "attacker": -0.15,
    "client": 0.28
  },
  "git_sha": "a1b2c3d4e5f6..."
}
```

#### 4.5.2 `victim_metrics.csv` Schema (1 Hz, Monotonic Pacing)
Standard library only (`python3`), median sample execution cost < 5 ms.

| Field Name | Description & Data Source | Notes |
|---|---|---|
| `ts_ms` | Timestamp in UTC epoch milliseconds | Integer |
| `syn_recv` | Count of sockets in `SYN_RECV` on port 80 (`03` in `/proc/net/tcp`) | Half-open count |
| `established` | Count of sockets in `ESTABLISHED` on port 80 (`01` in `/proc/net/tcp`) | Active sessions |
| `time_wait` | Count of sockets in `TIME_WAIT` on port 80 (`06` in `/proc/net/tcp`) | Closed waiting |
| `close_wait` | Count of sockets in `CLOSE_WAIT` on port 80 (`08` in `/proc/net/tcp`) | Remote closed |
| `fin_wait` | Count of sockets in `FIN_WAIT1` or `FIN_WAIT2` (`04`, `05`) | Teardown state |
| `last_ack` | Count of sockets in `LAST_ACK` (`09`) | Closing state |
| `listen_q` | Current listen queue backlog depth | `/proc/net/tcp` |
| `top_src_share` | Ratio (0.0 to 1.0) of port 80 sockets held by dominant remote IP | Single-source concentration |
| `n_distinct_src` | Number of distinct client IPs connected to port 80 | Source dispersion |
| `d_passive_opens` | 1-second delta of `Tcp: PassiveOpens` from `/proc/net/snmp` | Successful handshakes |
| `d_attempt_fails` | 1-second delta of `Tcp: AttemptFails` from `/proc/net/snmp` | Failed handshakes / aborted |
| `d_estab_resets` | 1-second delta of `Tcp: EstabResets` from `/proc/net/snmp` | Established resets |
| `d_retrans` | 1-second delta of `Tcp: RetransSegs` from `/proc/net/snmp` | Packet retransmissions |
| `d_listen_overflows` | 1-second delta of `TcpExt: ListenOverflows` from `/proc/net/netstat` | Accept queue overflow |
| `d_listen_drops` | 1-second delta of `TcpExt: ListenDrops` from `/proc/net/netstat` | SYN/Accept drops |
| `d_syncookies_sent` | 1-second delta of `TcpExt: SyncookiesSent` from `/proc/net/netstat` | Outbound SYN cookies |
| `d_syncookies_recv` | 1-second delta of `TcpExt: SyncookiesRecv` from `/proc/net/netstat` | Valid inbound cookies |
| `d_syncookies_failed` | 1-second delta of `TcpExt: SyncookiesFailed` from `/proc/net/netstat` | Invalid cookies |
| `d_reqq_full_cookies` | 1-second delta of `TcpExt: TCPReqQFullDoCookies` | Cookie fallback trigger |
| `d_reqq_full_drop` | 1-second delta of `TcpExt: TCPReqQFullDrop` | SYN queue drops |
| `cpu_pct` | Host CPU utilization percentage derived from `/proc/stat` | 0.0 to 100.0% |
| `mem_used_mb` | Total host RAM utilized derived from `/proc/meminfo` | Megabytes |
| `sample_cost_ms` | Wall-clock execution time for sampler iteration | Required median < 5 ms |

*Rule:* Missing kernel counters must be recorded as empty strings (`,,`), never `0`.

#### 4.5.3 `probe.csv` Schema (1 Hz Client HTTP Probe)
Probes executed by `probe.sh` from `client` to `http://$VICTIM_PRIVATE_IP/` with `--max-time 3`.
- `ts_ms`: Epoch millisecond timestamp of probe launch.
- `http_code`: HTTP response status code (e.g., `200`, `000` for timeout/drop).
- `t_connect_s`: TCP connection establishment time in seconds.
- `t_total_s`: Total HTTP request/response turnaround time in seconds.
- `ok`: Binary success indicator (`1` if `http_code == 200` AND `t_total_s <= 3.0`, else `0`).

---

## 5. Workload Generation & Capacity Calibration

### 5.1 Victim Capacity Calibration Protocol
Before executing scenarios, determine the physical throughput limit of the unmitigated victim (`CAPACITY_RPS`):
1. Execute `wrk` from `client` at stepped concurrency levels: 10, 25, 50, 100, 200, 400 for 20 seconds each.
2. Measure requests per second (`req/s`), p95 latency, and probe success rate.
3. **Definition:** `CAPACITY_RPS` is the highest measured request rate maintaining:
   - Probe success rate $\ge 99\%$
   - p95 response latency $< 200\text{ ms}$
4. Store calibrated levels in `infra/crowd_levels.json`:
   - Small Crowd ($25\%$ of `CAPACITY_RPS`)
   - Medium Crowd ($50\%$ of `CAPACITY_RPS`)
   - Large Crowd ($100\%$ of `CAPACITY_RPS`)
   - Map each level to `-c` (concurrency) and `-n` (total requests) parameters for `ab`.

### 5.2 Workload Generator Configurations

| Workload Type | Tool & Invocation | Target Parameters & Behavior |
|---|---|---|
| **Quiet Background** | `wrk -t1 -c2 -d{D}s -H "Connection: close" http://$VICTIM_PRIVATE_IP/` | Low, steady background load active during all scenarios except S0. |
| **Flash Crowd** | `ab -n {N} -c {C} http://$VICTIM_PRIVATE_IP/` | No keepalive (`-k` omitted) to force discrete TCP handshakes per request. Ramp variant: stepped concurrency 10 $\rightarrow$ C over 10 s. |
| **SYN Flood** | `attack_guard.sh hping3 -S -p 80 -i u{INTERVAL} $VICTIM_PRIVATE_IP` wrapped in `timeout {D}` | **L:** `u10000` ($\approx 100\text{ pps}$)<br>**M:** `u1000` ($\approx 1,000\text{ pps}$)<br>**H:** `u100` ($\approx 10,000\text{ pps}$)<br>*No `--rand-source`*. |
| **Connection Flood** | `attack_guard.sh python3 conn_hold.py --host $VICTIM_PRIVATE_IP --port 80 --n {N} --hold {D} --ramp 5` | **L:** $N=100$<br>**M:** $N=500$<br>**H:** $N=2,000$<br>Asyncio client, opens $N$ connections, transmits partial HTTP header (`GET / H`), holds $D$ seconds, closes cleanly. |

---

## 6. Experimental Scenario Matrix (S0 to S5)

### 6.1 Matrix Specification
Total runs: **65 runs** (13 scenario configurations $\times$ 5 repetitions).  
Execution duration: $\approx 4\text{ min/run} \approx 4.5\text{ hours}$ continuous serial execution.

| Scenario ID | Name / Description | Workload Parameters | Cookies (`syncookies`) | Reps | Timeline Windows |
|---|---|---|---|---|---|
| **S0** | Quiet Baseline | Quiet load (`wrk`) | Off (`0`, `break`) | 5 | 120 s continuous |
| **S1S** | Flash Crowd (Small) | `ab` Small Crowd (25% cap), 30 s event | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S1M** | Flash Crowd (Medium) | `ab` Medium Crowd (50% cap), 30 s event | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S1L** | Flash Crowd (Large) | `ab` Large Crowd (100% cap), 30 s event | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S2L** | SYN Flood (Low) | `hping3` L (`u10000`, 100 pps), 30 s event | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S2M** | SYN Flood (Medium) | `hping3` M (`u1000`, 1,000 pps), 30 s event | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S2H** | SYN Flood (High) | `hping3` H (`u100`, 10,000 pps), 30 s event | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S3L** | Connection Flood (Low) | `conn_hold.py` L ($N=100$), hold 30 s | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S3M** | Connection Flood (Medium) | `conn_hold.py` M ($N=500$), hold 30 s | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S3H** | Connection Flood (High) | `conn_hold.py` H ($N=2,000$), hold 30 s | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S4** | SYN Flood during Crowd | `hping3` M + `ab` M concurrent, 30 s event | Off (`0`, `break`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S5M** | SYN Flood M with Mitigation | `hping3` M (1,000 pps), 30 s event | **On** (`1`, `fix`) | 5 | 60 s pre, 30 s event, 60 s post |
| **S5H** | SYN Flood H with Mitigation | `hping3` H (10,000 pps), 30 s event | **On** (`1`, `fix`) | 5 | 60 s pre, 30 s event, 60 s post |

### 6.2 Per-Run Operational Protocol (`run_scenario.sh`)
1. **Pre-Flight Settling:**
   - Confirm active sysctl profile matches target scenario (`break` vs `fix`).
   - Confirm chrony clock offset $< 50\text{ ms}$.
   - Ensure `/tmp/LAB_STOP` is absent.
   - Wait until victim `syn_recv == 0` and `established` is stable for $\ge 10\text{ s}$. Timeout after 120 s (log and abort if unsettled).
2. **Directory & Initial State:** Initialize `runs/<run_id>/`; write `sysctl_snapshot.txt`.
3. **Data Collector Startup:** Launch `sampler.py`, `probe.sh`, and `pidstat`. On **Rep 1 only**, launch `tcpdump` header capture (`-s 96 -w capture.pcap 'tcp port 80'`).
4. **Pre-Event Phase:** Wait 60 seconds (collect steady baseline metrics).
5. **Event Execution:**
   - Record `t_start_epoch_ms`.
   - Launch background load + scenario workload.
   - Await workload completion (30 s duration); record `t_end_epoch_ms`.
6. **Post-Event Phase:** Wait 60 seconds (capture recovery dynamics).
7. **Artifact Fetching:** Stop collectors, retrieve logs, generate `events.json` and `notes.md`.
8. **Inter-Run Cooldown:** Mandatory wait until `syn_recv == 0` for 10 consecutive seconds (cap at 120 s) to allow expired half-open sockets to clear kernel tables.
9. **Execution Order:** Randomized block order across scenarios (one rep per scenario per block, seeded and logged).

### 6.3 Expected Live Behaviors & Diagnostics

| Scenario | Expected Observable Dynamics | Live Diagnostic Action if Deviating |
|---|---|---|
| **S0** | `syn_recv` $\approx 0\text{--}2$; completion ratio $\approx 1.0$; probes 100% `ok`. | Verify nginx running; check client background traffic. |
| **S1\*** | `established` and `time_wait` surge; `syn_recv` remains small; completion ratio stays high ($\ge 0.85$); probes mostly `ok`. | Check that `ab` does not have `-k` enabled; verify client file descriptor limits (`ulimit -n`). |
| **S2\* (Cookies Off)** | `syn_recv` saturates toward backlog limit ($128$); `d_listen_drops` surges; probes fail heavily at M/H; gradual decay after event. | If `syn_recv` remains $\approx 0$: **RST suppression rule missing** on attacker, or attack guard blocked execution. |
| **S3\*** | `established` surges to $\approx N$; completion ratio **remains high**; `top_src_share` $\approx 1.0$; probes degrade at H. | If `established` plateaus below $N$, inspect client ephemeral ports or server file limits. |
| **S4** | Superimposed signals: completion ratio dips but remains higher than S2 due to concurrent completed crowd handshakes. | Confirm both `ab` and `hping3` launched concurrently. |
| **S5\* (Cookies On)** | `syn_recv` remains $\approx 0$ (half-open entries bypassed); `d_syncookies_sent` surges; probes remain predominantly `ok`. | **Fundamental Finding:** Half-open signal vanishes; detector must trigger on cookie/queue rate branches. |

---

## 7. Detection Algorithms & Mathematical Formulations

### 7.1 Socket-Level Derived Features (Window $W = 3\text{ s}$)

1. **Half-Open Count:**
   $$x_t = \text{half\_open}_t = \text{syn\_recv}_t$$
2. **Handshake Completion Ratio ($C_t$):**
   $$C_t = \frac{\sum_{i=0}^{W-1} \Delta \text{PassiveOpens}_{t-i}}{\max\left(1, \sum_{i=0}^{W-1} \Delta \text{PassiveOpens}_{t-i} + \sum_{i=0}^{W-1} \Delta \text{AttemptFails}_{t-i}\right)}$$
   *Note:* $\Delta \text{PassiveOpens}$ tracks handshakes successfully completed; $\Delta \text{AttemptFails}$ tracks half-open connections that timed out or failed.
3. **Established Connection Growth Rate ($G_t$):**
   $$G_t = \text{established}_t - \text{EWMA}_\beta(\text{established}_t)$$
4. **Queue Pressure Metric ($Q_t$):**
   $$Q_t = \Delta \text{ListenDrops}_t + \Delta \text{ListenOverflows}_t + \Delta \text{TCPReqQFullDrop}_t$$
5. **Cookie Generation Rate ($K_t$):**
   $$K_t = \Delta \text{SyncookiesSent}_t$$
6. **Top Source IP Share ($S_t$):**
   $$S_t = \text{top\_src\_share}_t = \frac{\max_{\text{IP}} \text{Sockets}_{\text{IP}, t}}{\sum_{\text{IP}} \text{Sockets}_{\text{IP}, t}} \quad (\text{for non-listen port 80 sockets})$$

---

### 7.2 Detector Formulations

#### 7.2.1 Detector B1: Naive Baseline Volume Detector
- **Logic:** Raises alarm if half-open volume OR passive open rate exceeds static thresholds for $N$ consecutive seconds:
  $$\text{Alarm}_{B1}(t) = \mathbb{I}\left( \bigwedge_{j=0}^{N-1} \left( x_{t-j} > \text{FIXED\_T} \;\lor\; \Delta \text{PassiveOpens}_{t-j} > \text{FIXED\_R} \right) \right)$$
- **Threshold Derivation:** Static thresholds $\text{FIXED\_T}$ and $\text{FIXED\_R}$ are calibrated directly from maximum observed values in benign S0 baseline runs (e.g., $99.9\text{th percentile} \times 2$).

#### 7.2.2 Detector D1: Proposed Adaptive Dual-Signal Detector
- **Adaptive Baseline (EWMA):**
  $$\mu_t = \begin{cases} \alpha x_t + (1 - \alpha)\mu_{t-1}, & \text{if } \text{Alarm}_{D1}(t-1) = 0 \\ \mu_{t-1}, & \text{if } \text{Alarm}_{D1}(t-1) = 1 \quad \text{\textbf{(Baseline Frozen)}} \end{cases}$$
- **Dual Trigger Condition:**
  An alarm is triggered when both the volume condition and the completion condition hold for $N$ consecutive seconds:
  $$\text{Trigger}(t) = \left( x_t > \max(\text{FLOOR}, K \cdot \mu_t) \right) \;\land\; \left( C_t < \tau \right)$$
  $$\text{Alarm}_{D1}(t) = 1 \iff \bigwedge_{j=0}^{N-1} \text{Trigger}(t-j) = 1$$
- **Hysteresis Clearing:** Once active, the alarm remains latched until the trigger condition evaluates to false for $M$ consecutive calm seconds ($M = 5$).
- **Architectural Guardrail:** Freezing $\mu_t$ during alarms prevents an ongoing flood from polluting the adaptive baseline and normalizing the attack state.

#### 7.2.3 Detector D2: Extended Multi-Branch Detector
Extends D1 to detect connection floods (Hypothesis H3) and mitigate SYN-cookie blindness:
$$\text{Alarm}_{D2}(t) = \text{Alarm}_{D1}(t) \;\lor\; \text{Branch}_{\text{conn}}(t) \;\lor\; \text{Branch}_{\text{cookie}}(t)$$
- **Connection Flood Branch:**
  $$\text{Branch}_{\text{conn}}(t) = \left( G_t > \theta_{\text{estab}} \right) \;\land\; \left( S_t > S_{\text{thresh}} \right)$$
- **Mitigation / Queue Pressure Branch:**
  $$\text{Branch}_{\text{cookie}}(t) = \left( K_t > \theta_{\text{cookie}} \right) \;\lor\; \left( Q_t > \theta_{\text{queue}} \right)$$
- **Evaluation Requirement:** Perform an ablation study reporting the independent performance and false alarm contributions of each branch.

#### 7.2.4 Detector D3: Supervised Machine Learning Benchmark (Optional Extension)
- Model: Scikit-learn Decision Tree or Isolation Forest trained on the 6 derived socket features.
- Training split: Reps 1–3 only; Evaluation split: Reps 4–5 only.
- Deliverables: Binary model size, serialization footprint, and median inference time ($\mu\text{s}$).

---

## 8. Parameter Selection Protocol (Train / Test Split)

### 8.1 Grid Search Space
Evaluated exclusively across **Repetitions 1–3**:

| Hyperparameter | Description | Search Grid Candidates |
|---|---|---|
| $\alpha$ | EWMA baseline smoothing factor | $\{0.05, 0.1, 0.2\}$ |
| $K$ | Adaptive volume multiplier | $\{3, 5, 8\}$ |
| $\tau$ (`TAU`) | Handshake completion ratio threshold | $\{0.3, 0.5, 0.7\}$ |
| $N$ | Consecutive seconds required to trigger | $\{2, 3, 5\}$ |
| $\text{FLOOR}$ | Absolute minimum half-open floor count | $\{20, 50\}$ |
| $M$ | Consecutive calm seconds to clear alarm | $5$ (fixed) |

### 8.2 Strict Train/Test Separation Rules
1. **Training & Tuning Partition:** Repetitions 1, 2, and 3 across all scenarios. Used exclusively for threshold selection, hyperparameter tuning, and ROC curve generation.
2. **Held-Out Evaluation Partition:** Repetitions 4 and 5. Kept completely isolated until final parameters are locked. All final reported metrics (F1–F8, T1–T5, Abstract) MUST derive solely from Repetitions 4–5.
3. **Selection Criterion:** Choose the parameter tuple $(\alpha^*, K^*, \tau^*, N^*, \text{FLOOR}^*)$ that maximizes true attack detection rate subject to strictly **0 false alarms** across benign S0 and S1 tuning runs.
4. **Configuration Deliverable:** Output selected parameters to `detector/params.yaml`.

---

## 9. Evaluation Metrics & Statistical Standards

### 9.1 Detection Metrics (Attack Runs: S2\*, S3\*, S4, S5\*)
- **Binary Detection Flag (`detected`):** Evaluates to $1$ if at least one alarm is asserted in the window $[t_{\text{start}}, t_{\text{end}} + 10\text{ s}]$, else $0$.
- **Detection Delay ($\Delta t_{\text{detect}}$):** Time in seconds between ground truth attack start and initial alarm:
  $$\Delta t_{\text{detect}} = t_{\text{first\_alarm}} - t_{\text{start}}$$

### 9.2 Benign Classification Metrics (Benign Runs: S0, S1\*)
- **False Alarm Flag (`false_alarm`):** Evaluates to $1$ if any alarm is asserted anywhere within the entire test run window.
- **Alarm Duration (`alarm_seconds`):** Cumulative count of seconds the detector spent in an alarm state during a benign run.

### 9.3 Service Quality & Impact Metrics (Derived from `probe.csv`)
- **Probe Success Rate:** Percentage of HTTP probes returning code 200 within 3.0 seconds during the active event window $[t_{\text{start}}, t_{\text{end}}]$.
- **Latency Distribution:** Median and 95th percentile ($p95$) connection and total response times during the event.

### 9.4 Statistical Reporting Rules
- Never report raw means alone.
- Report all metrics as $\text{mean} \pm \text{standard deviation}$ across evaluation runs ($n=2$ per scenario in held-out set; $n=5$ across all reps where appropriate).
- Visualizations must depict individual run data points alongside aggregate bars or violins.

---

## 10. Computational Overhead Benchmark Protocol (Phase 8)

### 10.1 Benchmark Configurations
Measure resource consumption on the `victim` node (2 vCPU, 1 GiB RAM) across 5 repetitions of a 120-second S0 load followed by a 60-second S2M flood:

| Config ID | Description | Sampling Frequency | Detector State |
|---|---|---|---|
| **O0** | Unmonitored Baseline | N/A | None running |
| **O1** | Standard Proc Sampler | 1 Hz (`/proc` method) | D1 online |
| **O2** | SS Shell Sampler | 1 Hz (`ss -tan` CLI method) | D1 online |
| **O3** | High-Frequency Proc Sampler | 10 Hz (`/proc` method) | D1 online |
| **O4** | Packet Inspection IDS (Optional) | Suricata default configuration on `ens5` | Rule-based engine |

### 10.2 Measurement Methodology
- Instrument processes using `pidstat -u -r -p <pid> 1`.
- Record:
  - Mean and $p95$ CPU utilization percentage.
  - Resident Set Size (RSS) in megabytes.
  - Sampler wall-clock loop duration (`sample_cost_ms`).
- Deliverable: Tabulated results saved to `analysis/overhead.csv`.

---

## 11. Required Deliverables & Inventory

### 11.1 Publication Figures (PNG, 300 DPI, Labeled Units)
- **F1: Attack Timeline Dynamics (S0 vs S2M):** Stacked timeline depicting `syn_recv`, `established`, and probe success rate with shaded 30s attack window.
- **F2: Flash Crowd Dynamics (S1M):** Equivalent stacked timeline for flash crowd, positioned adjacent to F1 to illustrate the "wedding vs prank" contrast.
- **F3: Handshake Completion Ratio Distributions:** Box/violin plots comparing $C_t$ across S0, S1, S2, S3, S4, and S5.
- **F4: Detection Delay Comparison:** Bar/scatter plot showing median and spread of detection delay across attack scenarios for B1, D1, D2.
- **F5: Parameter ROC / Trade-Off Curve:** False alarm rate vs detection rate across tuning grid, with optimal operating point highlighted.
- **F6: SYN-Cookie Mitigation Impact:** Comparative plot of probe success and latency under S2M/H (cookies off) vs S5M/H (cookies on).
- **F7: System Overhead Comparison:** Comparative bar charts of CPU % and RSS (MB) across configurations O0 through O4.
- **F8: Connection Flood Diagnostics (S3):** Detailed diagnostic plot showing failure of completion ratio $C_t$ and successful trigger of D2's $G_t$ and $S_t$ signals.

### 11.2 Empirical Tables
- **T1: Scenario Execution Matrix:** Comprehensive summary of all 13 scenarios, traffic parameters, tool commands, and repetitions.
- **T2: Detection Performance Benchmark:** Evaluation metrics (detection rate, delay, false alarms) on held-out runs 4–5 for B1, D1, D2.
- **T3: Computational Overhead Summary:** Mean and p95 CPU %, RSS (MB), and sampling execution latency across O0–O4.
- **T4: D2 Feature Ablation Study:** Isolated contribution of D1 base, connection flood branch, and cookie rate branch.
- **T5: Methodological Limitations & Threats to Validity:** Explicit, honest accounting of lab constraints.

### 11.3 Academic Paper Report (`report/report.md`)
Structure:
1. **Abstract:** Filled strictly from empirical results using the mandatory template:
   > *TCP flooding attacks exhaust a server's connection resources and deny service to legitimate users. Edge devices cannot afford heavy packet inspection, and simple volume rules misclassify legitimate flash crowds. We propose a socket-level detector that reads the kernel's connection-state tables and alarms only when abnormal volume coincides with poor handshake completion, using an adaptive baseline. On an AWS testbed with normal traffic, flash crowds, SYN floods, connection floods, and floods hidden in crowds, it achieves [X]% detection with [Y]% false alarms on held-out runs and a median delay of [Z] s, using [N]% less CPU than a packet-level IDS. We also show that [finding on connection floods and SYN cookies].*
2. **Introduction & Motivation:** Problem statement, edge constraints, hypothesis definitions.
3. **Detection Methodology:** Formal mathematical formulation of features, EWMA baseline, dual trigger, multi-branch logic.
4. **Experimental Testbed:** Architecture, AWS environment, bounded workload generation, capacity calibration.
5. **Empirical Results:** Systematic analysis integrating F1–F8 and T1–T5.
6. **Threats to Validity (Mandatory):**
   - Single-source attacker IP (AWS VPC drops spoofed traffic).
   - Single-source legitimate crowd generator.
   - Micro-instance CPU credit throttling (`t3.micro` credits).
   - Synthetic workloads (`ab` / `wrk`) vs real-world user distributions.
   - Single Linux kernel version (Ubuntu 24.04).
   - Limited run durations (30 s events).
   - Parameter tuning performed within the same physical environment.
7. **Conclusion & Reproduction Guide:** CLI instructions to reproduce all figures from raw data.

### 11.4 Teardown Verification (`infra/teardown_verification.txt`)
- AWS CLI proof confirming:
  - All 3 EC2 instances in `terminated` state.
  - Security group `lab-sg` deleted.
  - EC2 key pair `tcp-flood-lab` deleted and local `.pem` removed.
  - Raw run data archived with cryptographic checksums.

### 11.5 Managerial Communication Log (`updates/`)
- Structured status updates posted to `updates/` tracking phase transitions, risk mitigations, blockers, and milestone resolutions.

---

## 12. Complete Features Discovered & Specification Inventory

### 12.1 Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|---|---|---|---|---|---|---|
| 1 | Safety | Target IP Verification | Strict enforcement that attack target matches `VICTIM_PRIVATE_IP` | CLI arguments | Boolean pass/fail | Exit non-zero, command refused | `AGENTS.md` §4.2 |
| 2 | Safety | Duration Clamping | Enforce maximum duration $\le 60\text{ s}$ via `timeout` | Duration parameter | Wrapped execution | Exit non-zero if $>60\text{ s}$ | `AGENTS.md` §4.2 |
| 3 | Safety | Rate Limiting (SYN) | Limit `hping3` interval to $\ge \text{u}100$ ($\le 10,000\text{ pps}$) | CLI interval flag | Rate enforcement | Refuse `--flood`, `--faster`, or $u < 100$ | `AGENTS.md` §4.2 |
| 4 | Safety | Connection Hold Limit | Enforce max connection count $\le 2,000$ | `--n` parameter | Process invocation | Refuse execution if $N > 2000$ | `AGENTS.md` §4.2 |
| 5 | Safety | Emergency Kill Switch | Host-wide kill switch via presence of `/tmp/LAB_STOP` | File existence | Execution block | Immediate abort if file present | `AGENTS.md` §4.2, 4.4 |
| 6 | Safety | Security Group Lockdown | Prohibit `0.0.0.0/0` ingress; restrict SSH to `/32` | Operator public IP | AWS SG rules | SG creation fails/refused | `AGENTS.md` §4.1 |
| 7 | Infra | Multi-Node Testbed Provisioning | AWS EC2 3-node topology (`victim`, `attacker`, `client`) | AWS CLI commands, AMI, Subnet | Running instances, `lab.env` | Retry on transient AWS failure | `AGENTS.md` §6 Phase 1 |
| 8 | Infra | Dynamic IP SG Update | Dynamic update of operator SSH rule upon IP shift | Operator public IP | Modified SG ingress rule | Logged to `LAB_LOG.md` | `AGENTS.md` §6 Phase 1 |
| 9 | Infra | Standard CPU Credit Enforcement | Launch with `--credit-specification CpuCredits=standard` | EC2 run-instances flag | Standard credit profile | Prevents unlimited burst cost | `AGENTS.md` §4.5 |
| 10 | Tooling | RST Suppression Rule | Drop outbound kernel TCP RST on attacker for raw SYNs | Iptables command | Filtered TCP flags | Masked attack if missing | `AGENTS.md` §6 Phase 2 |
| 11 | Tooling | Sysctl Break/Fix Profiles | Toggle vulnerable vs mitigated kernel state | `set_profile.sh {break\|fix}` | Kernel parameters applied | Snapshot verification | `AGENTS.md` §6 Phase 2 |
| 12 | Tooling | Sysctl Defaults Snapshot | Snapshot original system kernel defaults | `sysctl` command | `infra/sysctl_defaults.txt` | Read failure | `AGENTS.md` §6 Phase 2 |
| 13 | Tooling | Chrony Synchronization Check | Check clock offset across testbed nodes | `chronyc tracking` | Offset in milliseconds | Abort batch if offset $>50\text{ ms}$ | `AGENTS.md` §5.4 |
| 14 | Instrumentation | Socket-State Sampler (Proc) | 1 Hz monotonic reading of `/proc/net/tcp`, `/proc/stat`, etc. | Polling loop, 1 Hz schedule | `victim_metrics.csv` (24 cols) | Empty field on missing counter | `AGENTS.md` §5.5, Phase 3 |
| 15 | Instrumentation | Socket-State Sampler (SS) | Secondary 1 Hz sampler shelling out to `ss -tan` | Polling loop, 1 Hz schedule | Overhead comparison stream | Process failure | `AGENTS.md` §6 Phase 3, 8 |
| 16 | Instrumentation | HTTP Probe Generator | 1 Hz curl probing from client with 3 s max time | HTTP GET target | `probe.csv` (5 columns) | Records `ok=0` on timeout/drop | `AGENTS.md` §5.6, Phase 3 |
| 17 | Instrumentation | Automated Run Collector | Orchestrated startup/fetch of pidstat, sampler, probe | Run ID, configuration | Staged run folder artifacts | SCP/network retry | `AGENTS.md` §6 Phase 3 |
| 18 | Traffic | Victim Capacity Calibration | Determine `CAPACITY_RPS` via stepped `wrk` concurrency | Concurrency steps (10–400) | `infra/crowd_levels.json` | Log failure if criteria unmet | `AGENTS.md` §6 Phase 4 |
| 19 | Traffic | Bounded Quiet Background Load | Low steady background HTTP load via `wrk` | Duration, threads, conns | Background TCP traffic | Logged client error | `AGENTS.md` §6 Phase 4 |
| 20 | Traffic | Bounded Flash Crowd Generator | Concurrency-driven legitimate arrivals via `ab` | Concurrency, count | Transient connection burst | Ephemeral port exhaustion | `AGENTS.md` §6 Phase 4 |
| 21 | Traffic | Bounded SYN Flood Generator | Controlled raw SYN flood via `hping3` and guard | Interval (`u10000`, `u1000`, `u100`) | SYN packet flood | Guard blocks invalid args | `AGENTS.md` §6 Phase 4 |
| 22 | Traffic | Async Connection Hold Generator | Asyncio connection exhaustion via partial HTTP lines | Host, port, $N$, hold duration | Long-lived established sockets | Client `EMFILE` (fd limit) | `AGENTS.md` §6 Phase 4 |
| 23 | Execution | Serial Scenario Matrix Runner | Automated, strictly serial execution of S0–S5 runs | Scenario matrix specification | 65 populated run directories | Cooldown abort if unsettled | `AGENTS.md` §6 Phase 5 |
| 24 | Execution | Cooldown & Recovery Enforcer | Verification that `syn_recv == 0` for 10 s before run | Metric check loop | Clean initial socket state | Abort run after 120 s timeout | `AGENTS.md` §6 Phase 5 |
| 25 | Execution | Randomized Block Order | Seeded scenario execution shuffling per block | Random seed, scenario list | Randomized run sequence | Logged seed in metadata | `AGENTS.md` §6 Phase 5 |
| 26 | Execution | Header-Only PCAP Capture | Packet capture on port 80 during rep 1 of each scenario | `tcpdump -s 96` | `capture.pcap` | Timeout after 180 s | `AGENTS.md` §6 Phase 5 |
| 27 | Detection | Offline Replay Engine | Row-by-row simulation of detector against CSV traces | `victim_metrics.csv` | Alarm timestamp array | Parsing error | `AGENTS.md` §6 Phase 6 |
| 28 | Detection | Online Edge Detector | Live socket monitoring and real-time alarming | Socket table poll | Real-time alarm stream | Execution error | `AGENTS.md` §6 Phase 6 |
| 29 | Detection | Baseline Volume Detector (B1) | Static volume thresholding on half-open and passive opens | Fixed thresholds $T, R$ | Alarm indicator | Misclassifies crowds | `AGENTS.md` §6 Phase 6 |
| 30 | Detection | Adaptive Dual-Signal Detector (D1) | EWMA baseline volume + handshake completion ratio | $\alpha, K, \tau, N, \text{FLOOR}, M$ | Alarm indicator | Suppresses during mitigation | `AGENTS.md` §6 Phase 6 |
| 31 | Detection | Baseline Freeze Mechanism | Freezes EWMA update while alarm is active | Alarm status | Frozen $\mu_t$ | Baseline drift if disabled | `AGENTS.md` §6 Phase 6 |
| 32 | Detection | Hysteresis Alarm Clearing | Clears active alarm only after $M$ consecutive calm seconds | Calm second counter | De-asserted alarm | Oscillation if omitted | `AGENTS.md` §6 Phase 6 |
| 33 | Detection | Connection Flood Branch (D2) | Alarms on established growth + top source concentration | Growth $G_t$, source share $S_t$ | Alarm indicator | Undetected if multi-source | `AGENTS.md` §6 Phase 6 |
| 34 | Detection | SYN Cookie Branch (D2) | Alarms on cookie generation and queue drop rates | Cookie rate $K_t$, queue $Q_t$ | Alarm indicator | Silent if counters missing | `AGENTS.md` §6 Phase 6 |
| 35 | Detection | Machine Learning Benchmark (D3) | Decision tree / isolation forest socket classifier | Derived socket features | Predicted class / anomaly | Model size / inference cost | `AGENTS.md` §6 Phase 6 |
| 36 | Protocol | Parameter Tuning & Train/Test Split | Hyperparameter optimization on reps 1–3, testing on 4–5 | Parameter grid, Reps 1–3 data | `params.yaml`, test metrics | Overfitting if split violated | `AGENTS.md` §6 Phase 6 |
| 37 | Analysis | Detection Latency & Delay Metric | Measure time delta from attack start to first alarm | Ground truth, alarm logs | Delay in seconds | Undetected if no alarm | `AGENTS.md` §6 Phase 6 |
| 38 | Analysis | False Alarm Quantification | Measure alarm frequency and duration on benign runs | Benign traces, alarm logs | False alarm rate, alarm-sec | False positive inflation | `AGENTS.md` §6 Phase 6 |
| 39 | Benchmark | Computational Overhead Profiler | Measure CPU %, RSS, and sampling latency across O0–O4 | `pidstat`, sampler logs | `analysis/overhead.csv` | Process termination | `AGENTS.md` §6 Phase 8 |
| 40 | Reporting | Publication Visualizations F1–F8 | 300 DPI publication plots of empirical data | Raw & derived metrics | PNG figure files | Script rendering error | `AGENTS.md` §6 Phase 9 |
| 41 | Reporting | Publication Tables T1–T5 | Formatted markdown/LaTeX summary tables | Aggregated metrics | Markdown tables | Missing data cells | `AGENTS.md` §6 Phase 9 |
| 42 | Reporting | Academic Paper Report | Complete research manuscript with filled abstract | Analysis metrics, tables, plots | `report/report.md` | Incomplete template brackets | `AGENTS.md` §6 Phase 10 |
| 43 | Teardown | Resource Teardown & Verification | Destroy AWS instances, SG, keys, and verify zero spend | AWS CLI teardown commands | `infra/teardown_verification.txt`| Dangling resource alert | `AGENTS.md` §6 Phase 10 |
| 44 | Teardown | Run Artifact Archive | Cryptographic checksum packaging of raw data | `runs/`, `infra/` dirs | Compressed tarball & sha256 | Missing file in archive | `AGENTS.md` §6 Phase 10 |
| 45 | Management| Managerial Progress Logging | Autonomous update logs detailing phase transitions | Pipeline events | `updates/` markdown files | Missing update log | `ORIGINAL_REQUEST.md` R5 |

---

### 12.2 Edge Cases & Boundary Handling

| # | Feature | Input / Condition | Observed / Required Behavior |
|---|---|---|---|
| 1 | Attack Guard | Non-victim IP passed (e.g. `8.8.8.8` or broadcast) | Execution immediately refused with non-zero exit; error printed to stderr; tool never spawned. |
| 2 | Attack Guard | Attack duration set to $61\text{ s}$ | Refused by guard parameter validator ($>60\text{ s}$ check). |
| 3 | Attack Guard | `hping3` invoked with `--flood` or interval $< \text{u}100$ | Refused by guard argument validator; tool never spawned. |
| 4 | Attack Guard | `conn_hold.py` invoked with $N = 2,001$ sockets | Refused by guard connection count check ($>2,000$). |
| 5 | Attack Guard | Kill switch file `/tmp/LAB_STOP` exists on attacker | Immediate execution block for all guarded tools. |
| 6 | Infrastructure | Operator public IP changes dynamically during testing | SSH hangs; detect timeout, query current IP via `curl`, update SG rule `/32`, record in `LAB_LOG.md`. |
| 7 | Attacker Kernel | Attacker kernel transmits automatic RST to victim SYN-ACK | Suppressed via explicit `iptables` drop rule; without rule, `syn_recv` stays near zero and flood is masked. |
| 8 | Sampler | Kernel does not implement optional netstat counter (e.g. `TCPReqQFullDrop`) | Sampler records empty field (`,,`), does NOT write `0`, and documents absence in handoff. |
| 9 | Sampler | Sampler execution latency spikes ($> 5\text{ ms}$) | Logged in `sample_cost_ms`; monotonic scheduler maintains pacing without drifting cumulative clock. |
| 10 | Workload | Client runs out of ephemeral ports during large flash crowd | `ab` raises "Address already in use"; widen `ip_local_port_range`, reduce concurrency, log in `notes.md`. |
| 11 | Workload | Client hits OS open file descriptor limit during connection flood | `conn_hold.py` raises `EMFILE`; pre-emptively raise client `ulimit -n 65535` and verify before execution. |
| 12 | Experiment | Victim half-open connections fail to clear within 60 s post-event | Cooldown loop waits up to 120 s for `syn_recv == 0` (10 consecutive seconds); aborts if unsettled. |
| 13 | Experiment | Inter-host clock drift exceeds $50\text{ ms}$ | Pre-run chrony tracking check triggers execution abort before launching scenario batch. |
| 14 | Detector | Long-duration flood attempts to teach EWMA baseline that flood volume is normal | Baseline freeze triggers upon initial alarm; EWMA update halted until alarm fully clears. |
| 15 | Detector | Flash crowd creates sudden volume spike with legitimate handshakes | Volume exceeds threshold, but completion ratio $C_t \approx 1.0 \ge \tau$; dual condition prevents false alarm. |
| 16 | Detector | SYN flood occurs during concurrent flash crowd (S4) | Completion ratio decreases moderately; dual condition alarms when combined volume exceeds floor and ratio drops. |
| 17 | Detector | Mitigation enabled (`syncookies = 1`) during high SYN flood (S5) | `syn_recv` stays near 0; D1 half-open branch is blind, but D2 cookie/queue pressure branch triggers alarm. |
| 18 | Infrastructure | EC2 instance exhausts CPU burst credits (`CPUCreditBalance == 0`) | Throttling slows request servicing; standard credits prevent billing surprise; credit balance logged in metadata. |

---

## 13. Traceability Matrix: Acceptance Criteria vs Implementation Deliverables

| Acceptance Criteria (from `ORIGINAL_REQUEST.md`) | Normative Section in `AGENTS.md` | Verification Deliverable & Artifact |
|---|---|---|
| **No 0.0.0.0/0 ingress; SSH restricted to operator /32** | §4.1, §6 Phase 1 | `aws ec2 describe-security-groups` output saved in `infra/lab_sg.json`. |
| **`attack_guard.sh` automated self-tests passing** | §4.2, §6 Phase 4 | Output captured in `infra/guard_selftest.txt`. |
| **`lab.env` generated; inter-node ping verified** | §5.2, §6 Phase 1 | `lab.env` created; ICMP ping output verified in `infra/ping_test.txt`. |
| **Sampler 1 row/sec over 120 s with median cost < 5 ms** | §5.5, §6 Phase 3 | `victim_metrics.csv` row count = 120 $\pm 1$; `sample_cost_ms` median $< 5\text{ ms}$. |
| **Capacity calibration determines `CAPACITY_RPS`** | §6 Phase 4 | `infra/crowd_levels.json` with small/medium/large crowd parameters. |
| **All runs contain 10 mandatory raw artifacts** | §5.3, §6 Phase 5 | Artifact audit script across all `runs/<run_id>/` directories. |
| **Master run index `runs/INDEX.csv` complete** | §5.3, §6 Phase 5 | Valid `runs/INDEX.csv` with zero undocumented omissions. |
| **Tuning strictly on reps 1–3; reporting on reps 4–5** | §6.4 | `detector/params.yaml` tuned on reps 1–3; `analysis/metrics.csv` evaluates reps 4–5. |
| **Publication figures F1–F8 at 300 DPI & tables T1–T5** | §6 Phase 9 | PNG files under `report/figures/` (300 DPI) and tables in `report/tables/`. |
| **Academic research paper `report/report.md`** | §6 Phase 10 | Completed manuscript with filled empirical brackets and threats to validity. |
| **Full AWS teardown verified with zero active resources** | §6 Phase 10 | AWS CLI query results captured in `infra/teardown_verification.txt`. |
| **Structured managerial updates in `updates/`** | §6 Phase 0–10 | Sequenced update log files (`000_...`, `001_...`, etc.) in `updates/`. |

---
*End of Formal Specification Inventory (`survey_spec.md`)*

