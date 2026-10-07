# BRIEFING — 2026-10-07T08:02:00Z

## Mission
Implement Milestone 2: Provision victim, attacker, client environments, configure Nginx with backlog 128, record sysctl defaults, implement tools/set_profile.sh, tools/attack_guard.sh, tools/guard_selftest.sh, deploy attacker RST suppression, execute self-tests into infra/guard_selftest.txt, and validate all tests.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/worker_m2
- Original parent: c915840f-b40f-4c6b-9b28-92a18579e73d
- Milestone: Milestone 2 (Victim Environment, Tooling & Safety Guardrails)

## 🔒 Key Constraints
- Exclusive write ownership:
  - infra/sysctl_defaults.txt
  - infra/attacker_rules.txt
  - infra/guard_selftest.txt
  - tools/set_profile.sh
  - tools/attack_guard.sh
  - tools/guard_selftest.sh
  - Remote guest configurations on EC2 instances (victim, attacker, client).
- DO NOT CHEAT: genuine implementations only, no hardcoded values or fake test outputs.
- All 5 attack guard invariants fail-closed.
- Human Safety Gate G2 requires real output in infra/guard_selftest.txt.

## Current Parent
- Conversation ID: c915840f-b40f-4c6b-9b28-92a18579e73d
- Updated: not yet

## Task Summary
- **What to build**: Remote guest provisioning, Nginx backlog 128, sysctl snapshots, profile switcher script, iptables RST suppression, attack guard wrapper, guard selftest suite, and verification output.
- **Success criteria**: All 109 tests in tests/run_all_tests.sh pass cleanly.
- **Interface contracts**: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts/handoff.md
- **Code layout**: /Users/raja/Documents/syn-edge-flooding/PROJECT.md

## Key Decisions Made
- [TBD]

## Artifact Index
- [TBD]

## Change Tracker
- **Files modified**: none yet
- **Build status**: pending
- **Pending issues**: none

## Quality Status
- **Build/test result**: pending
- **Lint status**: pending
- **Tests added/modified**: pending

## Loaded Skills
- None
