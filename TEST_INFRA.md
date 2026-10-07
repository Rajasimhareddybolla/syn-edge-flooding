# TEST_INFRA.md — End-to-End Testing Infrastructure & Specification

## 1. Testing Philosophy

### 1.1 Opaque-Box, Requirement-Driven Verification
The research lab pipeline investigates socket-level lightweight detection of TCP flooding attacks on edge Linux instances. Safety, reproducibility, and rigorous empirical validation are paramount. The testing infrastructure is designed around an **opaque-box, requirement-driven philosophy**:
- **Implementation Agnostic**: Tests are derived strictly from normative requirements in `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `docs/AGENTS_tcp_flood_lab.md` (RFC 2119 keywords: **MUST**, **MUST NOT**, **SHOULD**). Tests verify observable behavior, interface contracts, kernel boundaries, and invariant properties rather than internal implementation quirks.
- **Authoritative Expected Output Derivation**: Expected outputs are grounded in explicit specifications:
  - AWS EC2 Security Group isolation: RFC 1918 private subnets, `/32` operator SSH restriction, strict prohibition of `0.0.0.0/0` ingress rules.
  - Fail-safe attack guard boundaries: String-exact target IP verification (`VICTIM_PRIVATE_IP`), duration clamp $\le 60\,\text{s}$, SYN rate cap $\le 10{,}000\,\text{pps}$ ($\ge u100$), connection hold limit $\le 2{,}000$, and immediate kill-switch halting on `/tmp/LAB_STOP`.
  - Kernel telemetry schemas: 1 Hz monotonic `/proc/net/tcp`, `/proc/net/snmp`, and `/proc/net/netstat` delta streams with median sample latency $< 5\,\text{ms}$.
  - Experimental run artifacts: Exactly 10 mandatory artifacts per run directory with zero missing deltas and strict train/test separation (reps 1–3 for tuning, reps 4–5 for evaluation).

### 1.2 Progressive Testability
During milestone progression (M1 through M6), the test harness operates under **progressive testability**:
- Tests are verifiable using features from completed milestones and independent contract/logic verification.
- For in-progress or planned milestones, tests validate the specification models, interface contracts, parameter bounds, schema validators, and behavioral harnesses.
- Tests do not raise false negatives when optional or subsequent-phase physical resources are idle.

### 1.3 Test Independence and Isolation
- Each test is self-contained and isolated.
- Tests do not depend on test execution order.
- Any temporary state or mock files (e.g. temporary kill-switch markers, mocked environment files) are created in isolated temporary directories and cleaned up immediately in test teardown.

---

## 2. 4-Tier Test Architecture

The test suite is structured into four distinct, complementary tiers:

```
+-------------------------------------------------------------------------------+
|                        4-TIER TEST ARCHITECTURE                               |
+-------------------------------------------------------------------------------+
| Tier 1: Feature Coverage (>=5 tests per feature)                              |
|   - M1/M2/M3 interface contracts, environment variables, security groups,    |
|     SSH permissions, attack guard safety rules, sysctl profiles, telemetry    |
+-------------------------------------------------------------------------------+
| Tier 2: Boundary & Corner Cases (>=5 tests per feature)                       |
|   - Target IP boundaries, duration (60s vs 61s), rate (u100 vs u99),          |
|     conns (2000 vs 2001), kill switch presence, sysctls, ulimits, chrony      |
+-------------------------------------------------------------------------------+
| Tier 3: Pairwise Combinations                                                 |
|   - Profile state (break/fix) x Guard enforcement x Network state             |
|   - Tool selection x Duration x Rate x Kill switch matrix                     |
+-------------------------------------------------------------------------------+
| Tier 4: Real-World Application Scenarios                                      |
|   - S0 Baseline, S1 Flash Crowd, S2 SYN Flood, S3 Connection Flood,           |
|     S4 Compound Flood+Crowd, S5 SYN-Cookie Mitigation, Run Manifest & Replay  |
+-------------------------------------------------------------------------------+
```

### Tier 1: Feature Coverage ($\ge 5$ tests per feature)
Tier 1 establishes baseline behavioral conformance for all primary functional units and interface contracts:
1. **Environment Configuration & Interface Contracts (`lab.env`)**:
   - Verification of 15 mandatory environment variables.
   - Strict bash export syntax compliance.
   - AWS identifier schema validation (`vpc-`, `sg-`, `i-`).
   - Strict differentiation between public IPs, private IPs, and interface names.
   - Monotonic interface name contract (`ens5`).
2. **Security Group Lockdown & Network Safety**:
   - Zero-tolerance verification against `0.0.0.0/0` ingress rules.
   - SSH ingress restricted strictly to operator `/32`.
   - Cluster intra-traffic bounded to self-referential `lab-sg` group.
   - Verification of AWS security group description JSON schema.
   - Dynamic IP update script contract verification (`update_sg_ip.sh`).
3. **SSH Key Security & Provisioning Permissions**:
   - Private key existence on filesystem.
   - Octal file permissions strictly `0400` (read-only for owner).
   - Valid PEM header and footer structure.
   - Key pair descriptor synchronization with `lab.env`.
   - Matching key name and filename conventions.
4. **Attack Guard Contract & Specification**:
   - Strict locking to `VICTIM_PRIVATE_IP`.
   - Absolute duration clamp at $\le 60\,\text{s}$.
   - SYN flood packet rate cap $\le 10{,}000\,\text{pps}$ (interval $\ge u100$).
   - Connection hold concurrency cap $\le 2{,}000$.
   - Host-wide emergency kill switch `/tmp/LAB_STOP` refusal.
5. **Sysctl Profiles & Kernel Parameter Configuration**:
   - Break profile: `net.ipv4.tcp_syncookies=0`, `net.ipv4.tcp_max_syn_backlog=128`, `net.core.somaxconn=128`.
   - Fix profile: `net.ipv4.tcp_syncookies=1` with backlogs preserved.
   - Sysctl defaults inventory and snapshot contract.
   - CLI invocation signature: `tools/set_profile.sh {break|fix}`.
   - Profile verification command format and output regex.
6. **Telemetry & Data Schema Contracts**:
   - `events.json` schema validation (ground truth, timestamps, git SHA, offsets).
   - `victim_metrics.csv` 18-column schema (socket states, SNMP/Netstat deltas, CPU/MEM).
   - `probe.csv` schema (`ts_ms,http_code,t_connect_s,t_total_s,ok`).
   - 1 Hz monotonic sampling pacing contract.
   - Chrony clock offset threshold ($\le 50\,\text{ms}$) across nodes.

### Tier 2: Boundary & Corner Cases ($\ge 5$ tests per feature)
Tier 2 subjects each boundary condition to adversarial edge values and off-by-one transitions:
1. **Target IP Boundaries**:
   - Exact victim private IP accepted.
   - Victim public IP rejected.
   - Attacker private IP rejected (self-targeting loopback).
   - Subnet off-by-one IP rejected (e.g. `172.31.37.215`).
   - Empty, broadcast (`255.255.255.255`), and localhost (`127.0.0.1`) rejected.
2. **Duration Clamping Boundaries**:
   - Upper boundary duration $60\,\text{s}$ accepted.
   - Boundary breach duration $61\,\text{s}$ rejected.
   - Zero duration ($0\,\text{s}$) rejected.
   - Negative durations ($-1\,\text{s}$) rejected.
   - Extreme duration values ($99999\,\text{s}$) rejected.
3. **SYN Flood Rate Boundaries**:
   - Exact upper rate boundary $u100$ ($10{,}000\,\text{pps}$) accepted.
   - Rate limit breach $u99$ ($10{,}101\,\text{pps}$) rejected.
   - Low intensity $u10000$ ($100\,\text{pps}$) accepted.
   - Flag `--flood` strictly rejected.
   - Flag `--faster` strictly rejected.
4. **Connection Hold Concurrency Boundaries**:
   - Upper concurrency boundary $2{,}000$ accepted.
   - Concurrency boundary breach $2{,}001$ rejected.
   - Minimum valid concurrency $1$ accepted.
   - Zero and negative connection counts rejected.
   - Concurrency exceeding port allocation limits rejected.
5. **Kill Switch Trigger Boundaries**:
   - Absent `/tmp/LAB_STOP` allows execution.
   - Present `/tmp/LAB_STOP` immediately aborts execution.
   - Empty `/tmp/LAB_STOP` file aborts execution.
   - Non-empty `/tmp/LAB_STOP` file aborts execution.
   - Mid-flight creation of `/tmp/LAB_STOP` halts execution.
6. **Sysctl Parameter Range Boundaries**:
   - Backlog value 128 boundary.
   - Somaxconn value 128 boundary.
   - Syncookies binary values ($0$ vs $1$).
   - Sysctl conf configuration file formatting.
   - Synack retries default boundary.
7. **Ulimit & Resource Boundaries**:
   - Client open file descriptor limit `ulimit -n` $\ge 2048$.
   - Concurrency exceeding active descriptor ceiling rejected.
   - Ephemeral port range exhaustion handling.
   - Sampler execution cost boundary $< 5\,\text{ms}$.
   - Clock offset threshold boundary $50\,\text{ms}$.

### Tier 3: Pairwise Combinations
Tier 3 tests combinatorial interactions across multiple system components:
- Profile state (`break`/`fix`) $\times$ Attack guard execution (permitted/refused).
- Tool selection (`hping3`/`conn_hold`/`wrk`/`ab`) $\times$ Target IP (valid/invalid).
- Kill switch presence $\times$ Attack duration ($30\,\text{s}$ / $60\,\text{s}$ / $61\,\text{s}$).
- Rate limit ($u100$ / $u1000$ / $u99$) $\times$ Kill switch state.
- Metric collection method (`proc`/`ss`) $\times$ Sampling frequency ($1\,\text{Hz}$ / $10\,\text{Hz}$).
- Network RST suppression state $\times$ SYN flood response.
- Concurrency levels (Small / Medium / Large) $\times$ Background load.
- Compound Scenario S4 (SYN flood + flash crowd) $\times$ Kernel mitigation state.
- Attack tool invocation $\times$ Exit code protocol.
- Sampling rate $\times$ CSV metric column completeness.
- Chrony offset ($\le 50\,\text{ms}$ vs $> 50\,\text{ms}$) $\times$ Batch run gating.
- Cooldown settling state (`syn_recv == 0` for 10 s vs unsettled) $\times$ Scenario dispatch.
- Connection hold concurrency $\times$ Hold duration $\times$ Ramp time combinations.
- Probe HTTP status $\times$ Latency $\times$ Success flag.
- Repetition index ($1 \dots 5$) $\times$ PCAP capture enablement.

### Tier 4: Real-World Application Scenarios
Tier 4 validates the entire end-to-end scientific pipeline workflows:
- **Scenario S0**: Quiet baseline workload, verifying steady state ($\text{syn\_recv} \le 2$, $\text{completion\_ratio} \approx 1.0$, 100% probe success).
- **Scenario S1**: Flash crowd workload (S1S, S1M, S1L), verifying surge in established sockets with high completion ratio ($\ge 0.80$) and responsive probes.
- **Scenario S2**: SYN flood attack unmitigated (S2L, S2M, S2H), verifying queue exhaustion, listen drops surge, completion ratio collapse ($< 0.30$), and probe degradation.
- **Scenario S3**: Connection hold attack (S3L, S3M, S3H), verifying established socket saturation, high completion ratio, and `top_src_share` $\approx 1.0$.
- **Scenario S4**: Compound attack during crowd, validating superposition of legitimate and malicious traffic.
- **Scenario S5**: SYN flood mitigated by kernel cookies, verifying $\text{syn\_recv} \approx 0$, `SyncookiesSent` surge, and service probe recovery.
- **Run Manifest & Artifact Validation**: Verification of 10 mandatory artifacts in every run folder.
- **Run Index CSV Schema & Accounting**: Validation of `runs/INDEX.csv` tracking.
- **Cooldown & Recovery Enforcer**: Simulated pacing ensuring 10 consecutive seconds of $\text{syn\_recv} = 0$.
- **Randomized Block Order & Seeded Shuffling**: Ensuring unbiased scenario execution.
- **PCAP Capture Policy**: Enforcing capture on repetition 1 only with header-only snaplen (`-s 96`).
- **Ground Truth & Event Alignment**: Verification of detector alarm timestamp mapping against `events.json`.
- **Hysteresis Alarm Clearing**: Validation of 5 consecutive calm seconds requirement.
- **Baseline Freeze Mechanism**: Ensuring EWMA does not learn attack volume as normal.
- **Train/Test Data Hygiene**: Validating hyperparameter tuning on reps 1–3 and reporting on reps 4–5.

---

## 3. Coverage Thresholds & Quality Criteria

| Metric | Target Threshold | Rationale |
|---|---|---|
| **Tier 1 Feature Tests** | $\ge 5$ tests per feature | Exhaustive coverage of interface contracts & requirements |
| **Tier 2 Boundary Tests** | $\ge 5$ tests per feature | Rigorous boundary and off-by-one stress testing |
| **Tier 3 Combination Tests** | $\ge 15$ pairwise tests | Cross-feature interaction coverage |
| **Tier 4 Scenario Tests** | $\ge 15$ scenario tests | End-to-end workflow and scientific artifact validation |
| **Overall Test Pass Rate** | **100% (Zero Failures)** | All tests must pass cleanly |
| **Execution Exit Code** | `0` | Script runner returns 0 on complete pass |

---

## 4. Test Execution Instructions

### 4.1 Consolidated Runner
To run all test suites across all tiers with formatted reporting:
```bash
bash tests/run_all_tests.sh
```

### 4.2 Direct Python Test Discovery
To execute using Python's standard `unittest` module:
```bash
python3 -m unittest discover tests -v
```

### 4.3 Running Individual Tiers
```bash
# Tier 1: Feature Coverage
python3 -m unittest tests/test_tier1_features.py -v

# Tier 2: Boundary & Corner Cases
python3 -m unittest tests/test_tier2_boundaries.py -v

# Tier 3: Pairwise Combinations
python3 -m unittest tests/test_tier3_combinations.py -v

# Tier 4: Real-World Application Scenarios
python3 -m unittest tests/test_tier4_scenarios.py -v
```
