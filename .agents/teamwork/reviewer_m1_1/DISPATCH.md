# DISPATCH — reviewer_m1_1

## Objective
Review Milestone 1 AWS cloud infrastructure correctness, security group rules, and instance configurations.
Inspect:
- Security Group `lab-sg` (`sg-09e89875382c47277`): Confirm zero `0.0.0.0/0` or `::/0` ingress rules; confirm SSH port 22 is allowed ONLY from `152.57.107.6/32`; confirm self-referential intra-SG rule allows traffic only within `lab-sg`.
- EC2 instances (`victim`, `attacker`, `client`): Confirm all 3 are running in `ap-south-1a`, have `Project=tcp-flood-lab` tag, and use `--credit-specification CpuCredits=standard`.
- Run AWS CLI verification commands and evaluate pass/fail.

Deliver verdict: APPROVE or REQUEST_CHANGES in handoff.md.

## 2026-10-07T07:15:08Z
You are reviewer_m1_1 operating in working directory /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/reviewer_m1_1.
Parent Orchestrator: orchestrator_1 (conversationId: f6cfd525-c586-41eb-8148-3a42cc6823d8).

You MUST read the original request before starting work:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Also read:
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/orchestrator_1/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/worker_m1/handoff.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/reviewer_m1_1/DISPATCH.md

Your mission:
Review Milestone 1 AWS cloud infrastructure correctness and security group rules.
Verify:
1. Security Group `lab-sg`: No 0.0.0.0/0 ingress. SSH allowed strictly from operator /32. Intra-SG mesh intact.
2. 3 EC2 instances running with `Project=tcp-flood-lab` tags and standard CPU credits in `ap-south-1a`.
3. Run AWS CLI commands to verify.

Deliver verdict: APPROVE or REQUEST_CHANGES in handoff.md and notify orchestrator_1 with send_message.
