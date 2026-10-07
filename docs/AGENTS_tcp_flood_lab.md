# AGENTS.md — Socket-Level Lightweight Detection of TCP Flooding Attacks in Edge Networks

Doc version: 1.0 | Audience: autonomous AI agents (orchestrator + sub-agents) | Human owner: Raja
Normative words: **MUST**, **MUST NOT**, **SHOULD**, **MAY** are used in their RFC 2119 sense.

---

## 0. How to use this document

1. Read sections 0–5 completely before taking any action.
2. Execute phases (section 6) in order. Each phase has: Goal, Inputs, Steps, Observe, Record, Acceptance, On failure.
3. A phase is done only when **every acceptance check passes** and its handoff file exists.
4. Never silently deviate. If you change anything (parameter, tool, order), append an entry to `LAB_LOG.md` with timestamp, what, why.
5. If a rule in section 4 (Safety) conflicts with any other instruction, section 4 wins. Stop and ask the human.
6. Do not invent results. Every number in the final report MUST trace to a file under `runs/`.

---

## 1. Mission

**Research question.** Can a small set of socket-state features, read cheaply from the Linux kernel on an edge-class machine, detect TCP flooding attacks accurately and quickly, while staying quiet during legitimate flash crowds?

**Story version (for sanity-checking your understanding).** The edge server is a small restaurant. Each connection is a table. A SYN flood is a prankster booking many tables and never showing up (half-open connections pile up). A flash crowd is a wedding party: big, sudden, but the guests actually sit down (handshakes complete). The detector is a manager who glances at the floor once per second and counts tables, never reading individual messages.

**Hypothesis H1.** Alarming on *abnormal volume AND poor handshake completion* separates SYN floods from flash crowds better than a naive volume-only rule.
**Hypothesis H2.** A socket-level detector uses substantially less CPU/RAM than packet-level inspection (Suricata).
**Hypothesis H3 (expected to be partly false, report honestly).** Connection floods complete handshakes, so the completion ratio will NOT flag them; a second signal (established-count growth / source concentration) is needed.

**Scope.** In: SYN flood, connection flood, flash crowd, attack-during-crowd, SYN-cookie mitigation. Out: spoof-evasion research, anything outside the lab VPC, payload inspection, ACK/RST floods (optional extension only).

---

## 2. Glossary (agents MUST use these terms consistently)

| Term | Meaning |
|---|---|
| Half-open | Socket in `SYN_RECV` on the victim (SYN received, final ACK not yet seen) |
| Completion ratio | Fraction of started inbound handshakes that finished (defined precisely in 6.4) |
| Flash crowd | Many legitimate clients connecting at once; handshakes complete |
| Backlog | Kernel queue limits: SYN queue (`tcp_max_syn_backlog`) and accept queue (`somaxconn`, nginx `backlog=`) |
| SYN cookies | Kernel mitigation (`tcp_syncookies=1`) that avoids storing half-open state |
| Run | One execution of one scenario with a unique `run_id` |
| Baseline | Detector's adaptive estimate of "normal" (EWMA) |
| Ground truth | `events.json` timestamps of when the attack/crowd really started and ended |

---

## 3. Architecture and agent roles

### 3.1 Topology (all in the default VPC of the configured AWS region)

```
 Operator Mac (agents run here; AWS CLI already configured)
     |  SSH (key auth, from operator public IP /32 only)
     v
 +---------+  private IPs only  +----------+
 | attacker|------------------->|  victim  |<------------+
 +---------+   (flood traffic)  | nginx +  |             |
                                | sampler  |      +-------------+
                                +----------+      |   client    |
                                                  | (legit load |
                                                  |  + probes)  |
                                                  +-------------+
```

- `victim`: t3.micro, Ubuntu 24.04. The "edge device". Runs nginx, sampler, detector, tcpdump.
- `attacker`: t3.micro. Runs attack tools only, only via guard wrapper (4.2).
- `client`: t3.micro. Generates legitimate traffic (quiet load, flash crowd) and 1 Hz service probes.

### 3.2 Agent roles (spawn plan)

