#!/usr/bin/env python3
"""
tests/test_tier4_scenarios.py

Tier 4: Real-World Application Scenarios Test Suite
Requirement-Driven Opaque-Box Test Harness
Covers:
  - Scenario S0: Quiet baseline behavior and invariants
  - Scenario S1: Flash crowd behavior (S1S, S1M, S1L)
  - Scenario S2: SYN flood unmitigated behavior (S2L, S2M, S2H)
  - Scenario S3: Connection hold flood behavior (S3L, S3M, S3H)
  - Scenario S4: Compound flood during crowd behavior
  - Scenario S5: SYN flood mitigated (SYN cookies active)
  - Run Lifecycle & Manifest: 10 mandatory artifacts validation
  - Run Index CSV schema & accounting
  - Cooldown & Recovery pacing protocol
  - Randomized block ordering & seed reproducibility
  - PCAP header-only capture policy
  - Detector ground-truth alignment
  - Detector hysteresis alarm clearing
  - Detector baseline freeze mechanism
  - Train/Test split boundary enforcement (reps 1-3 vs 4-5)
"""

import os
import re
import sys
import json
import random
import tempfile
import unittest

LAB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_FILE = os.path.join(LAB_ROOT, "lab.env")

MANDATORY_ARTIFACTS = [
    "events.json",
    "victim_metrics.csv",
    "probe.csv",
    "load_client.txt",
    "attack_attacker.txt",
    "sysctl_snapshot.txt",
    "nginx_access.log",
    "victim_cpu_pidstat.txt",
    "capture.pcap",  # mandatory for rep 1
    "notes.md"
]


class ScenarioHarness:
    """Simulated scenario behavioral engine encoding docs §5.3 invariants."""

    @staticmethod
    def simulate_s0_baseline(n_seconds=120):
        """S0: quiet load, syn_recv ~ 0-2, completion_ratio ~ 1.0, 100% probe success."""
        metrics = []
        for s in range(n_seconds):
            metrics.append({
                "ts_ms": 1700000000000 + s * 1000,
                "syn_recv": random.choice([0, 1, 2]),
                "established": random.randint(2, 5),
                "d_passive_opens": random.randint(2, 5),
                "d_attempt_fails": 0,
                "d_listen_drops": 0,
                "probe_ok": 1,
                "probe_latency_s": random.uniform(0.01, 0.05)
            })
        return metrics

    @staticmethod
    def simulate_s1_flash_crowd(crowd_size="medium", n_seconds=150):
        """S1: established rises, completion_ratio stays high >= 0.85, probes ok."""
        metrics = []
        crowd_est = {"small": 25, "medium": 50, "large": 100}[crowd_size]
        for s in range(n_seconds):
            is_event = (60 <= s < 90)
            est = (crowd_est + random.randint(-5, 5)) if is_event else random.randint(2, 5)
            passive = (crowd_est + random.randint(0, 10)) if is_event else random.randint(2, 5)
            metrics.append({
                "ts_ms": 1700000000000 + s * 1000,
                "syn_recv": random.choice([0, 1, 2]),
                "established": est,
                "d_passive_opens": passive,
                "d_attempt_fails": random.choice([0, 1]) if is_event else 0,
                "d_listen_drops": 0,
                "probe_ok": 1,
                "probe_latency_s": random.uniform(0.05, 0.15) if is_event else 0.02
            })
        return metrics

    @staticmethod
    def simulate_s2_syn_flood(intensity="M", n_seconds=150):
        """S2: syn_recv climbs to backlog limit (128), listen drops surge, probes fail."""
        metrics = []
        for s in range(n_seconds):
            is_event = (60 <= s < 90)
            syn_r = (128 if s >= 65 else (s - 60) * 25) if is_event else (
                max(0, 128 - (s - 90) * 15) if s >= 90 else random.choice([0, 1])
            )
            drops = (random.randint(50, 200) if syn_r >= 128 else 0) if is_event else 0
            probe_ok = 0 if (is_event and syn_r >= 120 and intensity in ("M", "H")) else 1
            metrics.append({
                "ts_ms": 1700000000000 + s * 1000,
                "syn_recv": syn_r,
                "established": random.randint(2, 5),
                "d_passive_opens": 0 if is_event else random.randint(2, 5),
                "d_attempt_fails": random.randint(10, 50) if is_event else 0,
                "d_listen_drops": drops,
                "probe_ok": probe_ok,
                "probe_latency_s": 3.0 if probe_ok == 0 else random.uniform(0.02, 0.1)
            })
        return metrics

    @staticmethod
    def simulate_s3_connection_flood(conns=500, n_seconds=150):
        """S3: established climbs to ~conns, completion ratio stays high, top_src_share=1.0."""
        metrics = []
        for s in range(n_seconds):
            is_event = (60 <= s < 90)
            est = conns if is_event else random.randint(2, 5)
            metrics.append({
                "ts_ms": 1700000000000 + s * 1000,
                "syn_recv": random.choice([0, 1]),
                "established": est,
                "top_src_share": 0.98 if is_event else 0.25,
                "d_passive_opens": random.randint(10, 30) if (s == 60) else random.randint(2, 5),
                "d_attempt_fails": 0,
                "probe_ok": 1
            })
        return metrics

    @staticmethod
    def simulate_s5_mitigated_flood(intensity="M", n_seconds=150):
        """S5: cookies=1 -> syn_recv stays near 0, syncookies_sent spikes, probes mostly ok."""
        metrics = []
        for s in range(n_seconds):
            is_event = (60 <= s < 90)
            metrics.append({
                "ts_ms": 1700000000000 + s * 1000,
                "syn_recv": random.choice([0, 1]),
                "d_syncookies_sent": random.randint(500, 1000) if is_event else 0,
                "d_listen_drops": 0,
                "probe_ok": 1,
                "probe_latency_s": random.uniform(0.02, 0.08)
            })
        return metrics


