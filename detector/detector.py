#!/usr/bin/env python3
"""
detector.py — Lightweight socket-state detector implementations.

Detectors:
  B1  — Baseline volume threshold: triggers when syn_recv >= threshold.
  D1  — Adaptive EWMA dual-signal: EWMA of half-open volume + handshake
         completion ratio (HCR). Alert when volume is elevated AND completion
         ratio collapses (discriminates attacks from flash crowds).
  D2  — Extended: adds connection flood branch (ESTABLISHED surge + source concentration)
         and SYN-cookie mitigation branch (d_syncookies_sent spike).

All detectors follow the same interface:
  detector = DetectorXX(params)
  label, score = detector.step(row: dict) -> (int, float)
    label: 1 = alert, 0 = normal
    score: continuous anomaly score (for ROC analysis)

Reference: docs/AGENTS_tcp_flood_lab.md §5.6, §5.7, §6.2, §6.3
"""

from __future__ import annotations
import math
from typing import Any


# ---------------------------------------------------------------------------
# B1 — Baseline Volume Threshold
# ---------------------------------------------------------------------------

class B1Detector:
    """
    Baseline volume detector.
    Alert when syn_recv exceeds a fixed threshold.

    Params (dict):
        threshold (int): SYN queue count trigger level. Default 48.
    """

    NAME = "B1"
    PARAM_SPACE: dict[str, list] = {
        "threshold": [16, 32, 48, 64, 80, 96, 112, 128],
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self.threshold: int = int(p.get("threshold", 48))

    def step(self, row: dict[str, Any]) -> tuple[int, float]:
        val = float(row.get("syn_recv", 0) or row.get("syn_queue_cur", 0) or 0)
        score = val / max(self.threshold, 1)
        label = 1 if val >= self.threshold else 0
        return label, score

    def reset(self) -> None:
        pass  # stateless


# ---------------------------------------------------------------------------
# D1 — Adaptive EWMA Dual-Signal Detector
# ---------------------------------------------------------------------------

class D1Detector:
    """
    Adaptive dual-signal detector.

    Signal 1 — Half-open volume: EWMA of syn_recv.
    Signal 2 — Handshake completion ratio (HCR):
                HCR = d_passive_opens / max(1, d_passive_opens + d_listen_drops + d_attempt_fails + syn_recv)
                A low HCR indicates uncompleted or dropped connection attempts.

    Alert when BOTH:
        (vol_ewma is elevated beyond adaptive threshold) AND
        (hcr_ewma drops below completion ratio threshold tau)

    Baseline updates are frozen during alarm states to prevent poison adaptation.

    Params (dict):
        alpha        (float): EWMA smoothing factor. Default 0.2.
        k_vol        (float): Sigma multiplier for volume. Default 3.0.
        tau          (float): Completion ratio floor. Default 0.98.
        floor        (float): Minimum absolute half-open volume floor. Default 20.0.
        warmup_steps (int):   Initial steps to establish baseline stats. Default 20.
    """

    NAME = "D1"
    PARAM_SPACE: dict[str, list] = {
        "alpha":        [0.1, 0.2, 0.3],
        "k_vol":        [2.5, 3.0, 3.5],
        "tau":          [0.90, 0.95, 0.98],
        "floor":        [15.0, 20.0, 30.0],
        "warmup_steps": [20, 30],
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self.alpha: float = float(p.get("alpha", 0.2))
        self.k_vol: float = float(p.get("k_vol", 3.0))
        self.tau: float = float(p.get("tau", 0.98))
        self.floor: float = float(p.get("floor", 20.0))
        self.warmup_steps: int = int(p.get("warmup_steps", 20))
        self._reset_state()

    def _reset_state(self) -> None:
        self._step = 0
        self._in_alarm = False
        # EWMA values
        self._vol_ewma: float = 0.0
        self._hcr_ewma: float = 1.0
        # Welford online stats for volume baseline estimation
        self._vol_n = 0
        self._vol_mean = 0.0
        self._vol_M2 = 0.0
        # Frozen baseline (post-warmup)
        self._vol_mu: float | None = None
        self._vol_sigma: float | None = None

    def reset(self) -> None:
        self._reset_state()

    @staticmethod
    def _welford_update(n: int, mean: float, M2: float,
                        x: float) -> tuple[int, float, float]:
        n += 1
        delta = x - mean
        mean += delta / n
        delta2 = x - mean
        M2 += delta * delta2
        return n, mean, M2

    @staticmethod
    def _welford_std(n: int, M2: float) -> float:
        if n < 2:
            return 1.0
        return math.sqrt(M2 / (n - 1))

    def step(self, row: dict[str, Any]) -> tuple[int, float]:
        vol = float(row.get("syn_recv", 0) or row.get("syn_queue_cur", 0) or 0)
        po = float(row.get("d_passive_opens", 0) or 0)
        drops = float(row.get("d_listen_drops", 0) or 0)
        af = float(row.get("d_attempt_fails", 0) or 0)

        # Handshake completion ratio
        denom = po + drops + af + vol
        hcr = po / denom if denom > 0 else 1.0

        # Update EWMAs
        if self._step == 0:
            self._vol_ewma = vol
            self._hcr_ewma = hcr
        else:
            self._vol_ewma = self.alpha * vol + (1 - self.alpha) * self._vol_ewma
            self._hcr_ewma = self.alpha * hcr + (1 - self.alpha) * self._hcr_ewma

        self._step += 1

        # During warmup: update baseline stats and return 0
        if self._vol_mu is None:
            self._vol_n, self._vol_mean, self._vol_M2 = self._welford_update(
                self._vol_n, self._vol_mean, self._vol_M2, self._vol_ewma)
            if self._step >= self.warmup_steps:
                self._vol_mu = self._vol_mean
                self._vol_sigma = max(self._welford_std(self._vol_n, self._vol_M2), 1.0)
            return 0, 0.0

        # Check conditions
        vol_elevated = (self._vol_ewma > (self._vol_mu + self.k_vol * self._vol_sigma)) or (self._vol_ewma >= self.floor)
        hcr_depressed = (self._hcr_ewma <= self.tau)

        # Dual-signal trigger: BOTH volume elevated AND HCR depressed
        label = 1 if (vol_elevated and hcr_depressed) else 0

        # Freeze baseline while in alarm to prevent poison adaptation
        if label == 0:
            # Calm step: adapt slowly
            self._vol_n, self._vol_mean, self._vol_M2 = self._welford_update(
                self._vol_n, self._vol_mean, self._vol_M2, self._vol_ewma)
            self._vol_mu = self._vol_mean
            self._vol_sigma = max(self._welford_std(self._vol_n, self._vol_M2), 1.0)

        vol_score = max(0.0, (self._vol_ewma - self._vol_mu) / (self.k_vol * self._vol_sigma))
        hcr_score = max(0.0, (1.0 - self._hcr_ewma) / max(1.0 - self.tau, 0.01))
        # Anomaly score: joint exceedance
        score = min(vol_score, hcr_score) if (vol_elevated and hcr_depressed) else (vol_score * 0.1)

        return label, score


# ---------------------------------------------------------------------------
# D2 — Extended: Connection Flood + Mitigation Branches
# ---------------------------------------------------------------------------

class D2Detector:
    """
    Extended detector building on D1.

    Branches:
      Branch 1: D1 dual-signal (half-open volume + HCR for SYN floods)
      Branch 2: Connection flood branch:
                ESTABLISHED socket surge with high single-source concentration (top_src_share).
      Branch 3: Mitigation branch (SYN cookies):
                d_syncookies_sent surge indicating kernel defense active.

    Final alert = Branch 1 OR Branch 2 OR Branch 3.
    """

    NAME = "D2"
    PARAM_SPACE: dict[str, list] = {
        "alpha":         [0.1, 0.2, 0.3],
        "k_vol":         [2.5, 3.0, 3.5],
        "tau":           [0.90, 0.95, 0.98],
        "floor":         [15.0, 20.0, 30.0],
        "estab_thresh":  [50.0, 75.0, 100.0],
        "src_share_min": [0.70, 0.80],
        "cookie_thresh": [30.0, 50.0, 100.0],
        "warmup_steps":  [20, 30],
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self.alpha: float = float(p.get("alpha", 0.2))
        self.estab_thresh: float = float(p.get("estab_thresh", 75.0))
        self.src_share_min: float = float(p.get("src_share_min", 0.70))
        self.cookie_thresh: float = float(p.get("cookie_thresh", 50.0))
        self._d1 = D1Detector(params)
        self._reset_extra()

    def _reset_extra(self) -> None:
        self._step = 0
        self._estab_ewma: float = 0.0
        self._cookies_ewma: float = 0.0

    def reset(self) -> None:
        self._d1.reset()
        self._reset_extra()

    def step(self, row: dict[str, Any]) -> tuple[int, float]:
        d1_label, d1_score = self._d1.step(row)

        estab = float(row.get("established", 0) or 0)
        src_share = float(row.get("top_src_share", 0) or 0)
        cookies = float(row.get("d_syncookies_sent", 0) or 0)

        if self._step == 0:
            self._estab_ewma = estab
            self._cookies_ewma = cookies
        else:
            self._estab_ewma = self.alpha * estab + (1 - self.alpha) * self._estab_ewma
            self._cookies_ewma = self.alpha * cookies + (1 - self.alpha) * self._cookies_ewma

        self._step += 1

        # Branch 2: Connection flood
        conn_alert = (self._estab_ewma >= self.estab_thresh and src_share >= self.src_share_min)
        conn_score = (self._estab_ewma / self.estab_thresh) if src_share >= self.src_share_min else 0.0

        # Branch 3: SYN Cookie mitigation
        cookie_alert = (self._cookies_ewma >= self.cookie_thresh)
        cookie_score = (self._cookies_ewma / self.cookie_thresh)

        label = 1 if (d1_label or conn_alert or cookie_alert) else 0
        score = max(d1_score, conn_score, cookie_score)

        return label, score


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

DETECTORS = {
    "B1": B1Detector,
    "D1": D1Detector,
    "D2": D2Detector,
}


def make_detector(name: str, params: dict | None = None):
    cls = DETECTORS.get(name.upper())
    if cls is None:
        raise ValueError(f"Unknown detector '{name}'. Choose from: {list(DETECTORS)}")
    return cls(params)
