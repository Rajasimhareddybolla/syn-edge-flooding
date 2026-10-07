# STATE — Socket-Level Lightweight Detection of TCP Flooding Attacks

**Document Version:** 1.0  
**Integrity Mode:** development  
**Current Phase:** Phase 2 (Victim Environment & Tooling / Milestone M2 Ready)  
**Overall Status:** IN_PROGRESS  
**Lead Orchestrator:** orchestrator_1 (conversationId: f6cfd525-c586-41eb-8148-3a42cc6823d8)  
**Last Updated:** 2026-10-07T07:12:00Z  

---

## 1. Human Safety Gates Status

| Gate ID | Description | Threshold / Trigger | Status | Confirmed By | Timestamp | Evidence / Artifact |
|---|---|---|---|---|---|---|
| **G1** | AWS Simulated DoS / Security Testing Policy Compliance | Mandatory prior to Phase 1 cloud provisioning | CONFIRMED | Raja (Human Owner) | 2026-10-07T06:40:00Z | Confirmed in chat & logged in `LAB_LOG.md` |
| **G2** | Attack Guard Bounded Enforcement Self-Test Verification | Mandatory prior to Phase 5 first attack execution | PENDING | — | — | Awaiting `infra/guard_selftest.txt` (Phase 4) |
| **G3** | Operational Cap Escalation (Rate, Duration, Conns) | Triggered only if raising caps defined in §4.2 | NONE | — | — | Strict default caps active: $\le$60s, $\le$10k pps, $\le$2k conns |

---

## 2. Phase Gating & Milestone Lifecycle Matrix

| Phase | Milestone | Name | Owner | Status | Started | Completed | Primary Artifacts | Handoff Report |
|---|---|---|---|---|---|---|---|---|
| **0** | M1 | Preflight & Scaffolding | worker_m1 | COMPLETE | 2026-10-07T06:20:27Z | 2026-10-07T06:55:00Z | `.gitignore`, `STATE.md`, `LAB_LOG.md`, directories | `handoffs/A0.md` |
| **1** | M1 | AWS Infrastructure Provisioning | worker_m1 | COMPLETE | 2026-10-07T06:55:00Z | 2026-10-07T07:11:00Z | `lab.env`, `infra/sg_described.json`, `infra/instances_described.json`, `infra/ping_verification.txt` | `handoffs/A1.md` |
| **2** | M2 | Victim Environment & Tooling | A2 | PLANNED | — | — | Nginx backlog=128, sysctl profiles, `infra/attacker_rules.txt`, defaults | `handoffs/A2.md` |
| **3** | M3 | Telemetry Instrumentation | A3 | PLANNED | — | — | `tools/sampler.py`, `tools/probe.sh`, `tools/collect.sh` | `handoffs/A3.md` |
| **4** | M3 | Traffic Calibration & Guardrails | A4 | PLANNED | — | — | `tools/attack_guard.sh`, `infra/guard_selftest.txt`, `infra/crowd_levels.json` | `handoffs/A4.md` |
| **5** | M4 | Empirical Scenario Execution | A5 | PLANNED | — | — | 65 runs in `runs/<run_id>/`, `runs/INDEX.csv` | `handoffs/A5.md` |
| **6** | M5 | Detection Benchmark & Tuning | A6 | PLANNED | — | — | `detector/replay.py`, `detector/params.yaml`, `analysis/metrics.csv` | `handoffs/A6.md` |
| **7** | M5 | Mitigation Analysis (SYN Cookies) | A6 | PLANNED | — | — | S2 vs S5 comparative metrics in `analysis/metrics.csv` | `handoffs/A6.md` |
| **8** | M5 | Overhead Profiling (O0–O4) | A5/A6 | PLANNED | — | — | `analysis/overhead.csv`, pidstat traces | `handoffs/A6.md` |
| **9** | M5 | Publication Figures & Tables | A6/A7 | PLANNED | — | — | Figures `analysis/figures/F1–F8`, Tables `analysis/tables/T1–T5` | `handoffs/A7.md` |
| **10** | M6 | Academic Report & Teardown | A7/A1 | PLANNED | — | — | `report/report.md`, `infra/teardown_verification.txt`, run archive | `handoffs/A7.md` |

---

## 3. Active Cloud Resources Inventory

| Attribute | Specification Value | Actual Provisioned Value |
|---|---|---|
| **AWS Region** | `ap-south-1` (Mumbai) | `ap-south-1` |
| **VPC ID** | Default VPC | `vpc-091281d6eb74da886` |
| **Availability Zone / Subnet** | `ap-south-1a` | `subnet-0709c5a163cc423bb` |
| **Security Group ID** | `lab-sg` (SSH /32 only) | `sg-09e89875382c47277` |
| **EC2 Key Pair Name** | `tcp-flood-lab` | `tcp-flood-lab` (`~/.ssh/tcp-flood-lab.pem`, 400) |
| **Ubuntu 24.04 AMI** | Noble HVM gp3 x86_64 | `ami-065d2b03fb493085a` |
| **Victim Instance** | `t3.micro` (`ens5`) | `i-0f89c07ce382931f2` (Pub: `13.235.246.92`, Priv: `172.31.37.214`) |
| **Attacker Instance** | `t3.micro` | `i-03e8f67a9cb58c94a` (Pub: `65.2.190.166`, Priv: `172.31.42.168`) |
| **Client Instance** | `t3.micro` | `i-07f191b24634a44ca` (Pub: `13.206.119.8`, Priv: `172.31.41.87`) |
| **Total Active EC2 Instances** | Max 3 | 3 |
| **Estimated Accrued Cost** | $\le$ $15.00 limit | < $0.05 |

---

## 4. Active Blockers & Remediation Log

| Blocker ID | Date Identified | Description | Impact | Action Required | Owner | Status |
|---|---|---|---|---|---|---|
| — | — | None | — | — | — | CLOSED |

---

## 5. Next Immediate Actions

1. Hand off Milestone 1 artifacts (`lab.env`, infra scripts, safety audit) to `orchestrator_1`.
2. Transition to Milestone 2 (Victim Environment, Tooling & Safety Guardrails).
