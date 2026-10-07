# Update 021 — M2 Complete: Tools Deployed, Gate G2 Pending

**Time:** 2026-10-07T08:21:00Z  
**Phase:** M2 → M3  
**Status:** 🟡 Gate G2 Awaiting User Sign-Off

---

## What Happened

Resumed from quota pause. All 3 EC2 nodes verified alive (victim, attacker, client).

**Completed in this session:**
- ✅ `tools/` deployed to all 3 nodes (sampler, probe, collect, attack_guard, guard_selftest, conn_hold, set_profile)
- ✅ Break sysctl profile applied on victim: `syncookies=0, backlog=128, somaxconn=128`
- ✅ Attacker RST drop rule confirmed active
- ✅ **Live guard self-test: 16/16 PASS** on attacker node
- ✅ `infra/guard_selftest_live.txt` saved
- ✅ `infra/attacker_rules.txt` written
- ✅ `handoffs/A2.md` written

## Gate G2

Guard self-test 16/16 passed on live attacker. **Waiting for Raja's "confirmed" to unlock Phase 5 attack traffic.**

## In Progress

- 🔄 Sampler validation (120s idle test on victim) — running now
- ⏳ Capacity calibration (wrk stepped load) — queued after sampler

## Next

M3 complete → M4 (65-run experiments) — blocked on Gate G2 for attack scenarios only.
Baseline S0 runs (no attack) can proceed without Gate G2.

