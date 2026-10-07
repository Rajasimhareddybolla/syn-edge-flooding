# Task Assignment: test_writer_e2e

You are `test_writer_e2e` (teamwork_preview_test_writer).
Target: E2E Testing Track — Comprehensive 4-Tier Opaque-Box Test Harness.
Project Root: /Users/raja/Documents/syn-edge-flooding
Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/test_writer_e2e
Parent Orchestrator: orchestrator_1_gen2 (c915840f-b40f-4c6b-9b28-92a18579e73d)

Scope:
- Requirement-driven, opaque-box test suite independent of implementation design.
- Derive test cases directly from `ORIGINAL_REQUEST.md` and `PROJECT.md § Feature Inventory`.
- Create `TEST_INFRA.md` outlining testing methodology, tier breakdown, coverage thresholds.
- Implement tests in `tests/`:
  - `tests/test_tier1_features.py`: Feature coverage (≥5 tests per feature).
  - `tests/test_tier2_boundaries.py`: Boundary and corner cases (≥5 tests per feature: IP boundaries, duration limits, rate bounds, conns limits, kill switch).
  - `tests/test_tier3_combinations.py`: Pairwise cross-feature interactions.
  - `tests/test_tier4_scenarios.py`: Real-world end-to-end workload and scenario checks.
  - `tests/run_all_tests.sh`: Consolidated runner.
- Create `TEST_READY.md` summarizing test counts across Tiers 1–4 and runner command.

Produce your structured handoff report in:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/test_writer_e2e/handoff.md
## 2026-10-07T07:31:36Z
You are test_writer_e2e, a test engineer for the parallel E2E Testing Track.

Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/test_writer_e2e
Project Root: /Users/raja/Documents/syn-edge-flooding

MANDATORY FIRST STEP: Read the original user request from:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Read project context:
- /Users/raja/Documents/syn-edge-flooding/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/lab.env
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/test_writer_e2e/DISPATCH.md

Your Scope:
1. Create `TEST_INFRA.md` at project root outlining:
   - Opaque-box, requirement-driven test philosophy
   - 4-Tier test architecture:
     Tier 1: Feature coverage (>=5 tests per feature)
     Tier 2: Boundary & corner cases (>=5 tests per feature)
     Tier 3: Pairwise combinations
     Tier 4: Real-world application scenarios
   - Coverage thresholds and execution instructions
2. Implement python test suites in `tests/`:
   - `tests/test_tier1_features.py`: test M1/M2/M3 interface contracts, environment variables, security group lockdown rules, key permissions, attack guard requirements, sysctl profiles.
   - `tests/test_tier2_boundaries.py`: boundary testing for attack guard (IP validation, duration 60s vs 61s, rate u100 vs u99, conns 2000 vs 2001, kill switch trigger), sysctl values, ulimit boundaries.
   - `tests/test_tier3_combinations.py`: combinatorial/pairwise test cases combining profile state with attack guard execution, network state, etc.
   - `tests/test_tier4_scenarios.py`: end-to-end scenario validation harnesses.
3. Create/update `tests/run_all_tests.sh` to execute the full test suite with clean pass/fail reporting and exit code 0 on success.
4. Create `TEST_READY.md` at project root summarizing the test inventory, tier counts, and test execution command.
5. Write your handoff report to:
   /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/test_writer_e2e/handoff.md
Notify orchestrator when complete via send_message.
