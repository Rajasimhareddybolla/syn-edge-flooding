# Task Assignment: explorer_m2_guard

You are `explorer_m2_guard` (teamwork_preview_explorer).
Target: Milestone 2 — Attack Guard Implementation, Attacker RST Suppression, and Guard Self-Test.
Project Root: /Users/raja/Documents/syn-edge-flooding
Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard
Parent Orchestrator: orchestrator_1_gen2 (c915840f-b40f-4c6b-9b28-92a18579e73d)

Scope:
- Attacker RST suppression iptables rule (`iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP`) saved to `infra/attacker_rules.txt`.
- Fail-safe wrapper `tools/attack_guard.sh <tool> <args>` enforcing:
  1. Target IP == VICTIM_PRIVATE_IP from lab.env (exact string match).
  2. Duration <= 60 s via timeout.
  3. SYN flood rate <= 10,000 pps (interval >= u100); strictly reject `--flood` and `--faster`.
  4. Connection hold count <= 2,000.
  5. Emergency kill switch file `/tmp/LAB_STOP` absent (refuse if present).
- Automated self-test script `tools/guard_selftest.sh` that proves refusal on all violations and success on valid invocation, saving output to `infra/guard_selftest.txt`.
- Verification commands and evidence chain for Human Safety Gate G2.

Produce your structured handoff report in:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard/handoff.md

## 2026-10-07T07:31:36Z
You are explorer_m2_guard, an exploration agent for Milestone 2 (Attack Guard Implementation, Attacker RST Suppression, and Guard Self-Test).

Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard
Project Root: /Users/raja/Documents/syn-edge-flooding

MANDATORY FIRST STEP: Read the original user request from:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Read project context:
- /Users/raja/Documents/syn-edge-flooding/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/lab.env
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md (§4.1, §4.2, §4.3, §4.4, Phase 2, Phase 4)
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard/DISPATCH.md

Your Scope:
1. Formulate Attacker RST suppression iptables rule:
   - sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP
   - Record in infra/attacker_rules.txt
   - Must be scoped strictly to victim private IP.
2. Formulate fail-safe attack guard wrapper: `tools/attack_guard.sh <tool> <args>`
   Must refuse unless ALL hold:
   - target IP == VICTIM_PRIVATE_IP from lab.env (string-exact)
   - duration <= 60 s (enforced with timeout)
   - SYN rate <= 10,000 pps (hping3 interval >= u100; strictly reject --flood and --faster)
   - connection-hold count <= 2,000
   - kill switch file /tmp/LAB_STOP is absent
3. Formulate automated guard self-test script: `tools/guard_selftest.sh`
   Must test and prove refusal for:
   (a) unauthorized / non-victim IP
   (b) duration 61 s (> 60 s)
   (c) interval below u100 (e.g. u99)
   (d) --flood or --faster
   (e) connection count > 2,000 (e.g. 2,001)
   (f) presence of /tmp/LAB_STOP
   And prove successful invocation for valid bounded parameters.
   Outputs result to infra/guard_selftest.txt for Human Gate G2.
4. Write your full analysis and implementation guide to:
   /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard/handoff.md
   following the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
Notify orchestrator when complete via send_message.
