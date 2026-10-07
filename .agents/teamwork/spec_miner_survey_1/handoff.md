# Handoff Report — spec_miner_survey_1

## 1. Observation
- Read and analyzed the following authoritative project specifications:
  - `ORIGINAL_REQUEST.md` (lines 1–52): Requirements R1–R5, acceptance criteria across 5 categories (Infrastructure & Safety, Pipeline Instrumentation & Calibration, Experimentation & Data Integrity, Analysis & Reporting, Teardown & Communications).
    - Quoted verbatim R1: "Provision an isolated 3-node AWS EC2 testbed (victim, attacker, client; t3.micro Ubuntu 24.04 in default VPC) in accordance with the safety guardrails in docs/AGENTS_tcp_flood_lab.md. The security group must allow SSH only from the operator public IP /32 and inter-node traffic only within the lab security group. Attack tools must be bound by a fail-safe attack guard that strictly restricts target IP to victim private IP, duration <= 60 s, and SYN flood rate <= 10,000 pps."
    - Quoted verbatim R4: "Implement and evaluate the baseline volume detector (B1), the proposed adaptive dual-signal detector (D1: EWMA half-open volume + handshake completion ratio), and extended detector (D2: connection flood & mitigation branches). Parameters must be tuned strictly on reps 1–3 and evaluated on held-out reps 4–5. Measure CPU/RAM overhead against standard inspection. Produce figures F1–F8 and tables T1–T5."
  - `docs/AGENTS_tcp_flood_lab.md` (lines 1–425):
    - §4.1–4.5: Non-negotiable safety guardrails: IP confinement to `VICTIM_PRIVATE_IP`, SG ingress without `0.0.0.0/0`, duration $\le 60\text{ s}$, SYN rate $\le 10,000\text{ pps}$ (`-i u100`), connection hold $\le 2000$, kill switch `/tmp/LAB_STOP`, human gates G1, G2, G3.
    - §5.1–5.6: Mandatory schemas for `lab.env`, `events.json`, `victim_metrics.csv` (24 columns, 1 Hz monotonic pacing), `probe.csv`, and run directory artifact list (10 files per run).
    - §6: 10 execution phases (Phases 0–10).
    - §6 Phase 4: `CAPACITY_RPS` calibration with $\ge 99\%$ probe success and p95 latency $< 200\text{ ms}$, yielding crowd levels in `infra/crowd_levels.json`.
    - §6 Phase 5: Scenario matrix across S0, S1S/M/L, S2L/M/H, S3L/M/H, S4, S5M/H (13 scenarios $\times$ 5 repetitions = 65 runs).
    - §6 Phase 6: Mathematical formulations for B1, D1 (EWMA baseline $\mu_t = \alpha x_t + (1-\alpha)\mu_{t-1}$ with freeze and hysteresis), D2 (connection flood branch and cookie/queue branch), D3 (scikit-learn ML benchmark), parameter tuning grid ($\alpha, K, \tau, N, \text{FLOOR}, M$).
    - §6 Phase 8: Overhead benchmark O0–O4 via `pidstat` on `t3.micro`.
    - §6 Phase 9–10: Deliverables F1–F8 (300 DPI), T1–T5, `report/report.md` with filled abstract and explicit threats to validity, teardown verification in `infra/teardown_verification.txt`.
  - `docs/design.md` (lines 1–20): Draft abstract and structural paper outline.
  - `updates/000_PROJECT_INITIALIZATION.md` & `updates/001_DISPATCH_AND_SENTINEL.md`: Project initialization tracking, active Sentinel supervisor, and Orchestrator dispatching.
- Produced detailed inventory document:
  - `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_survey_1/survey_spec.md` (lines 1–385, 45 discovered features, 18 edge cases, complete schemas, formulas, and traceability matrix).

## 2. Logic Chain
1. From `ORIGINAL_REQUEST.md` and `docs/AGENTS_tcp_flood_lab.md`, the authoritative specification demands an end-to-end automated research workflow operating under strict safety, experimental, algorithmic, and deliverable standards.
2. The safety rules (Section 4 of `AGENTS.md`) take absolute precedence over all other operational instructions. Any attack command that targets an unauthorized IP, exceeds 60 s, exceeds 10,000 pps, opens $>2,000$ conns, or encounters `/tmp/LAB_STOP` must fail closed via `attack_guard.sh`.
3. The experimental matrix consists of exactly 13 distinct scenario configurations (S0, S1S, S1M, S1L, S2L, S2M, S2H, S3L, S3M, S3H, S4, S5M, S5H). At 5 repetitions each, exactly 65 serial runs must be executed with 10 mandatory artifacts collected per run in `runs/<run_id>/`.
4. The detector algorithms require exact mathematical formulation:
   - Feature definitions: half-open count ($x_t$), completion ratio ($C_t$ over window $W=3\text{ s}$), established growth ($G_t$), queue pressure ($Q_t$), cookie rate ($K_t$), and top source concentration ($S_t$).
   - D1 requires EWMA baseline calculation with a mandatory freeze on updates while in alarm, and an $M=5$ second hysteresis cooldown.
   - Parameter optimization requires strict separation between training/tuning runs (reps 1–3) and evaluation/reporting runs (reps 4–5).
5. Deliverables are explicitly bounded: 8 publication figures (F1–F8, 300 DPI), 5 empirical tables (T1–T5), research paper report (`report/report.md`) with all bracketed numbers backed by empirical run data and mandatory threats to validity, AWS teardown verified in `infra/teardown_verification.txt`, and managerial communication updates in `updates/`.
6. Compiling all requirements, schemas, formulas, edge cases, and deliverables into `survey_spec.md` provides an exhaustive, unambiguous contract enabling orchestrator milestone planning and verification test authoring.

## 3. Caveats
- AWS simulated DoS and security testing policy compliance (Gate G1) requires operator confirmation.
- Cloud vendor behavior: AWS VPC infrastructure drops spoofed source packets (`--rand-source`), so attack traffic originates from the attacker's actual IP. This is an explicit threat to validity documented in T5.
- The optional Suricata benchmark (O4) and optional machine learning benchmark (D3) depend on time and environment feasibility, whereas B1, D1, D2, and O0–O3 are mandatory.

## 4. Conclusion
The specification mining survey is complete. The exhaustive specification inventory has been formalized in `survey_spec.md`. It covers 45 categorized features, 18 edge cases, complete schemas for `lab.env`, `events.json`, `victim_metrics.csv`, and `probe.csv`, exact mathematical specifications for detectors B1, D1, and D2, the train/test protocol, overhead measurement, and all deliverables F1–F8, T1–T5, `report.md`, and teardown verification.

## 5. Verification Method
To independently verify this specification inventory:
1. **Inspect Artifact Existence and Integrity:**
   - Verify `survey_spec.md` exists and contains all required sections:
     ```bash
     test -f /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_survey_1/survey_spec.md
     grep -E "(Features Discovered|Edge Cases|Mathematical Formulations|Scenario Matrix)" /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_survey_1/survey_spec.md
     ```
2. **Verify Feature Count & Coverage:**
   - Confirm all 45 discovered features and 18 edge cases are present:
     ```bash
     grep -c "^| [0-9]" /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_survey_1/survey_spec.md
     ```
3. **Trace Acceptance Criteria:**
   - Check the Traceability Matrix in Section 13 of `survey_spec.md` against `ORIGINAL_REQUEST.md` acceptance criteria items.
4. **Invalidation Conditions:**
   - Any omission of scenarios S0–S5, detector formulas B1/D1/D2, safety guard constraints, or deliverables F1–F8/T1–T5 invalidates this survey.