| ID | Role | Spawn when | Owns |
|---|---|---|---|
| A0 | Orchestrator | immediately | `STATE.md`, `LAB_LOG.md`, phase gating, human escalation |
| A1 | Infra | after A0 preflight | AWS resources, `lab.env`, teardown |
| A2 | Victim/tooling | after A1 done | package installs, nginx, sysctl snapshots |
| A3 | Collector | parallel with A2 (develop locally, deploy after A2) | `sampler.py`, `probe.sh` |
| A4 | Traffic | parallel with A2 | legit generators, attack wrappers, `attack_guard.sh`, `conn_hold.py` |
| A5 | Runner | after A2+A3+A4 pass integration | executes run matrix, fetches artifacts |
| A6 | Detector/Analysis | after first pilot traces exist | detector, replay, metrics, figures |
| A7 | Reporter | after A6 | final report, README |

**Concurrency rules.**
- Phases 1–4 sub-agents MAY work in parallel on disjoint files.
- **Experiments (Phase 5+) MUST be strictly serial.** One run at a time; the lab is a shared physical resource. Only A5 may start traffic.
- Each agent writes `handoffs/<ID>.md` on completion: what was done, files produced, commands to reproduce, open issues.
- A0 updates `STATE.md` (phase, status, blockers) after every handoff.

---

## 4. Safety, cost, and ethics guardrails (non-negotiable)

### 4.1 Scope
- Attack tools MUST only target the `victim` **private IP** from the `attacker` instance. Nothing else, ever.
- The security group MUST NOT contain any rule with source `0.0.0.0/0` or `::/0`. SSH is allowed only from the operator's current public IP `/32`.
- No lab traffic may leave the VPC. No scanning, no third-party hosts.

### 4.2 Attack guard (A4 MUST implement before any attack runs)
`attack_guard.sh <tool> <args>` on the attacker MUST refuse unless ALL hold:
- target IP == `VICTIM_PRIVATE_IP` from `lab.env` (string-exact);
- duration ≤ 60 s (enforced with `timeout`);
- SYN rate ≤ 10,000 packets/s (hping3 interval ≥ `u100`); **never** use `--flood` or `--faster`;
- connection-hold count ≤ 2,000;
- a kill switch file `/tmp/LAB_STOP` is absent (checked before launch; all tools launched via `timeout`).
Raising any cap requires explicit human approval recorded in `LAB_LOG.md`.

### 4.3 Human gates (stop and wait)
- **G1 (before Phase 1):** Human confirms they have read the current AWS policy on simulated DoS / security testing and that the lab complies. *The authors of this document did not verify the current policy text; do not assume.*
- **G2 (before first attack run):** Human confirms attack guard test output (`guard_selftest.txt`).
- **G3:** Any request to raise a cap in 4.2.

### 4.4 Stop-and-escalate conditions
Stop all traffic (`touch /tmp/LAB_STOP` on attacker), write the reason in `LAB_LOG.md`, notify the human if: any command would target a non-lab IP; more than 3 lab instances exist; estimated spend > US$15; an AWS abuse/policy notice appears; the security group gains a public rule; instances run > 12 h continuously.

### 4.5 Cost control
- Tag everything `Project=tcp-flood-lab`. Use `--credit-specification CpuCredits=standard` on t3 instances to avoid surprise unlimited-credit charges (note: CPU may throttle; record `CPUCreditBalance` in the run metadata).
- Stop (not terminate) instances between work sessions if pausing > 1 h; terminate at Phase 10.

### 4.6 Integrity
- Never delete raw run data. Never edit a raw CSV; derive into `analysis/`.
- Failed or aborted runs are kept and flagged, not hidden.

---

## 5. Global conventions

### 5.1 Repository layout (on the Mac: `~/tcp-flood-lab/`)

```
tcp-flood-lab/
  AGENTS.md              # this file
  STATE.md  LAB_LOG.md
  lab.env                # generated by A1 (never commit keys)
  handoffs/
  infra/                 # scripts + captured aws cli outputs
  tools/                 # sampler.py probe.sh attack_guard.sh conn_hold.py run_scenario.sh
  detector/              # detector.py replay.py params.yaml
  runs/<run_id>/         # raw artifacts per run (section 5.3)
  analysis/              # derived tables, figures, notebooks
  report/                # final report.md + figures
```

### 5.2 `lab.env` (exported by A1, sourced by everything)
`AWS_REGION, VPC_ID, SG_ID, KEY_NAME, KEY_PATH, VICTIM_ID, ATTACKER_ID, CLIENT_ID, VICTIM_PUB, ATTACKER_PUB, CLIENT_PUB, VICTIM_PRIVATE_IP, ATTACKER_PRIVATE_IP, CLIENT_PRIVATE_IP, VICTIM_IFACE` (usually `ens5`).

