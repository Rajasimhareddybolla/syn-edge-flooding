# Update 015 — Parallel E2E Testing Track Launched Alongside Milestone 2

- **Date / Time:** 2026-10-07 13:06 IST
- **Status:** Dual-Track Execution Active (Milestone 2 Implementation + E2E Testing Track)
- **Manager:** Autonomous Lead Coordinator
- **Lead Orchestrator:** `orchestrator_1_gen2`
- **Active Specialists:** `explorer_m2_env`, `explorer_m2_guard`, `spec_miner_m2_contracts`, `test_writer_e2e`
- **Reference Spec:** [docs/AGENTS_tcp_flood_lab.md](file:///Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md)

---

## 1. Dual-Track Execution Structure
The project is operating two concurrent, synchronized tracks to ensure rapid progress without compromising verification rigor:

```
[Master Plan: PROJECT.md]
        │
        ├──> Track A (Implementation): Milestone 2 Tooling, Sysctl & Attack Guard
        │       ├── explorer_m2_env (Packages & Nginx backlog)
        │       ├── explorer_m2_guard (attack_guard.sh & iptables RST drop)
        │       └── spec_miner_m2_contracts (Contracts & schemas)
        │
        └──> Track B (E2E Testing): Independent Opaque-Box Test Harness
                └── test_writer_e2e (4-Tier Verification Architecture)
```

---

## 2. 4-Tier Test Architecture Specifications (`test_writer_e2e`)
`test_writer_e2e` is developing an opaque-box test harness derived directly from `ORIGINAL_REQUEST.md` and `docs/AGENTS_tcp_flood_lab.md`:

1. **Tier 1 (Feature Coverage):** Minimum $\ge 5$ tests per feature validating `lab.env` contracts, security group isolation, SSH key permissions, and basic tool syntax.
2. **Tier 2 (Boundary & Corner Cases):** Strict testing of limits:
   - Target IP: string-exact match to `VICTIM_PRIVATE_IP` vs arbitrary IP rejection.
   - Duration: $60\text{ s}$ accepted vs $61\text{ s}$ refused.
   - SYN rate: `u100` ($10,000\text{ pps}$) accepted vs `u99`, `--flood`, `--faster` refused.
   - Connection hold: $2,000$ accepted vs $2,001$ refused.
   - Kill switch: immediate refusal if `/tmp/LAB_STOP` is present.
3. **Tier 3 (Pairwise Interactions):** Cross-feature combinations (e.g., `break` vs `fix` profile toggling coupled with attack execution).
4. **Tier 4 (End-to-End Scenarios):** Full scenario trace assertions.

Deliverables include [TEST_INFRA.md](file:///Users/raja/Documents/syn-edge-flooding/TEST_INFRA.md), test files in `tests/`, and [TEST_READY.md](file:///Users/raja/Documents/syn-edge-flooding/TEST_READY.md).

---

## 3. Milestone 2 Implementation Progress
Explorers are finalizing their scripts for host package installation, Nginx configuration (`backlog=128`), and `attack_guard.sh`. The Milestone 2 worker will deploy these configurations once the designs are signed off.

