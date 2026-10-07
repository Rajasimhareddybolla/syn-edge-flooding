# DISPATCH — explorer_survey_2

## Objective
Investigate system architecture, scientific methodologies, data pipeline flow, and edge cases.
Inspect:
- Socket state sampling mechanism via `/proc/net/tcp`, `/proc/net/snmp`, `/proc/net/netstat` vs `ss`.
- Kernel sysctl toggles (`break` vs `fix` profile) and iptables RST drop rule on attacker.
- Evaluation methodology: capacity calibration, train/test split (reps 1-3 vs 4-5), metric calculations (detection delay, false alarm rate, CPU/RAM overhead).
- Data artifact schemas, pipeline integration, threats to validity and failure modes.

Provide your findings in `.agents/teamwork/explorer_survey_2/survey_methodology.md`.

## 2026-10-07T06:24:16Z
Sender: f6cfd525-c586-41eb-8148-3a42cc6823d8
Content:
You are explorer_survey_2 operating in working directory /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2.
Parent Orchestrator: orchestrator_1 (conversationId: f6cfd525-c586-41eb-8148-3a42cc6823d8).

You MUST read the original request before starting work:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Also read:
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md
- /Users/raja/Documents/syn-edge-flooding/docs/design.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2/DISPATCH.md

Your mission:
Investigate the technical and scientific methodology:
1. Low-overhead socket state sampling from /proc/net/tcp, /proc/net/snmp, /proc/net/netstat vs ss.
2. Kernel parameters (break vs fix profiles) and attacker RST suppression.
3. Capacity calibration procedure, traffic generation tools (wrk, ab, hping3, conn_hold.py).
4. Dual-signal detection mathematics (EWMA baseline, completion ratio, freeze on alarm), tuning vs test evaluation rules.
5. Overhead measurement methodology (pidstat vs Suricata), figure/table generation pipelines.

Write your findings to:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_2/survey_methodology.md
Also provide handoff.md in your working directory.
When done, message orchestrator_1 with send_message.
