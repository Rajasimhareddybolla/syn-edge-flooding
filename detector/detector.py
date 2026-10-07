#!/usr/bin/env python3
"""
detector.py — Lightweight socket-state detector implementations.

Detectors:
  B1  — Baseline volume threshold: triggers when syn_queue > threshold.
  D1  — Adaptive EWMA dual-signal: EWMA of half-open volume + handshake
         completion ratio (HCR). Alert when either signal deviates beyond
         adaptive threshold.
  D2  — Extended: adds connection flood branch (CLOSE_WAIT / TIME_WAIT surge)
         and SYN-cookie mitigation branch (SYNcookies sent spike).

All detectors follow the same interface:
  detector = DetectorXX(params)
  label, score = detector.step(row: dict) -> (int, float)
    label: 1 = alert, 0 = normal
    score: continuous anomaly score (for ROC analysis)

Reference: docs/AGENTS_tcp_flood_lab.md §5.6, §5.7
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
    Alert when syn_queue_cur exceeds a fixed threshold.

    Params (dict):
        threshold (int): SYN queue count trigger level. Default 64.
    """

    NAME = "B1"
    PARAM_SPACE: dict[str, list] = {
        "threshold": [16, 32, 48, 64, 80, 96, 112, 128],
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self.threshold: int = int(p.get("threshold", 64))

    def step(self, row: dict[str, Any]) -> tuple[int, float]:
        val = float(row.get("syn_queue_cur", 0) or 0)
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

    Signal 1 — Half-open volume: EWMA of syn_queue_cur.
    Signal 2 — Handshake completion ratio (HCR):
                HCR = active_opens_delta / (syn_queue_cur + 1)
                A low HCR means SYNs are arriving faster than they complete.

    Alert when:
        (vol_ewma > vol_mu + k_vol * vol_sigma) OR
        (hcr_ewma < hcr_mu - k_hcr * hcr_sigma)

    Both EWMA means and standard deviations are estimated online using Welford's
    method and frozen after warmup_steps.

    Params (dict):
        alpha       (float): EWMA smoothing factor. Default 0.2.
        k_vol       (float): Sigma multiplier for volume. Default 3.0.
        k_hcr       (float): Sigma multiplier for HCR. Default 2.5.
        warmup_steps(int):   Steps to collect before alerting. Default 30.
    """

    NAME = "D1"
    PARAM_SPACE: dict[str, list] = {
        "alpha":        [0.1, 0.2, 0.3, 0.5],
        "k_vol":        [2.0, 2.5, 3.0, 3.5, 4.0],
        "k_hcr":        [2.0, 2.5, 3.0, 3.5],
        "warmup_steps": [20, 30, 60],
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self.alpha: float = float(p.get("alpha", 0.2))
        self.k_vol: float = float(p.get("k_vol", 3.0))
        self.k_hcr: float = float(p.get("k_hcr", 2.5))
        self.warmup_steps: int = int(p.get("warmup_steps", 30))
        self._reset_state()

    def _reset_state(self) -> None:
        self._step = 0
        # EWMA values
        self._vol_ewma: float = 0.0
        self._hcr_ewma: float = 1.0
        # Welford online stats for baseline estimation
        self._vol_n = 0
        self._vol_mean = 0.0
        self._vol_M2 = 0.0
        self._hcr_n = 0
        self._hcr_mean = 1.0
        self._hcr_M2 = 0.0
        # Frozen baseline (post-warmup)
        self._vol_mu: float | None = None
        self._vol_sigma: float | None = None
        self._hcr_mu: float | None = None
        self._hcr_sigma: float | None = None
        # Previous active_opens for delta
        self._prev_active_opens: float | None = None

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
            return 1.0  # avoid zero-division; will not alert in warmup anyway
        return math.sqrt(M2 / (n - 1))

    def step(self, row: dict[str, Any]) -> tuple[int, float]:
        vol = float(row.get("syn_queue_cur", 0) or 0)
        active_opens = float(row.get("active_opens", 0) or 0)

        # Compute active_opens delta
        if self._prev_active_opens is None:
            ao_delta = 0.0
        else:
            ao_delta = max(0.0, active_opens - self._prev_active_opens)
        self._prev_active_opens = active_opens

        # HCR: how many opens completed per half-open slot
        hcr = ao_delta / (vol + 1.0)

        # Update EWMAs
        if self._step == 0:
            self._vol_ewma = vol
            self._hcr_ewma = hcr
        else:
            self._vol_ewma = self.alpha * vol + (1 - self.alpha) * self._vol_ewma
            self._hcr_ewma = self.alpha * hcr + (1 - self.alpha) * self._hcr_ewma

        self._step += 1

        # During warmup: update Welford and return no-alert
        if self._vol_mu is None:
            self._vol_n, self._vol_mean, self._vol_M2 = self._welford_update(
                self._vol_n, self._vol_mean, self._vol_M2, self._vol_ewma)
            self._hcr_n, self._hcr_mean, self._hcr_M2 = self._welford_update(
                self._hcr_n, self._hcr_mean, self._hcr_M2, self._hcr_ewma)
            if self._step >= self.warmup_steps:
                # Freeze baseline
                self._vol_mu = self._vol_mean
                self._vol_sigma = max(self._welford_std(self._vol_n, self._vol_M2), 1.0)
                self._hcr_mu = self._hcr_mean
                self._hcr_sigma = max(self._welford_std(self._hcr_n, self._hcr_M2), 0.01)
            return 0, 0.0

        # Post-warmup: compute scores
        vol_z = (self._vol_ewma - self._vol_mu) / self._vol_sigma
        hcr_z = (self._hcr_mu - self._hcr_ewma) / self._hcr_sigma  # inverted: low HCR = bad

        # Combined score (max of normalized exceedances)
        score = max(vol_z / self.k_vol, hcr_z / self.k_hcr)

        label = 1 if (vol_z > self.k_vol or hcr_z > self.k_hcr) else 0
        return label, score


# ---------------------------------------------------------------------------
# D2 — Extended: Connection Flood + Mitigation Branches
# ---------------------------------------------------------------------------

class D2Detector:
    """
    Extended detector building on D1.

    Additional branches:
      Connection flood branch:
        CLOSE_WAIT + TIME_WAIT count surge signals connection flood.
        Alert when (close_wait + time_wait)_ewma > baseline + k_conn * sigma.

      Mitigation branch (SYN cookie):
        syn_cookies_sent spike indicates kernel mitigating (syncookies active).
        Alert when delta(syn_cookies_sent)_ewma > k_cookie * sigma.

    Final alert = D1 alert OR conn_flood alert OR cookie_spike alert.

    Params (dict):
        All D1 params, plus:
        k_conn   (float): Sigma multiplier for connection count. Default 3.0.
        k_cookie (float): Sigma multiplier for cookie spike. Default 3.0.
    """

    NAME = "D2"
    PARAM_SPACE: dict[str, list] = {
        "alpha":        [0.1, 0.2, 0.3, 0.5],
        "k_vol":        [2.0, 2.5, 3.0, 3.5, 4.0],
        "k_hcr":        [2.0, 2.5, 3.0, 3.5],
        "k_conn":       [2.0, 2.5, 3.0, 3.5],
        "k_cookie":     [2.0, 2.5, 3.0, 3.5],
        "warmup_steps": [20, 30, 60],
    }

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        p = params or {}
        self.alpha: float = float(p.get("alpha", 0.2))
        self.k_vol: float = float(p.get("k_vol", 3.0))
        self.k_hcr: float = float(p.get("k_hcr", 2.5))
        self.k_conn: float = float(p.get("k_conn", 3.0))
        self.k_cookie: float = float(p.get("k_cookie", 3.0))
        self.warmup_steps: int = int(p.get("warmup_steps", 30))
        self._d1 = D1Detector(params)
        self._reset_extra()

    def _reset_extra(self) -> None:
        self._step = 0
        self._conn_ewma: float = 0.0
        self._cookie_ewma: float = 0.0
        # Welford for conn and cookie
        self._conn_n = 0; self._conn_mean = 0.0; self._conn_M2 = 0.0
        self._cookie_n = 0; self._cookie_mean = 0.0; self._cookie_M2 = 0.0
        # Frozen
        self._conn_mu: float | None = None
        self._conn_sigma: float | None = None
        self._cookie_mu: float | None = None
        self._cookie_sigma: float | None = None
        self._prev_cookies: float | None = None

    def reset(self) -> None:
        self._d1.reset()
        self._reset_extra()

    def step(self, row: dict[str, Any]) -> tuple[int, float]:
        d1_label, d1_score = self._d1.step(row)

        close_wait = float(row.get("close_wait", 0) or 0)
        time_wait = float(row.get("time_wait", 0) or 0)
        conn_count = close_wait + time_wait

        syn_cookies_sent = float(row.get("syn_cookies_sent", 0) or 0)
        if self._prev_cookies is None:
            cookie_delta = 0.0
        else:
            cookie_delta = max(0.0, syn_cookies_sent - self._prev_cookies)
        self._prev_cookies = syn_cookies_sent

        alpha = self.alpha
        if self._step == 0:
            self._conn_ewma = conn_count
            self._cookie_ewma = cookie_delta
        else:
            self._conn_ewma = alpha * conn_count + (1 - alpha) * self._conn_ewma
            self._cookie_ewma = alpha * cookie_delta + (1 - alpha) * self._cookie_ewma

        self._step += 1

        if self._conn_mu is None:
            # Welford update
            n, m, M2 = self._conn_n, self._conn_mean, self._conn_M2
            n += 1; delta = self._conn_ewma - m; m += delta / n; M2 += delta * (self._conn_ewma - m)
            self._conn_n, self._conn_mean, self._conn_M2 = n, m, M2

            n, m, M2 = self._cookie_n, self._cookie_mean, self._cookie_M2
            n += 1; delta = self._cookie_ewma - m; m += delta / n; M2 += delta * (self._cookie_ewma - m)
            self._cookie_n, self._cookie_mean, self._cookie_M2 = n, m, M2

            if self._step >= self.warmup_steps:
                self._conn_mu = self._conn_mean
                self._conn_sigma = max(
                    (self._conn_M2 / max(self._conn_n - 1, 1)) ** 0.5, 1.0)
                self._cookie_mu = self._cookie_mean
                self._cookie_sigma = max(
                    (self._cookie_M2 / max(self._cookie_n - 1, 1)) ** 0.5, 0.01)
            return d1_label, d1_score

        # Compute extra branch scores
        conn_z = (self._conn_ewma - self._conn_mu) / self._conn_sigma
        cookie_z = (self._cookie_ewma - self._cookie_mu) / self._cookie_sigma

        conn_alert = conn_z > self.k_conn
        cookie_alert = cookie_z > self.k_cookie

        d2_score = max(d1_score, conn_z / self.k_conn, cookie_z / self.k_cookie)
        d2_label = 1 if (d1_label or conn_alert or cookie_alert) else 0
        return d2_label, d2_score


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

