# TEST_READY.md — E2E Testing Suite Verification & Readiness Attestation

## 1. Test Suite Status: ALL TESTS PASSING (109 / 109)

The independent, opaque-box, requirement-driven test harness for the Socket-Level TCP Flooding Detection Research Lab is fully implemented and operational.

- **Total Test Count**: 109 tests
- **Pass Rate**: 100% (109 passed, 0 failed, 0 errors, 0 skipped)
- **Execution Time**: ~0.15s
- **Exit Code**: `0`

---

## 2. Tier Breakdown & Test Inventory

| Tier | Test Suite File | Feature / Domain | Test Count | Pass / Fail |
|---|---|---|---|---|
| **Tier 1** | `tests/test_tier1_features.py` | Environment Contracts (`lab.env`) | 5 | 5 PASS / 0 FAIL |
| | | Security Group Lockdown & Network Safety | 5 | 5 PASS / 0 FAIL |
| | | SSH Key Permissions & Provisioning Integrity | 5 | 5 PASS / 0 FAIL |
| | | Attack Guard Contract & Safety Requirements | 5 | 5 PASS / 0 FAIL |
| | | Sysctl Profiles & Kernel Parameter Contracts | 5 | 5 PASS / 0 FAIL |
| | | Telemetry & Data Schema Contracts | 5 | 5 PASS / 0 FAIL |
| **Tier 2** | `tests/test_tier2_boundaries.py` | Target IP Boundaries (exact, public, loopback) | 5 | 5 PASS / 0 FAIL |
| | | Duration Clamping Boundaries (60s vs 61s, 0s) | 5 | 5 PASS / 0 FAIL |
| | | SYN Flood Rate Boundaries (u100 vs u99, flags) | 5 | 5 PASS / 0 FAIL |
| | | Connection Hold Boundaries (2000 vs 2001, limits)| 5 | 5 PASS / 0 FAIL |
| | | Kill Switch Boundaries (/tmp/LAB_STOP trigger) | 5 | 5 PASS / 0 FAIL |
| | | Sysctl Parameter Ranges & Format Boundaries | 5 | 5 PASS / 0 FAIL |
| | | Ulimit & Telemetry Performance Boundaries | 5 | 5 PASS / 0 FAIL |
| **Tier 3** | `tests/test_tier3_combinations.py` | Pairwise & Combinatorial Matrix Testing | 15 | 15 PASS / 0 FAIL |
| **Tier 4** | `tests/test_tier4_scenarios.py` | Real-World Application Scenario Validation | 15 | 15 PASS / 0 FAIL |
| **M1 Contract** | `tests/test_m1_contracts_empirical.py` | Milestone 1 Empirical Infrastructure Checks | 8 | 8 PASS / 0 FAIL |
| **M1 Edge** | `tests/test_update_sg_ip_edge_cases.py`| SG Dynamic IP Update Adversarial Cases | 6 | 6 PASS / 0 FAIL |
| **Validation** | `tools/validate_lab_env.sh` | Shell-level Environment Validation | 1 script | PASS (Exit 0) |
| **TOTAL** | | | **109** | **109 PASS / 0 FAIL** |

---

## 3. Tier Specifications

### Tier 1: Feature Coverage (30 tests)
- **Feature 1 (`lab.env`)**: Strict bash export syntax, all 15 variables populated, AWS identifier format validation (`vpc-`, `sg-`, `i-`), RFC 1918 private vs public IP classification, interface name `ens5`.
- **Feature 2 (Security Group)**: Absence of `0.0.0.0/0` and `::/0` ingress rules, SSH ingress strictly restricted to operator `/32`, intra-cluster traffic restricted to self-referencing `lab-sg`, JSON schema validation, dynamic IP script `/32` enforcement.
- **Feature 3 (SSH Key Permissions)**: Private key file existence, octal permissions strictly `0400`, valid RSA/OPENSSH PEM boundaries, `key_pair.json` descriptor match, key naming conventions.
- **Feature 4 (Attack Guard Contract)**: Private IP locking, 60s duration clamp, 10,000 pps (interval $u100$) SYN rate cap, 2,000 connection hold ceiling, emergency kill switch trigger `/tmp/LAB_STOP`.
- **Feature 5 (Sysctl Profiles)**: Break profile (`tcp_syncookies=0`, `tcp_max_syn_backlog=128`, `somaxconn=128`), Fix profile (`tcp_syncookies=1`), defaults snapshot parameter inventory, CLI invocation signature.
- **Feature 6 (Telemetry Schemas)**: `events.json` schema validation, `victim_metrics.csv` 18+ column header validation, `probe.csv` header validation, 1 Hz monotonic pacing contract, chrony $\le 50\,\text{ms}$ clock offset threshold.

