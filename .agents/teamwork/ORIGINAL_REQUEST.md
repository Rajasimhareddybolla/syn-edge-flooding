# Original User Request

## 2026-10-07T06:20:27Z

Execute an end-to-end automated research lab investigating socket-level lightweight detection of TCP flooding attacks (SYN floods, connection floods, and flash crowds) on edge Linux instances in AWS, delivering rigorous empirical evaluations, publication-quality figures, and an academic report alongside real-time managerial updates in updates/.

Working directory: /Users/raja/Documents/syn-edge-flooding
Integrity mode: development
Reference specification: docs/AGENTS_tcp_flood_lab.md

## Requirements

### R1. AWS Testbed Provisioning & Safety Enforcement
Provision an isolated 3-node AWS EC2 testbed (victim, attacker, client; t3.micro Ubuntu 24.04 in default VPC) in accordance with the safety guardrails in docs/AGENTS_tcp_flood_lab.md. The security group must allow SSH only from the operator public IP /32 and inter-node traffic only within the lab security group. Attack tools must be bound by a fail-safe attack guard that strictly restricts target IP to victim private IP, duration <= 60 s, and SYN flood rate <= 10,000 pps.

### R2. Instrumentation & Bounded Workload Generators
Deploy a 1 Hz socket-state sampler reading /proc/net/tcp, /proc/net/snmp, and /proc/net/netstat, paired with a 1 Hz HTTP probe from the client. Implement bounded traffic generators (wrk quiet load, ab flash crowd, hping3 SYN flood, and async connection hold) calibrated against the victim's observed capacity.

### R3. Empirical Experiment Matrix Execution
Serially execute the full experimental matrix across scenarios S0 (baseline), S1 (flash crowds), S2 (SYN floods), S3 (connection floods), S4 (flood during crowd), and S5 (SYN-cookie mitigation), storing raw timestamped artifacts per run.

### R4. Detection Benchmark & Analysis
Implement and evaluate the baseline volume detector (B1), the proposed adaptive dual-signal detector (D1: EWMA half-open volume + handshake completion ratio), and extended detector (D2: connection flood & mitigation branches). Parameters must be tuned strictly on reps 1–3 and evaluated on held-out reps 4–5. Measure CPU/RAM overhead against standard inspection. Produce figures F1–F8 and tables T1–T5.

### R5. Scientific Reporting, Teardown & Managerial Communication
Compile the complete research paper report in report/report.md filling all template brackets from empirical data and discussing threats to validity. Fully terminate all AWS resources and verify zero active lab resources. Throughout execution, maintain a managerial communication log in updates/ with structured managerial updates on phase transitions, blockers, and resolutions.

## Acceptance Criteria

### Infrastructure & Safety
- [ ] AWS Security Group contains no 0.0.0.0/0 ingress rules; SSH allowed only from current operator /32.
- [ ] attack_guard.sh passes automated self-tests refusing unauthorized IPs, durations > 60 s, and rates > 10,000 pps.
- [ ] lab.env generated with private IPs; inter-node reachability verified via ICMP ping.

### Pipeline Instrumentation & Calibration
- [ ] Sampler produces exactly 1 row/second over a 120-second test window with median sample cost < 5 ms and no missing deltas.
- [ ] Capacity calibration determines CAPACITY_RPS with probe success >= 99% and p95 latency < 200 ms, establishing crowd levels in infra/crowd_levels.json.

### Experimentation & Data Integrity
- [ ] Every scenario run directory in runs/<run_id>/ contains events.json, victim_metrics.csv, probe.csv, load_client.txt, and sysctl_snapshot.txt.
- [ ] Runs are recorded in runs/INDEX.csv with zero undocumented omissions.
- [ ] Parameter tuning is performed strictly on runs 1–3; reported metrics use exclusively held-out runs 4–5.

### Analysis & Reporting
- [ ] Figures F1–F8 generated at 300 DPI and tables T1–T5 populated directly from analysis/metrics.csv and analysis/overhead.csv.
- [ ] report/report.md completed with abstract, empirical metrics, and explicit threats to validity.

### Teardown & Communications
- [ ] All 3 EC2 instances terminated, security group removed, and key pair deleted with verification captured in infra/teardown_verification.txt.
- [ ] Timely, structured managerial updates created in updates/ detailing progress, blockers, and solutions.