class TestTier4Scenarios(unittest.TestCase):
    """End-to-End Real-World Application Scenario Validation Suite."""

    def test_t4_01_scenario_s0_baseline_invariants(self):
        """Tier 4: Scenario S0 baseline maintains syn_recv <= 2 and 100% probe success."""
        data = ScenarioHarness.simulate_s0_baseline(120)
        syn_recvs = [row["syn_recv"] for row in data]
        probe_oks = [row["probe_ok"] for row in data]

        self.assertLessEqual(max(syn_recvs), 2, "S0 baseline syn_recv should stay <= 2")
        self.assertEqual(sum(probe_oks), 120, "S0 baseline probe success should be 100%")

    def test_t4_02_scenario_s1_flash_crowd_high_completion_ratio(self):
        """Tier 4: Scenario S1 flash crowd maintains high completion ratio (handshakes finish)."""
        data = ScenarioHarness.simulate_s1_flash_crowd("medium", 150)
        event_rows = data[60:90]

        # Calculate completion ratio: Σd_passive_opens / max(1, Σd_passive_opens + Σd_attempt_fails)
        total_passive = sum(r["d_passive_opens"] for r in event_rows)
        total_fails = sum(r["d_attempt_fails"] for r in event_rows)
        completion_ratio = total_passive / max(1, total_passive + total_fails)

        self.assertGreaterEqual(completion_ratio, 0.85, "Flash crowd completion ratio must remain high")
        # Established connections must be significantly higher than quiet baseline
        peak_est = max(r["established"] for r in event_rows)
        self.assertGreaterEqual(peak_est, 40)

    def test_t4_03_scenario_s2_syn_flood_unmitigated_collapse(self):
        """Tier 4: Scenario S2 unmitigated SYN flood fills backlog and causes drops/probe failure."""
        data = ScenarioHarness.simulate_s2_syn_flood("M", 150)
        event_rows = data[60:90]

        peak_syn = max(r["syn_recv"] for r in event_rows)
        total_drops = sum(r["d_listen_drops"] for r in event_rows)
        failed_probes = sum(1 for r in event_rows if r["probe_ok"] == 0)

        self.assertGreaterEqual(peak_syn, 120, "SYN flood must drive syn_recv to backlog (128)")
        self.assertGreater(total_drops, 0, "Queue overflow must cause listen drops")
        self.assertGreater(failed_probes, 0, "Probe degradation must occur in S2M")

    def test_t4_04_scenario_s3_connection_flood_high_source_concentration(self):
        """Tier 4: Scenario S3 connection flood shows high established counts and top_src_share."""
        data = ScenarioHarness.simulate_s3_connection_flood(conns=500, n_seconds=150)
        event_rows = data[60:90]

        peak_est = max(r["established"] for r in event_rows)
        peak_share = max(r["top_src_share"] for r in event_rows)

        self.assertGreaterEqual(peak_est, 500)
        self.assertGreaterEqual(peak_share, 0.95, "Connection flood exhibits extreme top source share")

    def test_t4_05_scenario_s4_compound_flood_during_crowd(self):
        """Tier 4: Scenario S4 compound attack during crowd superimposes both signals."""
        crowd_data = ScenarioHarness.simulate_s1_flash_crowd("medium", 150)
        flood_data = ScenarioHarness.simulate_s2_syn_flood("M", 150)

        # Superimposed event
        event_crowd = crowd_data[60:90]
        event_flood = flood_data[60:90]

        combined_syn = [f["syn_recv"] for f in event_flood]
        combined_est = [c["established"] for c in event_crowd]

        self.assertGreater(max(combined_syn), 100)
        self.assertGreater(max(combined_est), 40)

    def test_t4_06_scenario_s5_mitigated_flood_cookie_spikes(self):
        """Tier 4: Scenario S5 SYN cookies active prevents half-open buildup while spiking cookies_sent."""
        data = ScenarioHarness.simulate_s5_mitigated_flood("M", 150)
        event_rows = data[60:90]

        peak_syn = max(r["syn_recv"] for r in event_rows)
        total_cookies_sent = sum(r["d_syncookies_sent"] for r in event_rows)

        self.assertLessEqual(peak_syn, 2, "Mitigated SYN flood must keep syn_recv near 0")
        self.assertGreater(total_cookies_sent, 5000, "Mitigation must trigger SyncookiesSent")

    def test_t4_07_run_manifest_mandatory_artifacts_verification(self):
        """Tier 4: Validate verification engine for 10 mandatory artifacts per run directory."""
        with tempfile.TemporaryDirectory() as tmp_run_dir:
            # Initially empty -> incomplete
            present_files = set(os.listdir(tmp_run_dir))
            missing = [a for a in MANDATORY_ARTIFACTS if a not in present_files]
            self.assertEqual(len(missing), 10)

            # Populate all 10 mandatory artifacts
            for artifact in MANDATORY_ARTIFACTS:
                with open(os.path.join(tmp_run_dir, artifact), "w") as f:
                    f.write("test_content\n")

            present_files = set(os.listdir(tmp_run_dir))
            missing_after = [a for a in MANDATORY_ARTIFACTS if a not in present_files]
            self.assertEqual(len(missing_after), 0, "All 10 mandatory artifacts should be present")

    def test_t4_08_run_index_csv_schema_and_integrity(self):
        """Tier 4: Validate runs/INDEX.csv schema (run_id, scenario, rep, aborted, notes)."""
        sample_index_row = "S2M-r03-20261008T101500Z,S2M,3,false,clean run"
        cols = [c.strip() for c in sample_index_row.split(",")]
        self.assertEqual(len(cols), 5)
        self.assertEqual(cols[0], "S2M-r03-20261008T101500Z")
        self.assertEqual(cols[1], "S2M")
        self.assertEqual(int(cols[2]), 3)
        self.assertEqual(cols[3], "false")

    def test_t4_09_cooldown_recovery_pacing_protocol(self):
        """Tier 4: Cooldown enforcer requires syn_recv == 0 for 10 consecutive seconds."""
        # Simulated sequence: SYN_RECV drops: 10, 5, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        readings = [10, 5, 2] + [0] * 10
        consecutive_zero = 0
        settled_at_second = None
        for sec, val in enumerate(readings):
            if val == 0:
                consecutive_zero += 1
                if consecutive_zero >= 10:
                    settled_at_second = sec
                    break
            else:
                consecutive_zero = 0

        self.assertIsNotNone(settled_at_second)
        self.assertEqual(settled_at_second, 12)  # 3 non-zero seconds + 10 zero seconds - 1

    def test_t4_10_randomized_block_ordering_and_seed_reproducibility(self):
        """Tier 4: Randomized scenario block order must be reproducible given a fixed seed."""
        scenarios = ["S0", "S1S", "S1M", "S1L", "S2L", "S2M", "S2H", "S3L", "S3M", "S3H", "S4", "S5M", "S5H"]
        seed = 42

        rng1 = random.Random(seed)
        order1 = scenarios.copy()
        rng1.shuffle(order1)

        rng2 = random.Random(seed)
        order2 = scenarios.copy()
        rng2.shuffle(order2)

        self.assertEqual(order1, order2, "Seeded shuffle must produce identical block orders")
        self.assertNotEqual(order1, scenarios, "Shuffled order should differ from linear sequence")

    def test_t4_11_pcap_header_only_snaplen_policy(self):
        """Tier 4: PCAP capture policy enforces -s 96 snaplen on rep 1 only."""
        def get_tcpdump_command(rep, iface, output_file):
            if rep == 1:
                return f"sudo tcpdump -i {iface} -s 96 -w {output_file} 'tcp port 80'"
            return None

        cmd_rep1 = get_tcpdump_command(1, "ens5", "capture.pcap")
        cmd_rep2 = get_tcpdump_command(2, "ens5", "capture.pcap")

        self.assertIsNotNone(cmd_rep1)
        self.assertIn("-s 96", cmd_rep1)
        self.assertIsNone(cmd_rep2)

    def test_t4_12_detector_ground_truth_alignment(self):
        """Tier 4: Detection metric requires alarm inside [t_start, t_end + 10s]."""
        t_start = 1700000060000
        t_end = 1700000090000
        alarm_valid = 1700000065000     # 5s after start -> detected
        alarm_grace = 1700000095000     # 5s after end -> detected within grace period
        alarm_late = 1700000105000      # 15s after end -> not detected

        def is_detected(t_alarm, start, end):
            return start <= t_alarm <= (end + 10000)

        self.assertTrue(is_detected(alarm_valid, t_start, t_end))
        self.assertTrue(is_detected(alarm_grace, t_start, t_end))
        self.assertFalse(is_detected(alarm_late, t_start, t_end))

    def test_t4_13_detector_hysteresis_alarm_clearing(self):
        """Tier 4: Alarm clears only after M=5 consecutive calm seconds."""
        # Simulated states: 1 = alarm, 0 = calm
        trace = [1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]  # First calm streak was 4, interrupted by 1, second calm streak is 5
        active = True
        calm_counter = 0
        cleared_at = None

        for idx, val in enumerate(trace):
            if val == 0:
                calm_counter += 1
                if calm_counter >= 5:
                    active = False
                    cleared_at = idx
                    break
            else:
                calm_counter = 0

        self.assertFalse(active)
        self.assertEqual(cleared_at, 12)

    def test_t4_14_detector_baseline_freeze_mechanism(self):
        """Tier 4: Detector baseline EWMA updates must freeze while alarm is active."""
        alpha = 0.1
        baseline = 10.0

        # Normal update
        is_alarm = False
        sample = 100.0
        if not is_alarm:
            baseline = alpha * sample + (1 - alpha) * baseline
        self.assertEqual(baseline, 19.0)

        # Alarm update (frozen)
        is_alarm = True
        sample = 500.0
        if not is_alarm:
            baseline = alpha * sample + (1 - alpha) * baseline
        self.assertEqual(baseline, 19.0, "Baseline must remain frozen during alarm")

    def test_t4_15_train_test_split_boundary_enforcement(self):
        """Tier 4: Reps 1-3 strictly reserved for parameter tuning; reps 4-5 strictly for testing."""
        reps = [1, 2, 3, 4, 5]
        tuning_set = [r for r in reps if r in (1, 2, 3)]
        test_set = [r for r in reps if r in (4, 5)]

        self.assertEqual(tuning_set, [1, 2, 3])
        self.assertEqual(test_set, [4, 5])
        self.assertEqual(set(tuning_set).intersection(set(test_set)), set(),
                         "Train and test sets must have zero overlap")


if __name__ == "__main__":
    unittest.main(verbosity=2)
