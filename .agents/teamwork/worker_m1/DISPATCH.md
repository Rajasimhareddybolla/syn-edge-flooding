# DISPATCH — worker_m1

## Objective
Execute and implement Milestone 1: Preflight & AWS Infrastructure Provisioning.
Follow the implementation plans and contracts authored by the explorers:
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_infra/plan_m1_infra.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety/plan_m1_safety.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m1_contracts/spec_m1_contracts.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/orchestrator_1/PROJECT.md

## Scope & File Ownership
You exclusively own and will create:
- `.gitignore`, `STATE.md`, `LAB_LOG.md`, `PROJECT.md` (at project root)
- `lab.env` (at project root with 15 variables)
- `infra/provision_m1.sh`, `infra/verify_m1_safety.sh`, `infra/update_sg_ip.sh`
- `infra/sg_describe.json`, `infra/instances_describe.json`, `infra/ping_verification.txt`
- `updates/001_M1_INFRASTRUCTURE_PROVISIONED.md`
- Directory structure scaffolding: `infra/`, `tools/`, `detector/`, `runs/`, `analysis/`, `report/`, `updates/`

## Verification Requirements
Run `infra/verify_m1_safety.sh` and capture output. Verify:
1. No 0.0.0.0/0 ingress in `lab-sg`; SSH restricted to operator /32.
2. 3 EC2 instances running with `Project=tcp-flood-lab` and standard CPU credits.
3. SSH access functional with `~/.ssh/tcp-flood-lab.pem` (`chmod 400`).
4. Inter-node ICMP ping succeeds between victim, attacker, and client.
5. `lab.env` contains all 15 variables and passes syntax validation.

Record all results in your `handoff.md`.

