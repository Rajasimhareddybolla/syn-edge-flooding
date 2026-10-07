# Task Assignment: explorer_m2_env

You are `explorer_m2_env` (teamwork_preview_explorer).
Target: Milestone 2 — Host packages, Nginx configuration, and Sysctl Break/Fix Profiles.
Project Root: /Users/raja/Documents/syn-edge-flooding
Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_env
Parent Orchestrator: orchestrator_1_gen2 (c915840f-b40f-4c6b-9b28-92a18579e73d)

Scope:
- Packages to install across all 3 nodes (victim, attacker, client) via APT.
- Nginx setup on victim: `listen 80 backlog=128;`, 1 KB static `index.html`.
- Sysctl defaults snapshot to `infra/sysctl_defaults.txt`.
- Sysctl break/fix profile toggling script `tools/set_profile.sh {break|fix|default}`.
- Verification commands and evidence chain.

Produce your structured handoff report in:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_env/handoff.md

## 2026-10-07T07:31:36Z
You are explorer_m2_env, an exploration agent for Milestone 2 (Victim Environment, Tooling & Sysctl Break/Fix Profiles).

Working Directory: /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_env
Project Root: /Users/raja/Documents/syn-edge-flooding

MANDATORY FIRST STEP: Read the original user request from:
/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/ORIGINAL_REQUEST.md

Read project context:
- /Users/raja/Documents/syn-edge-flooding/PROJECT.md
- /Users/raja/Documents/syn-edge-flooding/lab.env
- /Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md (§4.1, §4.5, Phase 2 §236-251)
- /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_env/DISPATCH.md

Your Scope:
1. Formulate exact APT package installation steps across all 3 nodes (victim, attacker, client):
   - All hosts: python3-pip, sysstat, jq, chrony, tcpdump
   - Victim: nginx
   - Attacker: hping3
   - Client: apache2-utils, wrk, curl
2. Formulate Nginx configuration on victim:
   - listen 80 backlog=128; in default server block
   - 1 KB static index.html
   - Service reload and curl 200 verification
3. Formulate sysctl snapshot and break/fix toggling:
   - Snapshot system defaults to infra/sysctl_defaults.txt (net.ipv4.tcp_syncookies, net.ipv4.tcp_max_syn_backlog, net.core.somaxconn, net.ipv4.tcp_synack_retries, net.ipv4.ip_local_port_range, client ulimit -n)
   - Break profile: net.ipv4.tcp_syncookies=0, net.ipv4.tcp_max_syn_backlog=128, net.core.somaxconn=128
   - Fix profile: net.ipv4.tcp_syncookies=1 (others unchanged)
   - Script tools/set_profile.sh {break|fix|default}
4. Write your full analysis and implementation guide to:
   /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_env/handoff.md
   following the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
Notify orchestrator when complete via send_message.
