# BRIEFING — 2026-10-07T07:58:00Z

## Mission
Mine authoritative specifications and extract exact contracts, schemas, CLI signatures, parameter bounds, exit codes, and boundary conditions for Milestone 2.

## 🔒 My Identity
- Archetype: spec_miner
- Roles: Specification Mining Agent for Milestone 2 (Contracts, Schemas & Boundary Conditions)
- Working directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts
- Original parent: c915840f-b40f-4c6b-9b28-92a18579e73d
- Milestone: Milestone 2

## 🔒 Key Constraints
- Read-only: do NOT implement anything or create code/infra files outside agent metadata directory.
- Must read ORIGINAL_REQUEST.md, PROJECT.md, lab.env, docs/AGENTS_tcp_flood_lab.md, DISPATCH.md.
- Output handoff report to .agents/teamwork/spec_miner_m2_contracts/handoff.md following 5-component format and spec miner tables.
- Notify parent orchestrator via send_message upon completion.

## Current Parent
- Conversation ID: c915840f-b40f-4c6b-9b28-92a18579e73d
- Updated: 2026-10-07T07:58:00Z

## Task Summary
- **What to build**: Comprehensive specification report for M2 contracts, schemas, CLI signatures, exit codes, and error logging.
- **Success criteria**: Complete discovery and formal specification of:
  1. M2 -> M3 Interface Contract (Host readiness, Nginx response format, set_profile.sh behavior, attacker iptables rule, attack_guard.sh behaviors).
  2. File schemas for `infra/sysctl_defaults.txt`, `infra/attacker_rules.txt`, `infra/guard_selftest.txt`.
  3. CLI invocation signatures for `tools/set_profile.sh {break|fix|default}`, `tools/attack_guard.sh <tool> <args>`, `tools/guard_selftest.sh`.
  4. Return / exit codes and error logging conventions.
  5. Specification miner tables: Features Discovered (18 items) and Edge Cases (15 items).
- **Interface contracts**: /Users/raja/Documents/syn-edge-flooding/PROJECT.md
- **Code layout**: /Users/raja/Documents/syn-edge-flooding/PROJECT.md

## Key Decisions Made
- Extracted exact parameter boundaries: target IP string-exact match to VICTIM_PRIVATE_IP, duration <= 60s, rate interval >= u100 (<= 10,000 pps), connection count <= 2,000, emergency kill switch /tmp/LAB_STOP absent.
- Standardized exit codes: exit code 0 for success/dry-run pass; non-zero (specifically exit code 1) for all refusal conditions.
- Formalized file schemas for sysctl_defaults.txt, attacker_rules.txt, and guard_selftest.txt.
- Documented error logging format to stderr and /tmp/attack_guard.log.

## Artifact Index
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts/handoff.md — Final specification mining handoff report

## Loaded Skills
- None specified in dispatch prompt.
