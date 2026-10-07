#!/usr/bin/env python3
"""
replay.py — Offline detector replay and benchmarking over experiment runs.

Usage:
    python3 replay.py --runs-dir runs/ --out-dir analysis/ [--tune-reps 1,2,3] [--eval-reps 4,5]

Steps:
  1. Load all runs from runs/INDEX.csv.
  2. Split into tune set (reps 1–3) and eval set (reps 4–5).
  3. Grid-search each detector's PARAM_SPACE on tune set (maximize F1).
  4. Evaluate best params on eval set → compute Precision, Recall, F1, FPR, AUC-ROC.
  5. Compute per-overhead delta vs baseline.
  6. Write analysis/metrics.csv and analysis/overhead.csv.

Ground truth: label=1 during [event_start_ts, event_end_ts] from events.json.

Reference: docs/AGENTS_tcp_flood_lab.md §5.7, §5.8
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


# ── local import ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from detector import make_detector, DETECTORS


# ── helpers ───────────────────────────────────────────────────────────────────

def load_index(runs_dir: Path) -> list[dict]:
    index_path = runs_dir / "INDEX.csv"
    if not index_path.exists():
        raise FileNotFoundError(f"runs/INDEX.csv not found at {index_path}")
    with open(index_path) as f:
        return list(csv.DictReader(f))


def load_run(run_dir: Path) -> tuple[list[dict], dict]:
    """Return (metric_rows, events_dict)."""
    metrics_path = run_dir / "victim_metrics.csv"
    events_path = run_dir / "events.json"

    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing {metrics_path}")
    if not events_path.exists():
        raise FileNotFoundError(f"Missing {events_path}")

    with open(metrics_path) as f:
        rows = list(csv.DictReader(f))
    with open(events_path) as f:
        events = json.load(f)
    return rows, events


def make_ground_truth(rows: list[dict], events: dict) -> list[int]:
    """
    Return per-row label (1=attack, 0=normal).
    Attack window: events['event_start_ts'] .. events['event_end_ts'].
    ts column: 'ts_ms' (epoch milliseconds).
    """
    start_ms = float(events.get("event_start_ts_ms", 0) or 0)
    end_ms = float(events.get("event_end_ts_ms", float("inf")) or float("inf"))

    labels = []
    for row in rows:
        ts = float(row.get("ts_ms", 0) or 0)
        labels.append(1 if start_ms <= ts <= end_ms else 0)
    return labels


def run_detector(det, rows: list[dict]) -> tuple[list[int], list[float]]:
    det.reset()
    preds, scores = [], []
    for row in rows:
        label, score = det.step(row)
        preds.append(label)
        scores.append(score)
    return preds, scores


def precision_recall_f1(preds: list[int], truth: list[int]) -> tuple[float, float, float]:
    tp = sum(p == 1 and t == 1 for p, t in zip(preds, truth))
    fp = sum(p == 1 and t == 0 for p, t in zip(preds, truth))
    fn = sum(p == 0 and t == 1 for p, t in zip(preds, truth))
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def fpr_score(preds: list[int], truth: list[int]) -> float:
    fp = sum(p == 1 and t == 0 for p, t in zip(preds, truth))
    tn = sum(p == 0 and t == 0 for p, t in zip(preds, truth))
    return fp / (fp + tn) if (fp + tn) else 0.0


def auc_roc(scores: list[float], truth: list[int]) -> float:
    """Trapezoidal AUC-ROC."""
    pairs = sorted(zip(scores, truth), key=lambda x: -x[0])
    pos = sum(truth)
    neg = len(truth) - pos
    if pos == 0 or neg == 0:
        return float("nan")
    tpr_pts, fpr_pts = [0.0], [0.0]
    tp = fp = 0
    prev_score = None
    for score, label in pairs:
        if score != prev_score and prev_score is not None:
            tpr_pts.append(tp / pos)
            fpr_pts.append(fp / neg)
        if label == 1:
            tp += 1
        else:
            fp += 1
        prev_score = score
    tpr_pts.append(tp / pos)
    fpr_pts.append(fp / neg)
    # trapezoidal
    auc = 0.0
    for i in range(1, len(fpr_pts)):
        auc += (fpr_pts[i] - fpr_pts[i - 1]) * (tpr_pts[i] + tpr_pts[i - 1]) / 2
    return abs(auc)


def param_combinations(param_space: dict) -> list[dict]:
    keys = list(param_space.keys())
    values = list(param_space.values())
    combos = []
    for vals in itertools.product(*values):
        combos.append(dict(zip(keys, vals)))
    return combos


# ── grid search ───────────────────────────────────────────────────────────────

def grid_search(det_name: str, tune_runs: list[tuple[list[dict], dict]]) -> dict:
    """Return best params maximizing mean F1 on tune_runs."""
    cls = DETECTORS[det_name]
    best_params = {}
    best_f1 = -1.0
    for params in param_combinations(cls.PARAM_SPACE):
        det = make_detector(det_name, params)
        f1s = []
        for rows, events in tune_runs:
            truth = make_ground_truth(rows, events)
            preds, _ = run_detector(det, rows)
            _, _, f1 = precision_recall_f1(preds, truth)
            f1s.append(f1)
        mean_f1 = sum(f1s) / len(f1s) if f1s else 0.0
        if mean_f1 > best_f1:
            best_f1 = mean_f1
            best_params = params
    return best_params


# ── evaluation ────────────────────────────────────────────────────────────────

def evaluate(det_name: str, params: dict,
             eval_runs: list[tuple[list[dict], dict]]) -> dict:
    """Return per-run and aggregate metrics."""
    det = make_detector(det_name, params)
    all_preds, all_truth, all_scores = [], [], []
    run_rows = []
    for rows, events in eval_runs:
        truth = make_ground_truth(rows, events)
        preds, scores = run_detector(det, rows)
        all_preds.extend(preds)
        all_truth.extend(truth)
        all_scores.extend(scores)
        prec, rec, f1 = precision_recall_f1(preds, truth)
        run_rows.append({"prec": prec, "rec": rec, "f1": f1})

    agg_prec, agg_rec, agg_f1 = precision_recall_f1(all_preds, all_truth)
    agg_fpr = fpr_score(all_preds, all_truth)
    agg_auc = auc_roc(all_scores, all_truth)

    return {
        "precision": agg_prec,
        "recall": agg_rec,
        "f1": agg_f1,
        "fpr": agg_fpr,
        "auc_roc": agg_auc,
        "run_rows": run_rows,
        "params": params,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Offline detector replay and benchmarking")
    ap.add_argument("--runs-dir", default="runs/", help="Directory containing INDEX.csv and run subdirs")
    ap.add_argument("--out-dir", default="analysis/", help="Output directory for metrics CSV files")
    ap.add_argument("--tune-reps", default="1,2,3", help="Comma-separated rep numbers for tuning")
    ap.add_argument("--eval-reps", default="4,5", help="Comma-separated rep numbers for evaluation")
    ap.add_argument("--scenario", default=None, help="Filter to specific scenario (e.g. S2L)")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tune_reps = set(int(r) for r in args.tune_reps.split(","))
    eval_reps = set(int(r) for r in args.eval_reps.split(","))

    print(f"Loading index from {runs_dir}/INDEX.csv ...")
    index = load_index(runs_dir)

    if args.scenario:
        index = [r for r in index if r.get("scenario") == args.scenario]
        print(f"  Filtered to scenario '{args.scenario}': {len(index)} runs")

    # Group runs by scenario and rep
    tune_data: list[tuple[list[dict], dict]] = []
    eval_data: list[tuple[list[dict], dict]] = []

    for entry in index:
        rep = int(entry.get("rep", 0))
        run_id = entry.get("run_id", "")
        run_dir = runs_dir / run_id
        try:
            rows, events = load_run(run_dir)
        except FileNotFoundError as e:
            print(f"  WARNING: Skipping {run_id}: {e}", file=sys.stderr)
            continue
        if rep in tune_reps:
            tune_data.append((rows, events))
        elif rep in eval_reps:
            eval_data.append((rows, events))

    print(f"  Tune runs: {len(tune_data)}, Eval runs: {len(eval_data)}")

    if not tune_data:
        print("ERROR: No tune data found. Check INDEX.csv rep columns.", file=sys.stderr)
        sys.exit(1)
    if not eval_data:
        print("ERROR: No eval data found. Check INDEX.csv rep columns.", file=sys.stderr)
        sys.exit(1)

    # Run grid search + evaluation for each detector
    metrics_rows = []
    print("\nGrid searching detectors on tune set ...")
    for det_name in ["B1", "D1", "D2"]:
        print(f"  {det_name}: grid search ({len(param_combinations(DETECTORS[det_name].PARAM_SPACE))} combos) ...")
        best_params = grid_search(det_name, tune_data)
        print(f"    Best params: {best_params}")

        print(f"  {det_name}: evaluating on eval set ...")
        result = evaluate(det_name, best_params, eval_data)
        row = {
            "detector": det_name,
            "precision": f"{result['precision']:.4f}",
            "recall": f"{result['recall']:.4f}",
            "f1": f"{result['f1']:.4f}",
            "fpr": f"{result['fpr']:.4f}",
            "auc_roc": f"{result['auc_roc']:.4f}" if not math.isnan(result['auc_roc']) else "nan",
            **{f"param_{k}": v for k, v in best_params.items()},
        }
        metrics_rows.append(row)
        print(f"    F1={result['f1']:.3f}  Prec={result['precision']:.3f}  "
              f"Rec={result['recall']:.3f}  FPR={result['fpr']:.3f}  "
              f"AUC={result['auc_roc']:.3f}")

    # Write metrics CSV
    metrics_path = out_dir / "metrics.csv"
    all_keys: list[str] = []
    for r in metrics_rows:
        for k in r:
            if k not in all_keys:
                all_keys.append(k)
    with open(metrics_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(metrics_rows)
    print(f"\nMetrics written to {metrics_path}")

    # Overhead placeholder (will be filled from pidstat traces in collect.sh output)
    overhead_path = out_dir / "overhead.csv"
    if not overhead_path.exists():
        with open(overhead_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "run_id", "scenario", "rep", "detector",
                "cpu_mean_pct", "rss_mean_kb", "wall_ms_per_sample"
            ])
            writer.writeheader()
        print(f"Overhead placeholder written to {overhead_path}")


if __name__ == "__main__":
    main()