### 5.3 Run IDs and artifacts
`run_id = <scenario>-r<rep:02d>-<UTC yyyymmddThhmmssZ>` e.g. `S2M-r03-20261008T101500Z`.
Every run directory MUST contain:

| File | Source | Content |
|---|---|---|
| `events.json` | runner | ground truth + parameters (schema 5.4) |
| `victim_metrics.csv` | sampler on victim | 1 Hz socket/kernel metrics (schema 5.5) |
| `probe.csv` | probe on client | 1 Hz legitimate-user probe results |
| `load_client.txt` | client | raw output of ab/wrk/conn_hold |
| `attack_attacker.txt` | attacker | raw hping3/conn_hold output |
| `sysctl_snapshot.txt` | victim | relevant sysctl values at run start |
| `nginx_access.log` | victim | slice for the run window |
| `victim_cpu_pidstat.txt` | victim | `pidstat -u -r -p ALL 1` for sampler/detector/nginx |
| `capture.pcap` | victim | ONLY for rep 1 of each scenario (see 6.5) |
| `notes.md` | runner | anomalies, aborts, anything unexpected |

### 5.4 `events.json` schema
```json
{
  "run_id": "S2M-r03-...",
  "scenario": "S2M",
  "rep": 3,
  "params": {"tool": "hping3", "interval_us": 1000, "duration_s": 30},
  "syncookies": 0,
  "t_start_epoch_ms": 0,
  "t_end_epoch_ms": 0,
  "sampler_start_epoch_ms": 0,
  "sampler_stop_epoch_ms": 0,
  "aborted": false,
  "abort_reason": null,
  "clock_offset_ms": {"victim": 0, "attacker": 0, "client": 0},
  "git_sha": "..."
}
```
Timestamps are UTC epoch milliseconds taken on the machine that generates the event. Before every batch, record chrony offsets (`chronyc tracking`) for all three hosts; abort the batch if any offset > 50 ms.

### 5.5 `victim_metrics.csv` schema (1 row per second, monotonic-clock paced)

| Column | Source / definition |
|---|---|
| `ts_ms` | epoch ms |
| `syn_recv, established, time_wait, close_wait, fin_wait, last_ack, listen_q` | counts per TCP state for local port 80 (from `/proc/net/tcp`; state hex 03=SYN_RECV, 01=ESTABLISHED, 06=TIME_WAIT, 08=CLOSE_WAIT) |
| `top_src_share` | share of non-listen port-80 sockets held by the single most common remote IP (0–1) |
| `n_distinct_src` | distinct remote IPs on port 80 |
| `d_passive_opens` | Δ `Tcp: PassiveOpens` (/proc/net/snmp) |
| `d_attempt_fails` | Δ `Tcp: AttemptFails` |
| `d_estab_resets` | Δ `Tcp: EstabResets` |
| `d_retrans` | Δ `Tcp: RetransSegs` |
| `d_listen_overflows, d_listen_drops` | Δ `TcpExt: ListenOverflows, ListenDrops` (/proc/net/netstat) |
| `d_syncookies_sent, d_syncookies_recv, d_syncookies_failed` | Δ `TcpExt: SyncookiesSent/Recv/Failed` |
| `d_reqq_full_cookies, d_reqq_full_drop` | Δ `TcpExt: TCPReqQFullDoCookies, TCPReqQFullDrop` (if present) |
| `cpu_pct, mem_used_mb` | whole-VM from `/proc/stat`, `/proc/meminfo` |
| `sample_cost_ms` | wall time the sampler spent producing this row |

Missing counters MUST be written as empty, not 0, and listed in `handoffs/A3.md`.

### 5.6 `probe.csv` schema
`ts_ms, http_code, t_connect_s, t_total_s, ok` — `ok=1` iff code 200 within 3 s. One probe per second from `client` to `http://$VICTIM_PRIVATE_IP/`, running through every run, independent of the load generator's own measurements.

---

## 6. Phases

### Phase 0 — Preflight (A0)
**Goal.** Confirm the environment.
**Steps.**
1. `aws sts get-caller-identity` and `aws configure get region`. Record account and region (mask account ID in any report).
2. Check local tools: `python3 --version` (≥3.10), `jq`, `git`, `ssh`. Install missing via Homebrew.
3. Human downloads for the Mac: **Wireshark** (`brew install --cask wireshark`). Analysis libs: `pip install pandas numpy matplotlib scikit-learn pyyaml`.
4. Create the repo layout (5.1), `git init`, add `.gitignore` for `*.pem`, `lab.env`, `runs/**/capture.pcap`.
5. Initialize `STATE.md` and `LAB_LOG.md`.
**Acceptance.** All commands succeed; **G1 confirmed** by human and logged.