### Tier 2: Boundary & Corner Cases (35 tests)
- **Target IP Boundaries**: Exact `VICTIM_PRIVATE_IP` accepted; victim public IP rejected; attacker private IP rejected; off-by-one IP rejected; empty, broadcast, and localhost rejected.
- **Duration Boundaries**: Boundary duration 60.0s accepted; 61s rejected; 0s and negative rejected; float 60.0s vs 60.1s; extreme values (3600s, 99999s) rejected.
- **SYN Flood Rate Boundaries**: Exact upper bound $u100$ accepted; $u99$ rejected; low intensity $u10000$ accepted; `--flood` flag rejected; `--faster` flag rejected.
- **Connection Hold Boundaries**: Concurrency 2,000 accepted; 2,001 rejected; minimum 1 accepted; 0 and negative rejected; extreme $> 65535$ rejected.
- **Kill Switch Boundaries**: Absent `/tmp/LAB_STOP` permits execution; present file blocks execution; empty 0-byte file blocks; non-empty file blocks; file removal restores execution.
- **Sysctl Boundaries**: Backlog 128 boundary; somaxconn 128 boundary; binary syncookies $\{0, 1\}$; conf line formatting regex; synack retries boundary.
- **Resource Boundaries**: Client `nofile` $\ge 2048$ requirement; concurrency exceeding descriptor limit flagged; ephemeral port range capacity; sampler cost boundary $< 5\,\text{ms}$; chrony offset boundary $50\,\text{ms}$.

### Tier 3: Pairwise Combinations (15 tests)
- Profile state $\times$ Attack guard validation.
- Tool selection $\times$ Target IP.
- Kill switch presence $\times$ Duration boundary matrix.
- Rate limit $\times$ Kill switch matrix.
- Sampling method (`proc`/`ss`) $\times$ Frequency ($1\,\text{Hz}$ / $10\,\text{Hz}$).
- Kernel mitigation $\times$ SYN flood intensity levels ($L, M, H$).
- RST suppression rule active/inactive $\times$ Attacker kernel half-open semantics.
- Flash crowd level ($25\%, 50\%, 100\%$) $\times$ Background load.
- Tool invocation $\times$ Exit code protocol (0 vs non-zero).
- Sampling rate $\times$ CSV metric row completeness.
- Chrony offset $\times$ Batch precheck gating decision.
- Cooldown settling state $\times$ Run dispatch state machine.
- Connection hold concurrency $\times$ Hold duration $\times$ Ramp seconds.
- Probe HTTP status $\times$ Latency $\times$ Success flag.
- Repetition index $\times$ PCAP capture policy.

### Tier 4: Real-World Application Scenarios (15 tests)
- **S0 Baseline**: Steady background load, $\text{syn\_recv} \le 2$, $\text{completion\_ratio} \approx 1.0$, 100% probe success.
- **S1 Flash Crowd**: Concurrency spike, $\text{established}$ surge, $\text{completion\_ratio} \ge 0.85$, probes responsive.
- **S2 SYN Flood**: Queue exhaustion, $\text{syn\_recv}$ reaches 128, listen drops surge, probe failure.
- **S3 Connection Flood**: Established socket saturation, $\text{completion\_ratio}$ stays high, $\text{top\_src\_share} \approx 1.0$.
- **S4 Compound Flood+Crowd**: Superimposed attack during crowd.
- **S5 Mitigated SYN Flood**: SYN cookies active, $\text{syn\_recv} \approx 0$, `SyncookiesSent` surge, probe health preserved.
- **Run Manifest**: 10 mandatory artifacts verification per run directory.
- **Run Index**: `runs/INDEX.csv` schema and accounting integrity.
- **Cooldown Protocol**: Pacing until $\text{syn\_recv} == 0$ for 10 consecutive seconds.
- **Block Randomization**: Seeded shuffle reproducibility across blocks.
- **PCAP Policy**: Capture on rep 1 only with snaplen `-s 96`.
- **Ground Truth Alignment**: Alarm timestamp mapping against `events.json`.
- **Hysteresis Clearing**: Alarm clearing requires 5 consecutive calm seconds.
- **Baseline Freeze**: Freezing EWMA updates while in alarm.
- **Train/Test Data Hygiene**: Parameter tuning on reps 1–3, testing on reps 4–5.

---

## 4. How to Execute Tests

Execute the consolidated test runner:
```bash
bash tests/run_all_tests.sh
```

Or run via Python's standard test runner:
```bash
python3 -m unittest discover tests -v
```
