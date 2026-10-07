# BRIEFING — 2026-10-07T08:00:00Z

## Mission
Analyze, formulate, and produce complete design, implementation specifications, and empirical validation for Milestone 2: Attacker RST suppression (`infra/attacker_rules.txt`), fail-safe attack guard wrapper (`tools/attack_guard.sh`), automated guard self-test (`tools/guard_selftest.sh`), and Human Safety Gate G2 evidence artifact (`infra/guard_selftest.txt`).

## 🔒 My Identity
- Archetype: explorer
- Roles: investigator, synthesis
- Working directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard
- Original parent: c915840f-b40f-4c6b-9b28-92a18579e73d
- Milestone: Milestone 2 (Attack Guard Implementation, Attacker RST Suppression, and Guard Self-Test)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly in project directories (`tools/`, `infra/`), produce structured analysis and proposed code in handoff report and agent workspace.
- Attacker RST suppression iptables rule must be scoped strictly to victim private IP: `sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP`.
- Attack guard wrapper `tools/attack_guard.sh` must refuse unless ALL hold:
  1. target IP == VICTIM_PRIVATE_IP from lab.env (string-exact)
  2. duration <= 60 s (enforced with timeout)
  3. SYN rate <= 10,000 pps (hping3 interval >= u100; strictly reject --flood and --faster)
  4. connection-hold count <= 2,000
  5. kill switch file /tmp/LAB_STOP is absent
- Guard self-test script `tools/guard_selftest.sh` must test and prove refusal for all safety violations (unauthorized IP, duration > 60s, interval < u100, --flood/--faster, connection count > 2000, /tmp/LAB_STOP present) and prove successful invocation for valid parameters, saving to `infra/guard_selftest.txt`.
- Deliver output via `handoff.md` and notify orchestrator via `send_message`.

## Current Parent
- Conversation ID: c915840f-b40f-4c6b-9b28-92a18579e73d
- Updated: 2026-10-07T08:00:00Z

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md`, `PROJECT.md`, `lab.env`, `docs/AGENTS_tcp_flood_lab.md` (§4.1, §4.2, §4.3, §4.4, Phase 2, Phase 4)
  - `tests/test_tier1_features.py`, `tests/test_tier2_boundaries.py`, `tests/test_tier3_combinations.py`
  - Peer agent workspaces (`spec_miner_m2_contracts`, `explorer_m2_env`, `test_writer_e2e`)
- **Key findings**:
  - Outbound TCP RST suppression on attacker kernel is mandatory to prevent automatic kernel teardown of half-open TCP connections upon receiving SYN-ACKs during raw hping3 packet generation.
  - Fail-safe wrapper `tools/attack_guard.sh` requires robust CLI parsing across multiple invocation signatures (`hping3`, `timeout <D> hping3`, `python3 conn_hold.py`, `--duration <D>`).
  - Emergency kill switch `/tmp/LAB_STOP` is enforced both before launch and in real-time via a background loop watchdog while the attack process runs.
  - Self-test suite `tools/guard_selftest.sh` successfully executed and verified 16/16 test cases covering all 6 invariant refusal categories and positive authorization boundaries.
  - Human Safety Gate G2 artifact structure verified and certified ready for human sign-off.
- **Unexplored areas**: Milestone 3 telemetry calibration, Milestone 4 empirical matrix execution (downstream milestones).

## Key Decisions Made
- Formulated `proposed_attacker_rules.txt` with rule specification, active deployment rule (`172.31.37.214`), check command, and teardown removal command.
- Formulated `proposed_attack_guard.sh` with fail-closed semantics, timeout enforcement, rate clamping, connection clamping, and active kill-switch watchdog.
- Formulated `proposed_guard_selftest.sh` with 16 automated tests producing `infra/guard_selftest.txt`.
- Executed self-test locally on Darwin arm64 with 100% pass rate. Verified compatibility with `test_tier2_boundaries.py`.

## Artifact Index
- `DISPATCH.md` — Task assignment and instructions
- `progress.md` — Liveness heartbeat and activity tracking
- `BRIEFING.md` — Working memory and identity index
- `proposed_attacker_rules.txt` — Proposed attacker RST suppression rule file
- `proposed_attack_guard.sh` — Proposed fail-safe attack guard wrapper
- `proposed_guard_selftest.sh` — Proposed automated guard self-test script
- `handoff.md` — Comprehensive 5-component handoff report for worker_m2 and orchestrator
