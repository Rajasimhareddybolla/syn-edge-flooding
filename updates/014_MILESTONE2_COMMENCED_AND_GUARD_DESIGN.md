# Update 014 — Milestone 2 Commenced: Tooling & Fail-Safe Attack Guard Design

- **Date / Time:** 2026-10-07 13:02 IST
- **Status:** Milestone 2 Active — Tooling, Kernel Profiles & Safety Guard Design
- **Manager:** Autonomous Lead Coordinator
- **Lead Orchestrator:** `orchestrator_1_gen2`
- **Active Specialists:** `explorer_m2_env`, `explorer_m2_guard`, `spec_miner_m2_contracts`
- **Reference Spec:** [docs/AGENTS_tcp_flood_lab.md](file:///Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md)

---

## 1. Milestone 2 Scope & Objectives
With Milestone 1 infrastructure provisioned and certified, Milestone 2 establishes the server environment, host networking configurations, and safety constraints:

1. **Guest OS Tooling & Nginx:**
   - Install required packages across instances: `nginx`, `sysstat`, `tcpdump`, `chrony` on victim; `hping3` on attacker; `wrk`, `apache2-utils` on client.
   - Configure Nginx on victim to serve a 1 KB static `index.html` with constrained listen backlog: `listen 80 backlog=128;`.
2. **Kernel Sysctl Profiles (`tools/set_profile.sh`):**
   - Snapshot default kernel parameters to `infra/sysctl_defaults.txt`.
   - Provide automated profile switching:
     - `break`: `tcp_syncookies=0`, `tcp_max_syn_backlog=128`, `somaxconn=128` (exposes SYN queue exhaustion).
     - `fix`: `net.ipv4.tcp_syncookies=1` (kernel mitigation enabled).
3. **Attacker Kernel RST Suppression:**
   - Apply `iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP` on attacker host to prevent the attacker kernel from tearing down half-open sockets upon receiving unsolicited SYN-ACKs.
4. **Fail-Safe Attack Guard (`tools/attack_guard.sh`):**
   - Enforce mandatory invariant checks before launching any attack binary:
     - Target IP strictly equals `VICTIM_PRIVATE_IP` (exact string match).
     - Duration $\le 60\text{ s}$ via system `timeout`.
     - SYN rate $\le 10,000\text{ pps}$ (interval $\ge \text{u100}$); strictly reject `--flood` and `--faster`.
     - Max held connections $\le 2,000$.
     - Kill switch file `/tmp/LAB_STOP` absent (refuses execution immediately if present).

---

## 2. Preparation for Human Safety Gate G2
Before any attack command can be invoked in Phase 5, the team must execute `tools/guard_selftest.sh` to prove that the guard systematically refuses out-of-spec targets, excessive durations, high rates, and kill-switch conditions, capturing proof in `infra/guard_selftest.txt`.

---

## 3. Parallel E2E Testing Track
Independent test specialists have begun assembling opaque-box verification suites (Tiers 1–4) to continuously validate requirements as implementations deploy.

