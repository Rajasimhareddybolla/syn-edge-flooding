#!/usr/bin/env python3
"""
tools/matrix_runner.py — Master serial experiment matrix runner.
Reference: docs/AGENTS_tcp_flood_lab.md §5.1, §5.2, §5.3

Executes 65 serial runs across 13 scenarios x 5 repetitions:
  S0, S1S, S1M, S1L, S2L, S2M, S2H, S3L, S3M, S3H, S4, S5M, S5H

Enforces:
  1. Strict serial execution (never parallel).
  2. Blocked randomization (rep 1 block shuffled, rep 2 block shuffled, etc.) with logged seed.
  3. Header-only snaplen pcap on rep 1 of each scenario.
  4. Resumability: skips runs already successfully recorded in runs/INDEX.csv.
  5. Automatic recovery and SG IP refresh on transient network drops.
"""

from __future__ import annotations

import csv
import os
import random
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / "runs"
INDEX_PATH = RUNS_DIR / "INDEX.csv"
SEED = 20261007

SCENARIOS = [
    "S0",
    "S1S", "S1M", "S1L",
    "S2L", "S2M", "S2H",
    "S3L", "S3M", "S3H",
    "S4",
    "S5M", "S5H",
]


def load_completed_runs() -> set[tuple[str, int]]:
    """Return set of (scenario, rep) that finished successfully."""
    completed = set()
    if not INDEX_PATH.exists():
        return completed
    with open(INDEX_PATH, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("aborted", "").lower() != "true":
                scen = row.get("scenario", "")
                rep_str = row.get("rep", "")
                if scen and rep_str:
                    try:
                        completed.add((scen, int(rep_str)))
                    except ValueError:
                        pass
    return completed


def generate_schedule(seed: int = SEED) -> list[tuple[str, int, bool]]:
    """
    Generate randomized block schedule.
    Returns list of (scenario, rep, do_pcap).
    """
    rng = random.Random(seed)
    schedule: list[tuple[str, int, bool]] = []
    for rep in range(1, 6):
        block = list(SCENARIOS)
        rng.shuffle(block)
        for scen in block:
            do_pcap = (rep == 1)
            schedule.append((scen, rep, do_pcap))
    return schedule


def ensure_sg_reachability() -> None:
    """Run infra/update_sg_ip.sh to ensure operator IP is authorized."""
    sg_script = REPO_ROOT / "infra" / "update_sg_ip.sh"
    if sg_script.exists():
        try:
            subprocess.run(["bash", str(sg_script)], cwd=str(REPO_ROOT), timeout=15, check=False)
        except Exception as e:
            print(f"[matrix_runner] SG update check warning: {e}", file=sys.stderr)


def run_single(scenario: str, rep: int, do_pcap: bool) -> bool:
    """Execute a single scenario run via tools/run_scenario.sh."""
    cmd = ["bash", "tools/run_scenario.sh", scenario, str(rep)]
    if do_pcap:
        cmd.append("--pcap")

    print(f"\n================================================================================")
    print(f"[matrix_runner] Launching {scenario} (Rep {rep}/5, PCAP={do_pcap})")
    print(f"Command: {' '.join(cmd)}")
    print(f"================================================================================")

    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        ret = subprocess.run(cmd, cwd=str(REPO_ROOT))
        if ret.returncode == 0:
            print(f"[matrix_runner] ✅ Run {scenario} rep {rep} completed successfully.")
            return True
        else:
            print(f"[matrix_runner] ⚠️ Run {scenario} rep {rep} exited with code {ret.returncode} (attempt {attempt}/{max_attempts})")
            if attempt < max_attempts:
                print(f"[matrix_runner] Refreshing security group IP and retrying in 10s...")
                ensure_sg_reachability()
                time.sleep(10)

    print(f"[matrix_runner] ❌ Run {scenario} rep {rep} failed after {max_attempts} attempts.")
    return False


def main() -> None:
    schedule = generate_schedule(SEED)
    completed = load_completed_runs()

    total_runs = len(schedule)
    remaining = [item for item in schedule if (item[0], item[1]) not in completed]

    print(f"================================================================================")
    print(f"Matrix Runner Initialized | Seed: {SEED}")
    print(f"Total Planned Runs: {total_runs} (13 scenarios x 5 reps)")
    print(f"Already Completed:  {len(completed)}")
    print(f"Remaining Runs:     {len(remaining)}")
    print(f"================================================================================")

    for idx, (scenario, rep, do_pcap) in enumerate(schedule, 1):
        if (scenario, rep) in completed:
            print(f"[{idx:02d}/{total_runs:02d}] Skipping {scenario} rep {rep} (already completed)")
            continue

        print(f"\n[{idx:02d}/{total_runs:02d}] Starting {scenario} rep {rep} ...")
        success = run_single(scenario, rep, do_pcap)
        if not success:
            print(f"[matrix_runner] FATAL: Stopping matrix on failed run {scenario} rep {rep}.", file=sys.stderr)
            sys.exit(1)

        # Update completed set
        completed.add((scenario, rep))

        # Cooldown between runs
        print(f"[matrix_runner] Run complete. Pausing 5s before next run...")
        time.sleep(5)

    print("\n================================================================================")
    print("🎉 ALL 65 MATRIX RUNS COMPLETED SUCCESSFULLY!")
    print("================================================================================")


if __name__ == "__main__":
    main()