### Phase 1 — Infrastructure (A1)
**Goal.** Three tagged instances in a private-traffic-only lab.
**Steps (all via AWS CLI; save every raw JSON output to `infra/`).**
1. `VPC_ID` = default VPC: `aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text`.
2. `MYIP=$(curl -s https://checkip.amazonaws.com)`.
3. Create SG `lab-sg` in that VPC (tag Project). Ingress: TCP 22 from `$MYIP/32`; all protocols from `lab-sg` itself (`--source-group`). Nothing else.
4. Key pair: `aws ec2 create-key-pair --key-name tcp-flood-lab --query KeyMaterial --output text > ~/.ssh/tcp-flood-lab.pem && chmod 400 ~/.ssh/tcp-flood-lab.pem`.
5. AMI: `aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id --query Parameter.Value --output text`.
6. Launch three instances: `aws ec2 run-instances --image-id $AMI --instance-type t3.micro --key-name tcp-flood-lab --security-group-ids $SG_ID --credit-specification CpuCredits=standard --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=victim},{Key=Project,Value=tcp-flood-lab}]'` (repeat for `attacker`, `client`). Place all three in the same subnet/AZ.
7. `aws ec2 wait instance-running`, then collect IDs, public and private IPs into `lab.env`.
8. SSH to each (`ssh -i $KEY_PATH ubuntu@$X_PUB`), accept host keys, run `hostname; ip -br a; chronyc tracking`. Record `VICTIM_IFACE`.
9. Verify private connectivity: from `client` and `attacker`, `ping -c3 $VICTIM_PRIVATE_IP`.
**Observe/record.** Instance types, AZ, AMI ID, private IPs, chrony offsets.
**Acceptance.** (a) `aws ec2 describe-security-groups` shows no `0.0.0.0/0` rule; (b) 3 instances tagged and running; (c) pings succeed; (d) `lab.env` complete.
**On failure.** SSH timeout → operator public IP changed; update SG rule (`/32`), log it.

### Phase 2 — Victim and tooling setup (A2)
**Goal.** Victim serves a tiny site; all tools installed; defaults recorded.
**Steps.**
1. All hosts: `sudo apt-get update && sudo apt-get install -y python3-pip sysstat jq chrony tcpdump`.
2. Victim: `sudo apt-get install -y nginx`. Replace default page with a ~1 KB static `index.html`. Set `listen 80 backlog=128;` in the default server block. Reload.
3. Client: `sudo apt-get install -y apache2-utils wrk curl`.
4. Attacker: `sudo apt-get install -y hping3`.
5. Victim sysctl **break configuration** (small queues, no cookies), applied via `/etc/sysctl.d/99-lab.conf` with two named profiles you can toggle with a script `set_profile.sh {break|fix}`:
   - `break`: `net.ipv4.tcp_syncookies=0`, `net.ipv4.tcp_max_syn_backlog=128`, `net.core.somaxconn=128`
   - `fix`: `net.ipv4.tcp_syncookies=1` (others unchanged)
6. Attacker RST suppression (**required for SYN-flood realism**): the attacker's kernel does not know about hping3's raw SYNs and will answer the victim's SYN-ACK with RST, which makes the victim free the half-open entry immediately and hides the attack. Add, scoped to the victim only: `sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP`. Save the exact rule in `infra/attacker_rules.txt`; it MUST be removed in Phase 10.
7. Snapshot defaults before changing anything: `sysctl net.ipv4.tcp_syncookies net.ipv4.tcp_max_syn_backlog net.core.somaxconn net.ipv4.tcp_synack_retries net.ipv4.ip_local_port_range` → `infra/sysctl_defaults.txt`. Also `ulimit -n` on client.
8. On the Mac, install Wireshark (done in Phase 0).
**Observe.** `curl -s -o /dev/null -w '%{http_code}\n' http://$VICTIM_PRIVATE_IP/` from client returns 200.
**Acceptance.** 200 from client; both sysctl profiles switch correctly (verify with `sysctl` output); RST rule present on attacker; defaults file saved.

