# Task Assignment: spec_miner_m2_contracts

You are `spec_miner_m2_contracts` (teamwork_preview_spec_miner).
Target: Milestone 2 — Specification Mining for Contracts, Schemas, and Acceptance Thresholds.
Project Root: /Users/raja/Documents/syn-edge-flooding
Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts
Parent Orchestrator: orchestrator_1_gen2 (c915840f-b40f-4c6b-9b28-92a18579e73d)

Scope:
- Mine authoritative specification from `docs/AGENTS_tcp_flood_lab.md` (§4, §5, §12) and `ORIGINAL_REQUEST.md`.
- Extract exact requirements, contracts, parameter ranges, return codes, file schemas for:
  1. `infra/sysctl_defaults.txt`
  2. `infra/attacker_rules.txt`
  3. `tools/set_profile.sh`
  4. `tools/attack_guard.sh`
  5. `tools/guard_selftest.sh` and `infra/guard_selftest.txt`
- Detail exact edge cases and error handling requirements.

Produce your structured report in:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts/handoff.md


## 2026-10-07T07:31:36Z
You are spec_miner_m2_contracts, a specification mining agent for Milestone 2 (Contracts, Schemas & Boundary Conditions).

Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts
Project Root: /Users/raja/Documents/syn-edge-flooding

MANDATORY FIRST STEP: Read the original user request from:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Read project context:
- /Users/raja/Documents/syn-edge-flooding/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/lab.env
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md (§4.1, §4.2, §4.3, §4.4, §5.1, §5.2, Phase 2, Phase 4)
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts/DISPATCH.md

Your Scope:
1. Mine authoritative requirements and extract exact contracts, parameter values, exit codes, and output formats for:
   - M2 -> M3 Interface Contract: Host readiness, Nginx response format, set_profile.sh behavior and output, attacker iptables rule, attack_guard.sh input/output and refusal behaviors.
   - File schemas: `infra/sysctl_defaults.txt`, `infra/attacker_rules.txt`, `infra/guard_selftest.txt`.
   - Exact CLI invocation signatures: `tools/set_profile.sh {break|fix|default}`, `tools/attack_guard.sh <tool> <args>`, `tools/guard_selftest.sh`.
   - Return codes: what does attack_guard.sh return when refusing? (e.g., non-zero, specific exit code 1 or 2).
   - Error logging: how failures are recorded.
2. Document edge cases, command parsing nuances (e.g. argument order, quotes, option flags in hping3 vs conn_hold.py), and failure modes.
3. Write your report to:
   /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts/handoff.md
   following the Handoff Protocol.
Notify orchestrator when complete via send_message.
