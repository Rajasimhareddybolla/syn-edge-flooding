# Project: Socket-Level Lightweight Detection of TCP Flooding Attacks in Edge Networks

## Architecture
- **Topology:** 3 EC2 nodes in default VPC (`ap-south-1a`, subnet `subnet-0709c5a163cc423bb`):
  - `victim` (`t3.micro`): Nginx server (`listen 80 backlog=128`), `sampler.py` (1 Hz `/proc/net/tcp`, snmp, netstat reader), `detector.py`, pidstat.
  - `attacker` (`t3.micro`): `attack_guard.sh` bounded runner, `hping3`, `conn_hold.py`, iptables RST suppression drop rule.
  - `client` (`t3.micro`): `wrk` (background load), `ab` (flash crowd), `probe.sh` (1 Hz HTTP probe).
- **Security:** Security Group `lab-sg` allows SSH (port 22) only from operator IP `152.57.107.6/32`, all traffic between instances in `lab-sg` only. 0.0.0.0/0 strictly forbidden.
- **Dual Track Organization:**
  - Implementation Track: Sequential Milestones M1 through M6.
  - E2E Testing Track: Parallel requirement-driven opaque-box testing harness (Tiers 1-4) creating `TEST_INFRA.md` and `TEST_READY.md`.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Target IP Verification | Strict enforcement that attack target matches `VICTIM_PRIVATE_IP` | M2 | survey_spec §12.1 |