### Phase 3 — Instrumentation (A3)
**Goal.** Measure everything cheaply and uniformly.
**Steps.**
1. Write `tools/sampler.py` (stdlib only; no psutil): once per second on a monotonic schedule, read `/proc/net/tcp` (and `/proc/net/tcp6` if port 80 sockets appear there), `/proc/net/snmp`, `/proc/net/netstat`, `/proc/stat`, `/proc/meminfo`; emit one CSV row per 5.5. Take `--out`, `--hz` (default 1), `--method {proc,ss}` (default `proc`). The `ss` method shells out to `ss -tan` and exists only for the overhead comparison in Phase 8.
2. Write `tools/probe.sh` per 5.6 (curl, `--max-time 3`).
3. Write `tools/collect.sh <run_id>`: starts pidstat, tcpdump (if requested), sampler on victim; probe on client; and stops/fetches them after the run via `scp`.
4. Unit-check the sampler: open 5 `curl` connections with keepalive and confirm `established` increases by ~5.
**Observe.** CSV has exactly 1 row/second over 120 s ±1; `sample_cost_ms` median < 5 ms.
**Acceptance.** 120-second idle test passes the row-count check; no negative deltas; counter availability list written.

### Phase 4 — Traffic tools (A4)
**Goal.** Reproducible, bounded legitimate and attack traffic.
**Steps.**
1. `attack_guard.sh` per 4.2 plus `guard_selftest.sh` that proves it **refuses** (a) a non-victim IP, (b) duration 61 s, (c) interval below `u100`, (d) `--flood`, (e) 2,001 connections. Save output to `infra/guard_selftest.txt`. **Wait for human gate G2.**
2. Legitimate generators (on `client`):
   - quiet: `wrk -t1 -c2 -d{D}s -H "Connection: close" http://$VICTIM_PRIVATE_IP/` (low, steady).
   - flash crowd: `ab -n {N} -c {C} http://$VICTIM_PRIVATE_IP/` (no `-k`, so every request opens a new TCP connection like real browsers arriving). Also a ramp variant: concurrency stepping 10→C over 10 s.
