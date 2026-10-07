# LAB_LOG — Audit Trail and Decision Journal

**Document Purpose:** Immutable, chronological log of all laboratory events, phase transitions, parameter calibrations, environmental anomalies, and human gate approvals per RFC 2119 standards.  
**Governing Policy:** docs/AGENTS_tcp_flood_lab.md §0 Rule 4 ("Never silently deviate. If you change anything, append an entry to LAB_LOG.md with timestamp, what, why.").  

---

## [2026-10-07T06:20:27Z] — PHASE_TRANSITION: Lab Execution Initialized
- **Phase:** Phase 0 (Preflight)
- **Agent / Actor:** `orchestrator_1` (Lead Orchestrator)
- **Category:** `[PHASE_TRANSITION]`
- **Description:** Laboratory initialized in response to user request. Integrity mode set to `development`. Target AWS region identified as `ap-south-1`.
- **Rationale / Justification:** Commencement of automated research campaign on socket-level lightweight detection of TCP flooding attacks.
- **Evidence Artifacts:** `ORIGINAL_REQUEST.md`, `PROJECT.md`, `updates/000_PROJECT_INITIALIZATION.md`.
- **Impact Analysis:** Establishes master orchestrator tracking and dual-track milestone execution framework.
- **Human Authorization:** Authorized by user prompt.

---

## [2026-10-07T06:40:00Z] — GATE_CONFIRMATION: Human Safety Gate G1 Approved
- **Phase:** Phase 0 (Preflight)
- **Agent / Actor:** Raja (Human Operator) / `orchestrator_1`
- **Category:** `[GATE_CONFIRMATION]`
- **Description:** Human Gate G1 confirmed. Human confirmed awareness and compliance with current AWS policy regarding simulated DoS and security testing on cloud instances.
- **Rationale / Justification:** Strict compliance with `docs/AGENTS_tcp_flood_lab.md` Section 4.3 Human Gate G1 before initiating cloud infrastructure provisioning in Phase 1.
- **Evidence Artifacts:** Recorded in `updates/002_PHASE0_SURVEY_AND_DECOMPOSITION.md` and `STATE.md`.
- **Impact Analysis:** Unblocks Phase 1 AWS EC2 instance and Security Group provisioning in `ap-south-1`.
- **Human Authorization:** Explicit human confirmation logged.

---

## [2026-10-07T06:45:00Z] — PARAMETER_CHANGE: Python Environment Resolution Strategy
- **Phase:** Phase 0 (Preflight)
- **Agent / Actor:** `explorer_survey_1_gen2` / `orchestrator_1`
- **Category:** `[PARAMETER_CHANGE]`
- **Description:** Resolved dual Python environment on operator Mac: System Python 3.14 lacks data science modules, whereas Framework Python 3.13 (`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`) contains `pandas` 3.0.5, `numpy` 2.5.1, `scikit-learn` 1.9.1, and `pyyaml` 6.0.3, but requires `matplotlib`.
- **Rationale / Justification:** Installing `matplotlib` into Framework Python 3.13 via `uv pip install matplotlib --python /Library/Frameworks/Python.framework/Versions/3.13/bin/python3` ensures 100% compliance with Phase 0 Step 3 without polluting system paths.
- **Evidence Artifacts:** `survey_environment.md` Section 3.2.
- **Impact Analysis:** Ensures immediate readiness of local plotting and statistical evaluation suite.
- **Human Authorization:** Pre-approved under standard Phase 0 tooling workflow.

---

## [2026-10-07T06:55:00Z] — PHASE_TRANSITION: Milestone 1 Provisioning Started
- **Phase:** Phase 1 (Infrastructure Provisioning)
- **Agent / Actor:** `worker_m1` (Implementation Worker)
- **Category:** `[PHASE_TRANSITION]`
- **Description:** Local Git repository initialized on branch main, directory layout created, .gitignore and PROJECT.md placed at root, STATE.md initialized.
- **Rationale / Justification:** Executing Milestone 1 in accordance with `plan_m1_infra.md`, `plan_m1_safety.md`, and `spec_m1_contracts.md`.
- **Evidence Artifacts:** `.gitignore`, `STATE.md`, `LAB_LOG.md`, `PROJECT.md`.
- **Impact Analysis:** Commences automated cloud provisioning for `tcp-flood-lab`.
- **Human Authorization:** Dispatched by `orchestrator_1`.
