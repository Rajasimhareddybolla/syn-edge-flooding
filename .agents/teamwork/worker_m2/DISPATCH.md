## 2026-10-07T08:01:30Z
You are worker_m2, the implementation worker for Milestone 2 (Victim Environment, Tooling & Safety Guardrails).

Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/worker_m2
Project Root: /Users/raja/Documents/syn-edge-flooding

MANDATORY FIRST STEP: Read the original user request from:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Read project context and explorer handoffs:
- /Users/raja/Documents/syn-edge-flooding/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/lab.env
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_env/handoff.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard/handoff.md
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m2_contracts/handoff.md
- /Users/raja/Documents/syn-edge-flooding/TEST_INFRA.md
- /Users/raja/Documents/syn-edge-flooding/TEST_READY.md

Staged assets from explorers for reference and deployment:
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard/proposed_attack_guard.sh
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard/proposed_guard_selftest.sh
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_guard/proposed_attacker_rules.txt

Write Ownership:
You own exclusively:
- `infra/sysctl_defaults.txt`
- `infra/attacker_rules.txt`
- `infra/guard_selftest.txt`
- `tools/set_profile.sh`
- `tools/attack_guard.sh`
- `tools/guard_selftest.sh`
- Remote guest configurations on EC2 instances (victim, attacker, client).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A forensic auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Execution Tasks:
1. SSH & Package Provisioning:
   - On victim: sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y -o DPkg::Lock::Timeout=60 python3-pip sysstat jq chrony tcpdump nginx
   - On attacker: sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y -o DPkg::Lock::Timeout=60 python3-pip sysstat jq chrony tcpdump hping3
   - On client: sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y -o DPkg::Lock::Timeout=60 python3-pip sysstat jq chrony tcpdump apache2-utils wrk curl
2. Nginx Setup on Victim:
   - Configure /etc/nginx/sites-available/default with `listen 80 default_server backlog=128;`
   - Create 1,024 byte static index.html at /var/www/html/index.html
   - Test config (sudo nginx -t) and restart nginx (sudo systemctl restart nginx)
   - Verify with curl from client to http://$VICTIM_PRIVATE_IP/ returning 200 and exactly 1024 bytes, and verify ss -tlpn shows Send-Q=128
3. Sysctl Defaults Snapshot:
   - Query live sysctl on victim (tcp_syncookies, tcp_max_syn_backlog, somaxconn, tcp_synack_retries, ip_local_port_range) and client ulimit -n
   - Save to infra/sysctl_defaults.txt per schema in spec_miner_m2_contracts/handoff.md
4. Sysctl Profile Tooling (tools/set_profile.sh):
   - Create tools/set_profile.sh with chmod +x (supporting break, fix, default, with remote SSH dispatch if invoked on Mac)
   - Test tools/set_profile.sh break (verify tcp_syncookies=0, backlog=128, somaxconn=128)
   - Test tools/set_profile.sh fix (verify tcp_syncookies=1, backlog=128, somaxconn=128)
5. Attacker RST Suppression:
   - Deploy sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP on attacker
   - Verify with iptables -C OUTPUT ... returning 0
   - Record commands and verification in infra/attacker_rules.txt
6. Attack Guard & Self-Test Suite:
   - Deploy tools/attack_guard.sh (chmod +x) enforcing all 5 invariants fail-closed
   - Deploy tools/guard_selftest.sh (chmod +x)
   - Execute tools/guard_selftest.sh and save full verified output to infra/guard_selftest.txt for Human Safety Gate G2
7. Full Test Suite Validation:
   - Execute bash tests/run_all_tests.sh and verify all 109 tests pass cleanly with exit code 0
8. Deliver handoff report:
   - Write comprehensive report to /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/worker_m2/handoff.md
   - Follow 5-component protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method)
   - Notify orchestrator via send_message when complete.
