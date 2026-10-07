# DISPATCH — explorer_m1_safety

## Objective
Analyze safety guardrails, credential isolation, and verification checks for Milestone 1.
Ensure:
1. SG contains NO `0.0.0.0/0` or `::/0` rules; SSH is strictly bound to operator `/32`.
2. Private keys (`~/.ssh/tcp-flood-lab.pem`) have `400` permissions and are excluded in `.gitignore`.
3. Instance launch parameters strictly use `--credit-specification CpuCredits=standard` to prevent unexpected charges.
4. All resources tagged `Project=tcp-flood-lab`.
5. Pre-launch and post-launch verification commands (AWS CLI describe commands, ICMP connectivity tests, SSH connectivity without host key prompting).

Produce recommendation in `plan_m1_safety.md` and handoff report.


## 2026-10-07T06:42:34Z
You are explorer_m1_safety operating in working directory /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety.
Parent Orchestrator: orchestrator_1 (conversationId: f6cfd525-c586-41eb-8148-3a42cc6823d8).

You MUST read the original request before starting work:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Also read:
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/orchestrator_1/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety/DISPATCH.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_survey_1/survey_spec.md

Your mission:
Formulate the safety, credential isolation, and verification strategy for Milestone 1.
Define exact verification checks:
1. Ensure SG has NO 0.0.0.0/0 ingress and only allows operator /32 on port 22.
2. Ensure SSH private key is chmod 400 and gitignored.
3. Ensure standard CPU credits and Project tags on all instances.
4. Define pre- and post-provisioning verification commands.

Write your report to:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m1_safety/plan_m1_safety.md
Write handoff.md in your working directory and notify orchestrator_1 with send_message.