| 2 | Duration Clamping | Enforce maximum duration <= 60s via timeout | M2 | survey_spec §12.1 |
| 3 | Rate Limiting (SYN) | Limit hping3 interval to >= u100 (<= 10,000 pps) | M2 | survey_spec §12.1 |
| 4 | Connection Hold Limit | Enforce max connection count <= 2,000 | M2 | survey_spec §12.1 |
| 5 | Emergency Kill Switch | Host-wide kill switch via presence of /tmp/LAB_STOP | M2 | survey_spec §12.1 |
| 6 | Security Group Lockdown | Prohibit 0.0.0.0/0 ingress; restrict SSH to /32 | M1 | survey_spec §12.1 |
| 7 | Multi-Node Testbed Provisioning | AWS EC2 3-node topology (victim, attacker, client) | M1 | survey_spec §12.1 |
| 8 | Dynamic IP SG Update | Dynamic update of operator SSH rule upon IP shift | M1 | survey_spec §12.1 |
| 9 | Standard CPU Credit Enforcement | Launch with --credit-specification CpuCredits=standard | M1 | survey_spec §12.1 |
| 10 | RST Suppression Rule | Drop outbound kernel TCP RST on attacker for raw SYNs | M2 | survey_spec §12.1 |
| 11 | Sysctl Break/Fix Profiles | Toggle vulnerable vs mitigated kernel state | M2 | survey_spec §12.1 |
| 12 | Sysctl Defaults Snapshot | Snapshot original system kernel defaults | M2 | survey_spec §12.1 |
| 13 | Chrony Synchronization Check | Check clock offset across testbed nodes (< 50ms) | M2 | survey_spec §12.1 |
| 14 | Socket-State Sampler (Proc) | 1 Hz monotonic reading of /proc/net/tcp, snmp, netstat | M3 | survey_spec §12.1 |
| 15 | Socket-State Sampler (SS) | Secondary 1 Hz sampler shelling out to ss -tan | M3 | survey_spec §12.1 |
| 16 | HTTP Probe Generator | 1 Hz curl probing from client with 3s max time | M3 | survey_spec §12.1 |
| 17 | Automated Run Collector | Orchestrated startup/fetch of pidstat, sampler, probe | M3 | survey_spec §12.1 |
| 18 | Victim Capacity Calibration | Determine CAPACITY_RPS via stepped wrk concurrency | M3 | survey_spec §12.1 |
| 19 | Bounded Quiet Background Load | Low steady background HTTP load via wrk | M3 | survey_spec §12.1 |
| 20 | Bounded Flash Crowd Generator | Concurrency-driven legitimate arrivals via ab | M3 | survey_spec §12.1 |
| 21 | Bounded SYN Flood Generator | Controlled raw SYN flood via hping3 and guard | M3 | survey_spec §12.1 |
| 22 | Async Connection Hold Generator | Asyncio connection exhaustion via partial HTTP lines | M3 | survey_spec §12.1 |
| 23 | Serial Scenario Matrix Runner | Automated, strictly serial execution of S0–S5 runs | M4 | survey_spec §12.1 |
| 24 | Cooldown & Recovery Enforcer | Verification that syn_recv == 0 for 10s before run | M4 | survey_spec §12.1 |
| 25 | Randomized Block Order | Seeded scenario execution shuffling per block | M4 | survey_spec §12.1 |
| 26 | Header-Only PCAP Capture | Packet capture on port 80 during rep 1 of each scenario | M4 | survey_spec §12.1 |
| 27 | Offline Replay Engine | Row-by-row simulation of detector against CSV traces | M5 | survey_spec §12.1 |
| 28 | Online Edge Detector | Live socket monitoring and real-time alarming | M5 | survey_spec §12.1 |
| 29 | Baseline Volume Detector (B1) | Static volume thresholding on half-open and passive opens | M5 | survey_spec §12.1 |
| 30 | Adaptive Dual-Signal Detector (D1) | EWMA baseline volume + handshake completion ratio | M5 | survey_spec §12.1 |
| 31 | Baseline Freeze Mechanism | Freezes EWMA update while alarm is active | M5 | survey_spec §12.1 |
| 32 | Hysteresis Alarm Clearing | Clears active alarm only after M=5 calm seconds | M5 | survey_spec §12.1 |
| 33 | Connection Flood Branch (D2) | Alarms on established growth + top source concentration | M5 | survey_spec §12.1 |
| 34 | SYN Cookie Branch (D2) | Alarms on cookie generation and queue drop rates | M5 | survey_spec §12.1 |
| 35 | Machine Learning Benchmark (D3) | Decision tree / isolation forest socket classifier | M5 | survey_spec §12.1 |
| 36 | Parameter Tuning & Train/Test Split | Hyperparameter optimization on reps 1–3, testing on 4–5 | M5 | survey_spec §12.1 |
| 37 | Detection Latency & Delay Metric | Measure time delta from attack start to first alarm | M5 | survey_spec §12.1 |
| 38 | False Alarm Quantification | Measure alarm frequency and duration on benign runs | M5 | survey_spec §12.1 |
| 39 | Computational Overhead Profiler | Measure CPU %, RSS, and sampling latency across O0–O4 | M5 | survey_spec §12.1 |
| 40 | Publication Visualizations F1–F8 | 300 DPI publication plots of empirical data | M5 | survey_spec §12.1 |
| 41 | Publication Tables T1–T5 | Formatted markdown/LaTeX summary tables | M5 | survey_spec §12.1 |
| 42 | Academic Paper Report | Complete research manuscript with filled abstract | M6 | survey_spec §12.1 |
| 43 | Resource Teardown & Verification | Destroy AWS instances, SG, keys, and verify zero spend | M6 | survey_spec §12.1 |
| 44 | Run Artifact Archive | Cryptographic checksum packaging of raw data | M6 | survey_spec §12.1 |
| 45 | Managerial Progress Logging | Autonomous update logs detailing phase transitions | M6 | survey_spec §12.1 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Preflight & AWS Infrastructure Provisioning | Git repo init, local tools (`matplotlib`), AWS SG `lab-sg` (/32 only), EC2 key pair, launch 3 `t3.micro` nodes in `ap-south-1a`, generate `lab.env`, ICMP verification, `STATE.md`, `LAB_LOG.md`. | none | **DONE** (Output: `lab.env`, instances running, `infra/ping_verification.txt`, gate passed) |
| M2 | Victim Environment, Tooling & Safety Guardrails | Ubuntu package installs, Nginx setup with backlog=128, sysctl break/fix profiles, snapshot defaults, attacker iptables RST drop rule, `attack_guard.sh` and `guard_selftest.sh` verification. | M1 | PLANNED |
| M3 | Telemetry Instrumentation & Traffic Calibration | `sampler.py` (1 Hz /proc, <5ms latency), `probe.sh`, `conn_hold.py`, `collect.sh`, capacity calibration (`CAPACITY_RPS`), `crowd_levels.json`, generator dry runs. | M2 | PLANNED |
| M4 | Empirical Scenario Matrix Execution | Serial scenario runner `run_scenario.sh`, execute 65 runs across S0–S5, pre-checks, randomized blocks, cooldown enforcement, populate `runs/<run_id>/` (10 artifacts) and `runs/INDEX.csv`. | M3 | PLANNED |
| M5 | Detection Benchmark, Tuning & Publication Analysis | `replay.py`, `detector.py` (B1, D1, D2), grid tuning on reps 1–3 (`params.yaml`), evaluation on reps 4–5 (`metrics.csv`), overhead benchmarks O0–O4 (`overhead.csv`), figures F1–F8 (300 DPI) and tables T1–T5. | M4 | PLANNED |
| M6 | Academic Reporting, Teardown & Verification | Write `report/report.md` filling abstract template and empirical data, AWS resource termination, `infra/teardown_verification.txt`, tarball archive of runs, final update log in `updates/`. | M5 | PLANNED |
| E2E | E2E Testing Track | Independent opaque-box test suite for research pipeline (Tiers 1-4), `TEST_INFRA.md`, and `TEST_READY.md`. | M1 | PLANNED |

