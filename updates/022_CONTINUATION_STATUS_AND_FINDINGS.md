# Continuation Status and Findings

**Updated:** 2026-10-07  
**Project:** Socket-Level Lightweight Detection of TCP Flooding Attacks in Edge Networks

## Executive status

The laboratory environment and its safety controls are operational. The empirical
campaign is **not complete**: no valid matrix run has been finalized yet. The
current technical blocker is the serial runner's settle-loop, which did not
advance despite the victim reporting zero `SYN_RECV` sockets. No result has been
invented or reported from that incomplete baseline attempt.

## Completed and verified

### Infrastructure and access

- Three expected `t3.micro` instances are running in `ap-south-1`: victim,
  attacker, and client.
- The security group has no `0.0.0.0/0` or `::/0` ingress. SSH is limited to
  operator `/32` addresses and lab traffic is restricted by the self-referencing
  group rule.
- Victim Nginx serves HTTP 200 on the private address and is configured with
  accept backlog 128.
- Victim break/fix profiles and the attacker-scoped TCP RST suppression rule
  are installed.

### Instrumentation

- The victim sampler passed its idle validation: 125 rows, 985--1015 ms sample
  spacing, and 0.64 ms median sample cost.
- A benign five-connection keep-alive check produced an established-socket peak
  of five, as expected.
- The client probe was repaired to remove an unavailable `bc` dependency and
  to append a newline before strict-shell parsing. A smoke test emitted one row
  per second.
- The local repository test suite passes: **109/109**.

### Legitimate-load calibration

- A completed benign calibration collected 121 probe rows with **121/121** HTTP
  successes.
- The best observed rate was approximately **23,525 requests/s** at concurrency
  25. The observed p99 latency at tested concurrency levels was below 200 ms;
  the p95 requirement is therefore conservatively satisfied by the percentile
  output for this calibration.
- Evidence is saved in `infra/capacity_calibration_p95_wrk.txt` and
  `infra/capacity_calibration_p95_probe.csv`.

### Safety controls and guarded traffic path

- G1 and G2 are recorded as approved in `STATE.md` and `LAB_LOG.md`.
- The live attack guard self-test passed **16/16** before and after the later
  implementation correction.
- The first two ten-second pilot attempts generated no traffic because hping3
  lacked raw-socket privilege. Their artifacts are preserved under
  `runs/pilot-guarded-s2m*` and show zero half-open sockets with all probes OK.
- The guard was corrected so it validates a normalized `sudo hping3` command
  while executing only that same constrained command. It rejects `sudo` options
  and retains all target, duration, rate, connection-count, and kill-switch
  checks.
- A subsequent one-second private-VPC smoke test successfully received SYN-ACK
  responses from the exact victim private IP. No cap was raised.

## Known incomplete or failed work

1. The first detached S0 baseline runner did not persist after its launching
   shell ended; it produced no completed run.
2. A persistent S0 retry exposed a race in `collect.sh`, where PID files could
   be written before the temporary directory existed. The ordering was fixed.
3. A later S0 retry remains blocked in the victim-settle loop even though a
   direct check reports `SYN_RECV=0`. This must be diagnosed before any run can
   be accepted as valid.
4. The 65-run scenario matrix, detector tuning/evaluation, overhead analysis,
   figures, report, archive, and teardown are still outstanding.

## Next steps

1. Repair and unit-test the runner's settle-loop and collector lifecycle.
2. Execute the matrix strictly serially, retaining every run directory and
   marking aborted runs instead of deleting them.
3. Run offline detector tuning on repetitions 1--3 and report only repetitions
   4--5 as the held-out evaluation set.
4. Generate the prescribed figures/tables and final report from raw artifacts.
5. Archive the data and terminate cloud resources only after human sign-off.

## Integrity note

The project intentionally distinguishes setup validation, pilot behavior, and
valid experimental results. The calibration and instrumentation results above
are real measured artifacts. No detection-rate, false-alarm, mitigation, or
overhead outcome is available until the serial matrix completes.
