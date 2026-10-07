#!/usr/bin/env python3
"""
tools/sampler.py — Socket-state sampler for TCP flood detection research.
Reads /proc/net/tcp (and tcp6), /proc/net/snmp, /proc/net/netstat, /proc/stat,
/proc/meminfo once per second on a monotonic schedule, emits one CSV row per §5.5.

Usage:
  python3 sampler.py --out metrics.csv [--hz 1] [--method {proc,ss}]

Stdlib only — no psutil or third-party packages.
"""
import argparse
import csv
import os
import re
import select
import subprocess
import sys
import time

# CSV columns per §5.5
COLUMNS = [
    "ts_ms",
    "syn_recv", "established", "time_wait", "close_wait",
    "fin_wait", "last_ack", "listen_q",
    "top_src_share", "n_distinct_src",
    "d_passive_opens", "d_attempt_fails", "d_estab_resets", "d_retrans",
    "d_listen_overflows", "d_listen_drops",
    "d_syncookies_sent", "d_syncookies_recv", "d_syncookies_failed",
    "d_reqq_full_cookies", "d_reqq_full_drop",
    "cpu_pct", "mem_used_mb", "sample_cost_ms",
]

# TCP state hex codes → field names
TCP_STATE_MAP = {
    "01": "established",
    "03": "syn_recv",
    "06": "time_wait",
    "08": "close_wait",
    "05": "fin_wait",    # FIN_WAIT1
    "07": "fin_wait",    # CLOSE (use fin_wait bucket)
    "09": "last_ack",
    "0A": "listen_q",   # LISTEN
    "0B": "listen_q",   # CLOSING
}


def read_proc_tcp(port_hex="0050"):
    """Parse /proc/net/tcp for port 80 (0x0050) sockets. Returns state counts and src IPs."""
    state_counts = {
        "established": 0, "syn_recv": 0, "time_wait": 0,
        "close_wait": 0, "fin_wait": 0, "last_ack": 0, "listen_q": 0,
    }
    src_ips = []
    for proc_file in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(proc_file) as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 12:
                        continue
                    local_addr = parts[1]
                    rem_addr = parts[2]
                    state_hex = parts[3].upper()
                    # local_port is last 4 chars of local_addr (hex)
                    local_port = local_addr.split(":")[1].upper() if ":" in local_addr else ""
                    if local_port != port_hex.upper():
                        continue
                    state_name = TCP_STATE_MAP.get(state_hex)
                    if state_name:
                        state_counts[state_name] = state_counts.get(state_name, 0) + 1
                    # Collect remote IP for non-LISTEN
                    if state_hex != "0A":
                        rem_ip_hex = rem_addr.split(":")[0] if ":" in rem_addr else rem_addr
                        # Convert little-endian hex IP to dotted
                        try:
                            if len(rem_ip_hex) == 8:
                                b = bytes.fromhex(rem_ip_hex)
                                ip_str = f"{b[3]}.{b[2]}.{b[1]}.{b[0]}"
                                src_ips.append(ip_str)
                        except Exception:
                            pass
        except FileNotFoundError:
            pass
    return state_counts, src_ips


def read_snmp_counters():
    """Read /proc/net/snmp Tcp row. Returns dict of counter names->values."""
    result = {}
    try:
        with open("/proc/net/snmp") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith("Tcp:") and i + 1 < len(lines):
                keys = line.split()[1:]
                vals = lines[i + 1].split()[1:]
                for k, v in zip(keys, vals):
                    result[k] = int(v)
                break
    except Exception:
        pass
    return result


def read_netstat_counters():
    """Read /proc/net/netstat TcpExt row. Returns dict."""
    result = {}
    try:
        with open("/proc/net/netstat") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith("TcpExt:") and i + 1 < len(lines):
                keys = line.split()[1:]
                vals = lines[i + 1].split()[1:]
                for k, v in zip(keys, vals):
                    result[k] = int(v)
                break
    except Exception:
        pass
    return result


def read_cpu_mem():
    """Read CPU% (from /proc/stat delta) and used memory MB from /proc/meminfo."""
    cpu_pct = None
    mem_used_mb = None
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = line.split()
        # user nice system idle iowait irq softirq steal guest guest_nice
        idle = int(parts[4])
        total = sum(int(x) for x in parts[1:])
        cpu_pct = (idle, total)  # return raw for delta
    except Exception:
        pass
    try:
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                meminfo[k.strip()] = int(v.strip().split()[0])
        mem_total = meminfo.get("MemTotal", 0)
        mem_avail = meminfo.get("MemAvailable", 0)
        mem_used_mb = (mem_total - mem_avail) / 1024.0
    except Exception:
        pass
    return cpu_pct, mem_used_mb


