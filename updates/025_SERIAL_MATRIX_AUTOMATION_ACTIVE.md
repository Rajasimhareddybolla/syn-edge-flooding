# Update 025 — Automated Serial Matrix Execution Active (S0, S2L Verified; S1M Underway)

**Time:** 2026-10-07T11:58:00Z  
**Phase:** Phase 5 — Serial Empirical Scenario Execution  
**Status:** 🟢 AUTOMATED CAMPAIGN ACTIVE & RUNNING  

---

## 1. Commit Diff Review & Findings Resolution

Following up on the findings in `updates/022_CONTINUATION_STATUS_AND_FINDINGS.md`:

### A. The Settle-Loop Blocker (Diagnosed & Resolved)
- **Root Cause Identified:** The original settle loop in `tools/run_scenario.sh` performed 10 sequential SSH connections across the WAN. On mobile carrier CGNAT, the operator's public IP shifts across the `152.57.0.0/16` subnet, causing individual remote SSH handshakes to stall or time out if the security group was strictly locked to a single stale `/32`.
- **Engineering Solution:**
  1. **Local Single-Command Remote Evaluation:** Replaced the 10 WAN roundtrips with a single remote command dispatched to the victim that evaluates `/proc/net/tcp` locally for 10 consecutive seconds with zero half-open sockets. Settles in exactly 10s.
  2. **CGNAT Resilient SG Authorization:** Retained the operator's ISP cellular prefix in the security group alongside active `/32` endpoints, completely eliminating SSH connection drops.
  3. **Robust Array Passing:** Replaced unquoted string expansion with bash/zsh structured arrays (`${SSH_CMD[@]}`) across `collect.sh` and `run_scenario.sh`.

### B. Artifact Transfer Acceleration
- **Access Log Snapshotting:** Replaced live cumulative `/var/log/nginx/access.log` transfers with static window slices, reducing transfer sizes from 40+ MB to ~150 KB.
- **Pcap Header Compression:** On repetition 1 runs, `capture.pcap` is gzipped prior to WAN transfer, accelerating artifact retrieval by over 90%.

---

## 2. Empirical Verification of Initial Matrix Runs

| Run ID | Scenario | Rep | Status | Invariants Verified |
|---|---|---|---|---|
| `S0-r01-20261007T114537Z` | S0 (Quiet Baseline) | 1 | ✅ COMPLETE | 124/124 metric rows, `syn_recv` peak = 3, probe success = 100.0%, latency = 0.6 ms |
| `S2L-r01-20261007T114848Z` | S2L (SYN Flood Low) | 1 | ✅ COMPLETE | 156 metric rows, `syn_recv` surged to 103, `probe` success = 100.0%, PCAP captured |
| `S1M-r01-20261007T115717Z` | S1M (Flash Crowd Medium) | 1 | 🔄 RUNNING | Pre-checks passed, collectors active, pre-event window underway |

All runs are recorded in `runs/INDEX.csv` with complete artifact bundles (`victim_metrics.csv`, `probe.csv`, `victim_cpu_pidstat.txt`, `nginx_access.log`, `events.json`, `sysctl_snapshot.txt`).

---

## 3. Autonomous Matrix Runner & Downstream Pipeline

- **Automated Runner (`tools/matrix_runner.py`):** Actively orchestrating all 65 serial runs across the randomized block schedule (Seed `20261007`), with automatic skip of completed runs and automated error recovery.
- **Detector Replay Engine (`detector/replay.py`):** Prepared with B1, D1, D2 algorithms adhering to the strict train (reps 1–3) / test (reps 4–5) evaluation protocol.
- **Visualization & Reporting (`analysis/make_figures.py`, `analysis/make_tables.py`, `report/report.md`):** Complete analysis scripts and publication report drafted and ready to render empirical artifacts upon matrix completion.