## Interface Contracts
### M1 -> M2 (`lab.env`)
- `lab.env` exports: `AWS_REGION="ap-south-1"`, `VPC_ID="vpc-091281d6eb74da886"`, `SG_ID="sg-09e89875382c47277"`, `KEY_NAME="tcp-flood-lab"`, `KEY_PATH="/Users/raja/.ssh/tcp-flood-lab.pem"`, `VICTIM_ID="i-0f89c07ce382931f2"`, `ATTACKER_ID="i-03e8f67a9cb58c94a"`, `CLIENT_ID="i-07f191b24634a44ca"`, `VICTIM_PUB="13.235.246.92"`, `ATTACKER_PUB="65.2.190.166"`, `CLIENT_PUB="13.206.119.8"`, `VICTIM_PRIVATE_IP="172.31.37.214"`, `ATTACKER_PRIVATE_IP="172.31.42.168"`, `CLIENT_PRIVATE_IP="172.31.41.87"`, `VICTIM_IFACE="ens5"`.
- Inter-node ICMP ping succeeds.

### M2 -> M3 (Host Readiness & Safety)
- Victim responds with HTTP 200 to `curl http://$VICTIM_PRIVATE_IP/`.
- `set_profile.sh {break|fix}` toggles `tcp_syncookies`.
- Attacker drops RST to victim: `iptables -C OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP`.
- `attack_guard.sh` refuses invalid IP, duration > 60s, rate > 10,000 pps, conns > 2,000, or kill switch present.

### M3 -> M4 (Generators & Calibration)
- `tools/sampler.py --out <csv>` produces monotonic 1 Hz rows with median cost < 5ms.
- `tools/probe.sh` outputs `ts_ms,http_code,t_connect_s,t_total_s,ok`.
- `infra/crowd_levels.json` defines Small, Medium, Large concurrency levels mapped from `CAPACITY_RPS`.

### M4 -> M5 (Raw Empirical Data)
- 65 run directories in `runs/<run_id>/` containing all 10 mandatory artifacts: `events.json`, `victim_metrics.csv`, `probe.csv`, `load_client.txt`, `attack_attacker.txt`, `sysctl_snapshot.txt`, `nginx_access.log`, `victim_cpu_pidstat.txt`, `capture.pcap` (rep 1), `notes.md`.
- `runs/INDEX.csv` index file.

### M5 -> M6 (Analysis Artifacts)
- `analysis/metrics.csv` containing detection rates, false alarm rates, and detection delays for B1, D1, D2.
- `analysis/overhead.csv` containing CPU %, RSS MB, and sample cost for O0–O4.
- Figures `analysis/figures/F1` through `F8` (PNG, 300 DPI).
- Tables `analysis/tables/T1` through `T5`.

### M6 -> Complete
- `report/report.md` filled with empirical values and threats to validity.
- AWS CLI confirmation that all EC2 instances are terminated and SG deleted.

## Code Layout
```
/Users/raja/Documents/syn-edge-flooding/
  lab.env
  STATE.md
  LAB_LOG.md
  PROJECT.md
  TEST_INFRA.md
  TEST_READY.md
  infra/
    sysctl_defaults.txt
    attacker_rules.txt
    guard_selftest.txt
    crowd_levels.json
    teardown_verification.txt
  tools/
    sampler.py
    probe.sh
    attack_guard.sh
    guard_selftest.sh
    conn_hold.py
    collect.sh
    run_scenario.sh
    set_profile.sh
  detector/
    detector.py
    replay.py
    params.yaml
  runs/
    INDEX.csv
    <run_id>/
  analysis/
    metrics.csv
    overhead.csv
    generate_figures.py
    generate_tables.py
    figures/ (F1.png - F8.png)
    tables/ (T1.md - T5.md)
  report/
    report.md
  updates/
    *.md
  tests/
    test_tier1_features.py
    test_tier2_boundaries.py
    test_tier3_combinations.py
    test_tier4_scenarios.py
    run_all_tests.sh
```
