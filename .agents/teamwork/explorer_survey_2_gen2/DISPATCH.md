# DISPATCH — explorer_survey_2_gen2

## Objective
Resume and complete the methodology survey from explorer_survey_2.
Refer to:
- `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2/progress.md` (which already analyzed the key dimensions)
- `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_survey_1/survey_spec.md`
- `/Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md`
- `/Users/raja/Documents/syn-edge-flooding/docs/design.md`

Produce:
- `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2_gen2/survey_methodology.md` covering:
  1. Socket sampling mechanism (`/proc/net/tcp`, snmp, netstat vs `ss`)
  2. Sysctl profiles (`break` vs `fix`) and iptables RST suppression
  3. Capacity calibration & traffic generator configurations (`wrk`, `ab`, `hping3`, `conn_hold.py`)
  4. Detection algorithms (B1, D1 dual-trigger, D2 multi-branch), baseline freeze, hysteresis clearing, train/test split (reps 1-3 vs 4-5)
  5. Computational overhead benchmark and figure/table pipelines
- `handoff.md` in your working directory.
## 2026-10-07T06:33:01Z
Sender: orchestrator_1 (f6cfd525-c586-41eb-8148-3a42cc6823d8)
Message:
You are explorer_survey_2_gen2 operating in working directory /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2_gen2.
Parent Orchestrator: orchestrator_1 (conversationId: f6cfd525-c586-41eb-8148-3a42cc6823d8).

You MUST read the original request before starting work:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Also read:
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md
- /Users/raja/Documents/syn-edge-flooding/docs/design.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2_gen2/DISPATCH.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2/progress.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_survey_1/survey_spec.md

Your mission:
Synthesize the complete technical and scientific methodology report.
Cover:
1. Low-overhead socket state sampling from /proc/net/tcp, snmp, netstat vs ss.
2. Kernel parameters (break vs fix profiles) and attacker RST suppression.
3. Capacity calibration procedure & traffic generators (wrk, ab, hping3, conn_hold.py).
4. Detection algorithms (B1, D1 dual-signal, D2 multi-branch), baseline freeze, hysteresis clearing, train/test split (reps 1-3 vs 4-5).
5. Computational overhead benchmark and figure/table pipelines.

Write your report to:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2_gen2/survey_methodology.md
Write handoff.md in your working directory and notify orchestrator_1 with send_message.