3. SYN flood (on `attacker`, via guard): `hping3 -S -p 80 -i u{INTERVAL} $VICTIM_PRIVATE_IP` wrapped in `timeout {D}`. Intensity levels: **L = `u10000` (≈100 pps), M = `u1000` (≈1,000 pps), H = `u100` (≈10,000 pps)**. Do not use `--rand-source` (AWS drops spoofed-source packets inside a VPC; expect all flood traffic to come from the attacker's real IP, and record this as a known limitation).
4. Connection flood: `tools/conn_hold.py --host $VICTIM_PRIVATE_IP --port 80 --n {N} --hold {D} --ramp 5` opens N TCP connections (asyncio), sends a partial HTTP request line only, holds them for D seconds, then closes cleanly. Levels: **L=100, M=500, H=2000**. Raise `ulimit -n` accordingly; log it.
5. **Calibration run (A4 + A5):** find victim capacity. Step `wrk` concurrency 10, 25, 50, 100, 200, 400 for 20 s each; record req/s, p95 latency, probe `ok` rate. Define `CAPACITY_RPS` = highest req/s with ≥99% probe success and p95 < 200 ms. Flash crowd sizes are then **small = 25%, medium = 50%, large = 100% of capacity** (translate to `-c`/`-n` for `ab`; record the mapping in `infra/crowd_levels.json`).
**Acceptance.** Guard self-test passes and is human-approved; calibration file exists; each generator has a 10-second dry run with expected visible effect in `victim_metrics.csv`.

### Phase 5 — Experiments (A5; strictly serial)

#### 5.1 Run matrix

| Scenario | Description | Params | Cookies | Reps | Window |
|---|---|---|---|---|---|
| S0 | Quiet baseline | quiet load, 120 s | off (break profile) | 5 | 120 s |
| S1S / S1M / S1L | Flash crowd small/med/large | per `crowd_levels.json`, event 30 s | off | 5 each | 60 s pre, 30 s event, 60 s post |
| S2L / S2M / S2H | SYN flood low/med/high | hping3 L/M/H, event 30 s | off | 5 each | same |
| S3L / S3M / S3H | Connection flood | conn_hold L/M/H, hold 30 s | off | 5 each | same |
| S4 | SYN flood M **during** flash crowd M | both concurrent, 30 s | off | 5 | same |
| S5M / S5H | SYN flood M/H with mitigation | as S2M/S2H | **on** (fix profile) | 5 each | same |

Total ≈ 65 runs × ~4 min ≈ 4.5 h. A quiet background (S0-level load) MUST run in every scenario except S0 itself, so attack and crowd runs share a realistic baseline.

#### 5.2 Per-run procedure (script it as `tools/run_scenario.sh`)
1. **Pre-checks:** profile set (`break`/`fix`) and confirmed via `sysctl`; chrony offsets < 50 ms; victim `syn_recv` = 0 and `established` within baseline for 10 s; `/tmp/LAB_STOP` absent. If not settled within 120 s, abort run and log.
2. Create `runs/<run_id>/`; write `sysctl_snapshot.txt`.
3. Start sampler, probes, pidstat (and tcpdump if rep 1, see below).
4. Wait 60 s (pre-event window).
5. Record `t_start_epoch_ms`; launch event (via guard for attacks); wait for completion; record `t_end_epoch_ms`.
6. Wait 60 s (post window). Stop all collectors.
7. Fetch artifacts, write `events.json` and `notes.md`.
8. **Cooldown:** wait until `syn_recv == 0` for 10 consecutive seconds (SYN_RECV entries can take up to ~60 s to expire with default `tcp_synack_retries`). Cap at 120 s.
9. **Order:** randomize scenario order in blocks (one rep of every scenario per block, shuffled), not all reps of one scenario back to back; log the seed.
10. Pcap policy: `sudo tcpdump -i $VICTIM_IFACE -s 96 -w capture.pcap 'tcp port 80'` on **rep 1 of each scenario only**, wrapped in `timeout 180`. Header-only snaplen; delete nothing, but exclude pcaps from git.

#### 5.3 What to observe live and sanity-check (expected behavior)

| Scenario | Expected | If NOT observed |
|---|---|---|
| S0 | `syn_recv` ≈ 0–2; completion ratio ≈ 1; probes all `ok` | check nginx up; check client load |
| S1* | `established`/`time_wait` rise; `syn_recv` small; completion ratio stays high; probes mostly ok (latency may rise at L) | check `ab` isn't using `-k`; check ulimit |
| S2* (cookies off) | `syn_recv` climbs toward ≈ the backlog limit within seconds; `d_listen_drops` rises; probes begin failing at M/H; recovery after attack as entries expire | If `syn_recv` stays ~0: **RST suppression rule missing** (step 2.6) or guard blocked the tool |
| S3* | `established` climbs to ≈ N; completion ratio **stays high**; `top_src_share` ≈ 1.0; probes may degrade at H | If `established` plateaus below N: fd limit or backlog; log it |
| S4 | Both signals superimposed; crowd's successful handshakes keep completion ratio from collapsing as far as in S2 | — |
| S5* (cookies on) | `syn_recv` stays ≈ 0 (cookies avoid half-open state), `d_syncookies_sent` rises sharply, probes mostly ok | **Key finding:** with cookies on, the half-open signal disappears; detector must use cookie/queue counters instead |

Results that contradict these expectations are findings, not errors: record them in `notes.md`; do not tune the experiment to make them match.

**Acceptance for Phase 5.** All runs present, or each missing run has a logged reason; every run directory has the mandatory files (5.3 table); a `runs/INDEX.csv` (run_id, scenario, rep, aborted, notes) exists.

### Phase 6 — Detector (A6)

#### 6.1 Develop offline first
Build `detector/replay.py` which reads `victim_metrics.csv` row by row (simulating 1 Hz arrival) and outputs `alarm_ts` list. Only after offline validation, wrap the same core logic as `detector/detector.py` for online use on the victim. **Same code path for both** (shared module) so results are comparable.

#### 6.2 Features (per second, window `W=3` s for ratios)
| Name | Definition |
|---|---|
| `half_open` | `syn_recv` |
| `completion_ratio` | `Σd_passive_opens / max(1, Σd_passive_opens + Σd_attempt_fails)` over the last W seconds. (`PassiveOpens` counts handshakes completed; `AttemptFails` counts half-open attempts that died.) Validate this definition empirically against S0/S1/S2; if it is a poor proxy, document and propose another. |
| `estab_growth` | `established − EWMA(established)` |
| `queue_pressure` | `d_listen_drops + d_listen_overflows + d_reqq_full_drop` |
| `cookie_rate` | `d_syncookies_sent` |
| `top_src_share` | from sampler |

#### 6.3 Detector variants
- **B1 (naive baseline):** alarm if `half_open > FIXED_T` OR new-conn rate (`d_passive_opens`) > `FIXED_R`, for ≥ N s. Pick `FIXED_T`, `FIXED_R` from S0 maxima (document the rule: e.g., 99.9th percentile × 2).
- **D1 (proposed, volume AND failure):** adaptive baseline `mu_t = α·x_t + (1−α)·mu_{t−1}` for `x = half_open`. Alarm when for N consecutive seconds **both**: `half_open > max(FLOOR, K·mu)` AND `completion_ratio < TAU`. **Freeze baseline updates while in alarm** so the attack does not teach the detector that it is normal. Clear alarm after M consecutive calm seconds.
- **D2 (extended, addresses H3 and mitigation):** D1 OR a second branch: `estab_growth` high AND `top_src_share > S` (connection-flood branch) OR `cookie_rate`/`queue_pressure` high (cookies-on branch). Report each branch's contribution separately (ablation).
- **D3 (optional, only if time):** small decision tree / isolation forest (scikit-learn) on the same features, trained on runs reps 1–3, evaluated on reps 4–5. Report model size and inference time.

#### 6.4 Parameter selection protocol (prevents overfitting)
- Search grid: `α∈{0.05,0.1,0.2}`, `K∈{3,5,8}`, `TAU∈{0.3,0.5,0.7}`, `N∈{2,3,5}`, `FLOOR∈{20,50}`, `M=5`.
- **Tune on reps 1–3 only; report on reps 4–5 only.** Never report tuning-set results as final.
- Select the operating point that maximizes detection rate subject to 0 false alarms on S0 and S1 tuning runs; report the full trade-off curve too.

#### 6.5 Metrics (A6 computes from `events.json` + alarm lists)
- **Attack run:** `detected` = any alarm in `[t_start, t_end + 10 s]`; `detection_delay_s` = first alarm − `t_start`.
- **Benign run (S0, S1*):** `false_alarm` = any alarm anywhere in the run; count alarm-seconds.
- **Service impact (from `probe.csv`):** probe success % and p95 latency during event, per scenario and variant (no detector / cookies on).
- Aggregate as mean ± std (n reps) and show individual points; never report only means.

**Acceptance.** `detector/params.yaml` (final values), `analysis/metrics.csv` (one row per run per detector), replay reproduces from raw data with one command.

### Phase 7 — Mitigation analysis (A6)
Compare S2M/S2H (cookies off) vs S5M/S5H (cookies on): probe success, p95 latency, `syn_recv`, `d_listen_drops`, CPU. Answer explicitly: does D1 still alarm when cookies are on? (Expected: no via `half_open`; D2's cookie/queue branch should.)

### Phase 8 — Overhead (A5 runs, A6 analyzes)
**Goal.** Quantify the cost of detection.
**Runs (each 120 s on S0-level load, then 60 s during S2M, 5 reps):**
- O0: nothing running (baseline CPU/RSS).
- O1: sampler `--method proc` @1 Hz + D1 online.
- O2: sampler `--method ss` @1 Hz + D1 online.
- O3: `--method proc` @10 Hz.
- O4 (optional): Suricata default config on `$VICTIM_IFACE`, same loads. Install via apt; record version/ruleset, CPU, RSS, and whether it flagged S2M.
**Measure** with `pidstat -u -r -p <pid> 1`; report mean/p95 CPU % and RSS MB, plus `sample_cost_ms`. Report that t3.micro has 2 vCPUs and 1 GiB RAM so numbers are meaningful in context.
**Acceptance.** `analysis/overhead.csv` with one row per (config, rep).

### Phase 9 — Analysis and figures (A6, then A7)
Produce (PNG, 300 dpi, labeled axes, units, n in caption):
- F1 Timeline of S0 vs S2M: `syn_recv`, `established`, probe ok-rate (stacked, shared x-axis, event window shaded).
- F2 Same for S1M (flash crowd) — placed next to F1 for the "wedding vs prank" contrast.
- F3 Completion ratio distributions per scenario (box/violin).
- F4 Detection delay per attack scenario per detector.
- F5 False-alarm rate vs detection rate trade-off (parameter sweep curve), tuning vs test marked.
- F6 Mitigation effect: probe success with/without cookies.
- F7 Overhead bars (CPU %, RSS MB) per config.
- F8 S3 (connection flood): why completion ratio fails and what D2 adds.
Tables: T1 scenario matrix, T2 metrics summary (test set), T3 overhead, T4 ablation of D2 branches, T5 limitations.

### Phase 10 — Report (A7) and teardown (A1)
1. A7 writes `report/report.md`: abstract (use template below), problem, method, testbed, results (F1–F8, T1–T5), threats to validity, conclusion, reproduction steps. All numbers from `analysis/`; every figure cites the generating script.
2. **Threats to validity (MUST include):** single-source attacker IP (VPC blocks spoofing); single-source legitimate crowd; small instance and CPU-credit throttling; synthetic flash crowd (ab/wrk) not real users; one kernel/version; short runs; parameters tuned on lab data.
3. **Teardown (A1)** after human sign-off that all data is archived: terminate 3 instances; delete SG `lab-sg`; delete key pair + local `.pem`; remove nothing else. Verify with `aws ec2 describe-instances --filters Name=tag:Project,Values=tcp-flood-lab` (none running) and `describe-security-groups`/`describe-key-pairs`. Archive `runs/` and `infra/` to a tarball with checksums.

**Abstract template (fill brackets from data only):**
> TCP flooding attacks exhaust a server's connection resources and deny service to legitimate users. Edge devices cannot afford heavy packet inspection, and simple volume rules misclassify legitimate flash crowds. We propose a socket-level detector that reads the kernel's connection-state tables and alarms only when abnormal volume coincides with poor handshake completion, using an adaptive baseline. On an AWS testbed with normal traffic, flash crowds, SYN floods, connection floods, and floods hidden in crowds, it achieves [X]% detection with [Y]% false alarms on held-out runs and a median delay of [Z] s, using [N]% less CPU than a packet-level IDS. We also show that [finding on connection floods and SYN cookies].

---

## 7. Definition of done

- [ ] G1, G2 logged; no cap raised without G3
- [ ] Run matrix complete (or missing runs justified); `runs/INDEX.csv` valid
- [ ] Detector reproducible from raw CSVs with one command; parameters tuned on reps 1–3, reported on 4–5
- [ ] F1–F8, T1–T5 generated by scripts under `analysis/`
- [ ] `report/report.md` includes threats to validity and honest negative findings
- [ ] Teardown verified by CLI output saved to `infra/teardown_verification.txt`
- [ ] `STATE.md` shows all phases complete; `LAB_LOG.md` contains every deviation

---

## 8. Troubleshooting quick table

| Symptom | Likely cause | Action |
|---|---|---|
| SSH hangs | operator IP changed | update SG SSH rule to new `/32` |
| `syn_recv` never rises during SYN flood | attacker RST not suppressed, or guard blocked tool | check `iptables -S OUTPUT` on attacker; read `attack_attacker.txt` |
| Probes all fail even in S0 | nginx down / wrong IP / SG rule | `systemctl status nginx`; use **private** IP |
| `ab` errors "Address already in use" / socket exhaustion | client ephemeral ports | lower concurrency; widen `ip_local_port_range`; log |
| Metrics rows missing/irregular | sampler overloaded | check `sample_cost_ms`; ensure monotonic pacing; lower Hz |
| Runs vary wildly | t3 CPU credit throttling | record `CPUCreditBalance`; add longer idle between runs; log as limitation |
| Flood has no visible effect | rate capped far below capacity | do NOT raise caps; report the effect level honestly; ask human (G3) |
| Counter missing from `/proc/net/netstat` | kernel version | leave column empty; list in `handoffs/A3.md` |

---

## 9. Sub-agent prompt headers (A0 SHOULD paste the relevant one when spawning)

**A1 Infra:** "You own AWS resources for tcp-flood-lab. Follow AGENTS.md Phase 1 and Phase 10 and Section 4 exactly. Never create a public ingress rule except SSH from my `/32`. Output `lab.env` and `handoffs/A1.md`. Stop at any 4.4 condition."

**A3 Collector:** "Implement `sampler.py`, `probe.sh`, `collect.sh` per 5.5, 5.6, Phase 3. Stdlib only. Meet the acceptance checks. Output `handoffs/A3.md` including counter availability."

**A4 Traffic:** "Implement attack guard, generators, calibration per Phase 4 and 4.2. Prove the guard refuses out-of-scope input before anything else. Stop for human gate G2."

**A5 Runner:** "Execute Phase 5 and Phase 8 serially per the run matrix and per-run procedure. Never start two runs concurrently. Record anomalies in `notes.md`. Do not change parameters to match expectations."

**A6 Detector/Analysis:** "Implement B1, D1, D2 (and D3 if time) per Phase 6 with the train/test protocol. Compute metrics exactly as defined. Report negative results honestly."

**A7 Reporter:** "Write the report from files under `analysis/` only. Include threats to validity and the abstract template filled from data."