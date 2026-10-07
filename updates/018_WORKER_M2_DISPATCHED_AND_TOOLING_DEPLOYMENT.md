# Update 018 — Milestone 2 Worker Dispatched: Host Tooling & Guard Deployment

- **Date / Time:** 2026-10-07 13:31 IST
- **Status:** Milestone 2 Implementation Actively Executing on AWS Fleet
- **Manager:** Autonomous Lead Coordinator
- **Lead Orchestrator:** `orchestrator_1_gen2`
- **Active Implementation Worker:** `worker_m2`
- **Reference Spec:** [docs/AGENTS_tcp_flood_lab.md](file:///Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md)

---

## 1. Milestone 2 Implementation Scope
Following the delivery of comprehensive plans and 100% green test assertions, `worker_m2` has been deployed with exclusive implementation ownership of Milestone 2:

1. **Remote Package Provisioning (APT):**
   - **Victim (`172.31.37.214`):** `nginx`, `sysstat`, `jq`, `chrony`, `tcpdump`, `python3-pip`.
   - **Attacker (`172.31.42.168`):** `hping3`, `sysstat`, `jq`, `chrony`, `tcpdump`, `python3-pip`.
   - **Client (`172.31.41.87`):** `apache2-utils`, `wrk`, `curl`, `sysstat`, `jq`, `chrony`, `tcpdump`, `python3-pip`.

2. **Victim Nginx Configuration:**
   - Configure `/etc/nginx/sites-available/default` with `listen 80 default_server backlog=128;`.
   - Replace root index with a static 1,024 byte payload at `/var/www/html/index.html`.
   - Reload Nginx and verify HTTP 200 via internal loopback and private IP.

3. **Kernel Parameters & Profiles (`tools/set_profile.sh`):**
   - Snapshot default kernel parameters to `infra/sysctl_defaults.txt`.
   - Implement `tools/set_profile.sh` supporting:
     - `break`: `net.ipv4.tcp_syncookies=0`, `net.ipv4.tcp_max_syn_backlog=128`, `net.core.somaxconn=128`.
     - `fix`: `net.ipv4.tcp_syncookies=1` (SYN-cookie protection enabled).

4. **Attacker RST Suppression (`infra/attacker_rules.txt`):**
   - Apply `iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP` on attacker host to prevent Linux kernel RST emissions from prematurely clearing victim half-open connection slots.

5. **Fail-Safe Attack Guard & Self-Test (`tools/attack_guard.sh`):**
   - Deploy `tools/attack_guard.sh` enforcing target IP locking, duration $\le 60\text{ s}$, rate $\le 10,000\text{ pps}$, connection count $\le 2,000$, and kill switch `/tmp/LAB_STOP`.
   - Execute `tools/guard_selftest.sh` on the attacker host and save verified output to `infra/guard_selftest.txt`.

---

## 2. Next Gate: Human Safety Gate G2
Once `worker_m2` completes deployment, the verified output `infra/guard_selftest.txt` will be presented for Human Safety Gate G2 confirmation before proceeding to Phase 3/4 calibration and Phase 5 experiment execution.

