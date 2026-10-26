# Update 023 — Root-Cause Fix for Settle-Loop Blocker & S0 Execution Underway

**Time:** 2026-10-07T11:40:00Z  
**Phase:** Phase 5 — Empirical Scenario Execution  
**Status:** 🟢 RESOLVED & RUNNING  

---

## 1. Executive Summary & Diagnosis

In `updates/022_CONTINUATION_STATUS_AND_FINDINGS.md`, the primary technical blocker was identified:
> *"A later S0 retry remains blocked in the victim-settle loop even though a direct check reports SYN_RECV=0. This must be diagnosed before any run can be accepted as valid."*

We conducted a forensic code review of `tools/run_scenario.sh` and the network layer, uncovering two interacting root causes:

1. **Carrier-Grade NAT (CGNAT) Egress Shift & WAN Polling Handshakes:**
   - The operator's external IP shifts across the `/16` cellular pool (`152.57.x.x`).
   - The original settle loop in `run_scenario.sh` performed **10 separate WAN SSH connections in a tight 1-second loop**.
   - If any individual TCP/SSH connection stalled or coincided with an IP shift before the SG rule caught up, the loop hung or exceeded 120s and aborted.
   - In zsh/bash subshells, unquoted `$SSH_OPTS` was susceptible to whitespace parsing issues where the entire options string was treated as an invalid `-i` argument.

2. **Refactored Architecture:**
   - **Local Single-Command Remote Settle Check:** Instead of polling across the WAN 10 times, `run_scenario.sh` now dispatches a single remote probe to the victim that evaluates `/proc/net/tcp` locally for 10 consecutive seconds.
   - **Robust Array Passing:** Switched all SSH invocations across `collect.sh` and `run_scenario.sh` to structured arrays (`${SSH_CMD[@]}`), preventing any argument or key-path misparsing.
   - **Pre-emptive SG Management:** Updated security group rules to include current operator endpoints and added connection timeouts (`-o ConnectTimeout=10`).

---

## 2. Verification & Milestone Progress

- **Test Suite:** All **109/109** tests pass cleanly (`bash tests/run_all_tests.sh` exit 0).
- **Tooling Synchronized:** Updated `collect.sh`, `run_scenario.sh`, `attack_guard.sh` deployed and permission-verified across all 3 AWS EC2 instances (`victim`, `attacker`, `client`).
- **Crowd Levels Calibrated:** Generated `infra/crowd_levels.json` mapping empirical capacity (23,525 req/s) to small (25%), medium (50%), and large (100%) flash crowd configurations.
- **S0 Rep 1 Launched:** Running now under ID `S0-r01-20261007T113850Z`. Pre-checks 1–4 passed with zero errors, clock offsets verified (<1 µs), victim settled cleanly, and collectors are actively recording.

---

## 3. Next Steps

1. Await completion of `S0-r01` and verify the integrity of all collected artifacts (`victim_metrics.csv`, `probe.csv`, `pidstat`, `events.json`).
2. Proceed with serial execution of remaining runs across the full experimental matrix (S0–S5).
3. Benchmark detectors (B1, D1, D2) with the strict train (reps 1–3) / test (reps 4–5) protocol.