def read_ss_method():
    """Shell out to ss -tan and parse state counts for port 80."""
    state_counts = {
        "established": 0, "syn_recv": 0, "time_wait": 0,
        "close_wait": 0, "fin_wait": 0, "last_ack": 0, "listen_q": 0,
    }
    src_ips = []
    try:
        out = subprocess.check_output(
            ["ss", "-tan"], timeout=5, stderr=subprocess.DEVNULL
        ).decode()
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 5:
                continue
            state = parts[0].lower()
            local = parts[3]
            if ":80" not in local:
                continue
            if state == "estab":
                state_counts["established"] += 1
                remote = parts[4].rsplit(":", 1)[0].strip("[]")
                src_ips.append(remote)
            elif state == "syn-recv":
                state_counts["syn_recv"] += 1
            elif state == "time-wait":
                state_counts["time_wait"] += 1
            elif state == "close-wait":
                state_counts["close_wait"] += 1
            elif state in ("fin-wait-1", "fin-wait-2"):
                state_counts["fin_wait"] += 1
            elif state == "last-ack":
                state_counts["last_ack"] += 1
            elif state == "listen":
                state_counts["listen_q"] += 1
    except Exception:
        pass
    return state_counts, src_ips


def delta(new, old, key):
    """Return delta of counter, or empty string if key missing."""
    if key not in new or key not in old:
        return ""
    return new[key] - old[key]


def main():
    parser = argparse.ArgumentParser(description="TCP socket-state sampler")
    parser.add_argument("--out", required=True, help="Output CSV file path")
    parser.add_argument("--hz", type=float, default=1.0, help="Sampling frequency (default 1)")
    parser.add_argument("--method", choices=["proc", "ss"], default="proc",
                        help="Sampling method: proc (default) or ss")
    args = parser.parse_args()

    interval = 1.0 / args.hz
    use_ss = args.method == "ss"

    # Initialize previous counters
    prev_snmp = read_snmp_counters()
    prev_netstat = read_netstat_counters()
    prev_cpu, _ = read_cpu_mem()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True) if os.path.dirname(args.out) else None

    with open(args.out, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        csvfile.flush()

        next_tick = time.monotonic() + interval
        while True:
            t0 = time.monotonic()
            ts_ms = int(time.time() * 1000)

            # Read state + source IPs
            if use_ss:
                state_counts, src_ips = read_ss_method()
            else:
                state_counts, src_ips = read_proc_tcp()

            # Source concentration
            n_distinct = len(set(src_ips))
            if src_ips:
                from collections import Counter
                top_count = Counter(src_ips).most_common(1)[0][1]
                top_src_share = round(top_count / len(src_ips), 4)
            else:
                top_src_share = 0.0

            # SNMP + netstat deltas
            cur_snmp = read_snmp_counters()
            cur_netstat = read_netstat_counters()
            cur_cpu, mem_used_mb = read_cpu_mem()

            # CPU %
            cpu_pct = ""
            if cur_cpu and prev_cpu:
                d_idle = cur_cpu[0] - prev_cpu[0]
                d_total = cur_cpu[1] - prev_cpu[1]
                if d_total > 0:
                    cpu_pct = round(100.0 * (1.0 - d_idle / d_total), 2)

            sample_cost_ms = round((time.monotonic() - t0) * 1000, 2)

            row = {
                "ts_ms": ts_ms,
                "syn_recv": state_counts.get("syn_recv", 0),
                "established": state_counts.get("established", 0),
                "time_wait": state_counts.get("time_wait", 0),
                "close_wait": state_counts.get("close_wait", 0),
                "fin_wait": state_counts.get("fin_wait", 0),
                "last_ack": state_counts.get("last_ack", 0),
                "listen_q": state_counts.get("listen_q", 0),
                "top_src_share": top_src_share,
                "n_distinct_src": n_distinct,
                "d_passive_opens": delta(cur_snmp, prev_snmp, "PassiveOpens"),
                "d_attempt_fails": delta(cur_snmp, prev_snmp, "AttemptFails"),
                "d_estab_resets": delta(cur_snmp, prev_snmp, "EstabResets"),
                "d_retrans": delta(cur_snmp, prev_snmp, "RetransSegs"),
                "d_listen_overflows": delta(cur_netstat, prev_netstat, "ListenOverflows"),
                "d_listen_drops": delta(cur_netstat, prev_netstat, "ListenDrops"),
                "d_syncookies_sent": delta(cur_netstat, prev_netstat, "SyncookiesSent"),
                "d_syncookies_recv": delta(cur_netstat, prev_netstat, "SyncookiesRecv"),
                "d_syncookies_failed": delta(cur_netstat, prev_netstat, "SyncookiesFailed"),
                "d_reqq_full_cookies": delta(cur_netstat, prev_netstat, "TCPReqQFullDoCookies"),
                "d_reqq_full_drop": delta(cur_netstat, prev_netstat, "TCPReqQFullDrop"),
                "cpu_pct": cpu_pct,
                "mem_used_mb": round(mem_used_mb, 1) if mem_used_mb is not None else "",
                "sample_cost_ms": sample_cost_ms,
            }
            writer.writerow(row)
            csvfile.flush()

            prev_snmp = cur_snmp
            prev_netstat = cur_netstat
            prev_cpu = cur_cpu

            # Monotonic sleep until next tick
            now = time.monotonic()
            sleep_for = next_tick - now
            next_tick += interval
            if sleep_for > 0:
                time.sleep(sleep_for)


if __name__ == "__main__":
    main()

