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


## [2026-10-07T07:06:18Z] — PARAMETER_CHANGE: Operator IP Shift
- **Phase:** Active Phase
- **Agent / Actor:** update_sg_ip.sh
- **Category:** [PARAMETER_CHANGE]
- **Description:** Security group sg-09e89875382c47277 SSH rule updated to 152.57.107.6/32.
- **Rationale / Justification:** Maintain operator reachability.


## [2026-10-07T07:09:11Z] — RESOURCE_ALLOCATION: AWS Infrastructure Provisioned
- **Phase:** Phase 1 (Infrastructure Provisioning)
- **Agent / Actor:** worker_m1
- **Category:** [RESOURCE_ALLOCATION]
- **Description:** Provisioned Security Group sg-09e89875382c47277 (/32 SSH only), Key Pair tcp-flood-lab, and 3 t3.micro instances (victim=i-0f89c07ce382931f2, attacker=i-03e8f67a9cb58c94a, client=i-07f191b24634a44ca) in subnet-0709c5a163cc423bb with CpuCredits=standard.
- **Rationale / Justification:** Establishing physical multi-node isolated research testbed for Milestone 1.
- **Evidence Artifacts:** infra/sg_described.json, infra/instances_described.json, lab.env, infra/ping_verification.txt.
- **Impact Analysis:** Testbed is fully operational and safely locked down.
- **Human Authorization:** Covered under Gate G1 approval.

## [2026-10-07T07:52:19Z] — PARAMETER_CHANGE: Operator IP Shift
- **Phase:** Active Phase
- **Agent / Actor:** update_sg_ip.sh
- **Category:** [PARAMETER_CHANGE]
- **Description:** Security group sg-09e89875382c47277 SSH rule updated to 152.57.5.80/32.
- **Rationale / Justification:** Maintain operator reachability.


## [2026-10-07T07:52:24Z] — PARAMETER_CHANGE: Operator IP Shift
- **Phase:** Active Phase
- **Agent / Actor:** update_sg_ip.sh
- **Category:** [PARAMETER_CHANGE]
- **Description:** Security group sg-09e89875382c47277 SSH rule updated to 152.57.5.80/32.
- **Rationale / Justification:** Maintain operator reachability.


## [2026-10-07T07:54:30Z] — PARAMETER_CHANGE: Operator CGNAT Egress Shift
- **Phase:** Milestone 2 (Victim Environment & Tooling Exploration)
- **Agent / Actor:** `explorer_m2_env`
- **Category:** `[PARAMETER_CHANGE]`
- **Description:** Authorized operator public egress IPv4 `152.57.24.183/32` in security group `sg-09e89875382c47277` for port 22 SSH ingress.
- **Rationale / Justification:** ISP CGNAT rotated outbound IP from 152.57.129.48 to 152.57.24.183. Maintained strict RFC 2119 /32 restriction with zero 0.0.0.0/0 exposure.
- **Impact Analysis:** Restores seamless SSH access to all lab nodes.
- **Human Authorization:** Permitted under `docs/AGENTS_tcp_flood_lab.md` §234 and §4.1.


## [2026-10-07T08:03:09Z] — PARAMETER_CHANGE: Operator IP Shift
- **Phase:** Active Phase
- **Agent / Actor:** update_sg_ip.sh
- **Category:** [PARAMETER_CHANGE]
- **Description:** Security group sg-09e89875382c47277 SSH rule updated to 152.57.5.80/32.
- **Rationale / Justification:** Maintain operator reachability.

## [2026-10-07T09:00:00Z] — INSTRUMENTATION_VALIDATION: Sampler and probe checks
- **Phase:** Phase 3 (Telemetry Instrumentation)
- **Description:** Victim sampler idle validation recorded 125 rows with 985–1015 ms spacing, 0.64 ms median collection cost, and a five-connection established-socket peak during a benign keep-alive check. Evidence: `infra/sampler_idle_validation.csv`.
- **Deviation and correction:** Capacity calibration was discarded because the client probe exited after one row: first due to an unavailable `bc` dependency, then because a no-newline curl metrics string caused `read` to return non-zero under `set -e`. `tools/probe.sh` now uses awk for its fractional sleep and appends a newline before parsing. A five-second smoke test produced five rows. No attack traffic was generated.
- **Next action:** Repeat legitimate-only capacity calibration, then obtain G2 confirmation before any attack scenario.

## [2026-10-07T09:15:00Z] — GATE_CONFIRMATION: Human Safety Gate G2 Approved
- **Phase:** Phase 4 / Phase 5 entry
- **Actor:** Raja (Human Operator)
- **Description:** Human explicitly confirmed safe continuation after review of the 16/16 passing attack-guard self-test.
- **Scope retained:** Target remains the exact victim private IP only; duration is capped at 60 seconds, SYN rate at 10,000 packets/s, connection holds at 2,000, and `/tmp/LAB_STOP` remains an emergency kill switch. No cap escalation is authorized.

## [2026-10-07T09:20:00Z] — PILOT: Guarded SYN path validation
- **Phase:** Phase 4
- **Description:** Two 10-second pilot attempts generated no packets because hping3 lacked raw-socket privilege. They are retained under `runs/pilot-guarded-s2m*`; metrics show zero half-open sockets and all probes successful.
- **Correction:** `attack_guard.sh` now permits only a bare `sudo` prefix for a validated supported tool, rejects sudo options, validates the normalized command, and executes the original constrained command. The live guard self-test was rerun successfully (16/16). A one-second private-VPC smoke test then produced SYN-ACK responses from the exact victim private IP. No cap was changed.

## [2026-10-07T11:31:41Z] — PARAMETER_CHANGE: Operator IP Shift
- **Phase:** Active Phase
- **Agent / Actor:** update_sg_ip.sh
- **Category:** [PARAMETER_CHANGE]
- **Description:** Security group sg-09e89875382c47277 SSH rule updated to 152.57.4.19/32.
- **Rationale / Justification:** Maintain operator reachability.


## [2026-10-07T11:54:46Z] — PARAMETER_CHANGE: Operator IP Shift
- **Phase:** Active Phase
- **Agent / Actor:** update_sg_ip.sh
- **Category:** [PARAMETER_CHANGE]
- **Description:** Security group sg-09e89875382c47277 SSH rule updated to 152.57.4.19/32.
- **Rationale / Justification:** Maintain operator reachability.


## [2026-10-07T11:56:01Z] — PARAMETER_CHANGE: Operator IP Shift
- **Phase:** Active Phase
- **Agent / Actor:** update_sg_ip.sh
- **Category:** [PARAMETER_CHANGE]
- **Description:** Security group sg-09e89875382c47277 SSH rule updated to 152.57.4.19/32.
- **Rationale / Justification:** Maintain operator reachability.

