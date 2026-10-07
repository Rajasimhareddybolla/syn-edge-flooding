# DISPATCH — explorer_m1_infra

## Objective
Analyze and formulate the exact AWS CLI provisioning commands and implementation strategy for Milestone 1 (Preflight & AWS Infrastructure Provisioning).
Target scope:
1. Git repository init, .gitignore, directory structure (`infra/`, `tools/`, `detector/`, `runs/`, `analysis/`, `report/`, `updates/`), `STATE.md`, `LAB_LOG.md`.
2. Python environment (`uv pip install matplotlib`).
3. AWS Security Group `lab-sg` in default VPC `vpc-091281d6eb74da886` with ingress from `152.57.107.6/32:22` and self-referential SG ingress only.
4. EC2 key pair `tcp-flood-lab` saved to `~/.ssh/tcp-flood-lab.pem` with `chmod 400`.
5. EC2 run-instances command for 3 `t3.micro` nodes (`victim`, `attacker`, `client`) in `subnet-0709c5a163cc423bb` (`ap-south-1a`) with AMI `ami-065d2b03fb493085a`, `--credit-specification CpuCredits=standard`, and `Project=tcp-flood-lab` tags.
6. Instance IP queries, generation of `lab.env`, and inter-node private ICMP ping verification.

Produce recommendation in `plan_m1_infra.md` and handoff report.


## 2026-10-07T06:42:34Z
You are explorer_m1_infra operating in working directory /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_infra.
Parent Orchestrator: orchestrator_1 (conversationId: f6cfd525-c586-41eb-8148-3a42cc6823d8).

You MUST read the original request before starting work:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Also read:
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/orchestrator_1/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_infra/DISPATCH.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_1_gen2/survey_environment.md

Your mission:
Formulate the exact, foolproof AWS CLI and local implementation strategy for Milestone 1 (Preflight & AWS Infrastructure Provisioning).
Detail the commands for git initialization, directories, python matplotlib installation, SG creation (/32 only), key pair creation, EC2 instance launch (victim, attacker, client in ap-south-1a), lab.env generation, and private IP ICMP verification.

Write your report to:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_infra/plan_m1_infra.md
Write handoff.md in your working directory and notify orchestrator_1 with send_message.
