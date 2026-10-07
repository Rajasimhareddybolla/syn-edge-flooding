# Update 002 — Phase 0 Survey & Architecture Decomposition

- **Date / Time:** 2026-10-07 11:55 IST
- **Status:** Phase 0 (Survey & Decomposition) Active
- **Manager:** Autonomous Lead Coordinator
- **Active Agents:** 
  - Sentinel Supervisor
  - Project Orchestrator (`orchestrator_1`)
  - Spec Miner (`spec_miner_survey_1`)
  - AWS Environment Explorer (`explorer_survey_1`)
  - Methodology Explorer (`explorer_survey_2`)

---

## 1. Operational Overview
The Project Orchestrator has initiated Phase 0 (Survey & Scoping) by dispatching three concurrent survey specialists to verify all requirements, environment constraints, and testbed interfaces before writing deployment scripts:

1. **Specification Miner (`spec_miner_survey_1`):**
   - Extracting explicit RFC-2119 requirements (**MUST**, **MUST NOT**, **SHOULD**) from `docs/AGENTS_tcp_flood_lab.md`.
   - Building the complete Feature Inventory and linking them to acceptance criteria.

2. **AWS Environment Explorer (`explorer_survey_1`):**
   - Probing the active AWS environment (`ap-south-1`).
   - Verifying default VPC availability, subnet placement, Ubuntu 24.04 LTS AMI parameters, and security group isolation constraints.

3. **Methodology Explorer (`explorer_survey_2`):**
   - Reviewing the experimental calibration protocol, the 65-run scenario matrix (S0–S5), and 1 Hz `/proc/net/tcp` sampling metrics.
   - Verifying the train/test split protocol (reps 1–3 for tuning, reps 4–5 for held-out evaluation).

---

## 2. Blockers & Risks
- **Blockers:** None.
- **Risks & Mitigation:**
  - *Risk:* Rate limits or AWS AMI discrepancies. *Mitigation:* `explorer_survey_1` queries SSM Parameter Store dynamically for official Ubuntu 24.04 AMIs in `ap-south-1`.

---

## 3. Next Milestone
Once all three survey specialists return their findings, `orchestrator_1` will synthesize the Feature Inventory into `PROJECT.md`, establish interface contracts, and trigger Phase 1 AWS infrastructure provisioning (`A1 Infra`).

