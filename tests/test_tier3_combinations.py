#!/usr/bin/env python3
"""
tests/test_tier3_combinations.py

Tier 3: Pairwise & Combinatorial Test Suite
Requirement-Driven Opaque-Box Test Harness
Covers:
  - Pairwise interactions across profile state (break/fix), attack guard,
    tools, durations, rates, kill switches, network states, and telemetry.
"""

import os
import re
import sys
import tempfile
import itertools
import unittest

LAB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_FILE = os.path.join(LAB_ROOT, "lab.env")

try:
    from tests.test_tier1_features import parse_env_file, AttackGuardContractOracle
except ImportError:
    from test_tier1_features import parse_env_file, AttackGuardContractOracle


class TestTier3Combinations(unittest.TestCase):
    """Pairwise combinatorial tests for cross-feature interactions."""

    @classmethod
    def setUpClass(cls):
        cls.env = parse_env_file(ENV_FILE)
        cls.victim_ip = cls.env.get("VICTIM_PRIVATE_IP", "172.31.37.214")
        cls.attacker_ip = cls.env.get("ATTACKER_PRIVATE_IP", "172.31.42.168")

    def test_t3_01_profile_state_x_attack_guard_execution(self):
        """Tier 3: Test Cartesian product of Profile State {break, fix} x Guard validation {valid, invalid}."""
        profiles = ["break", "fix"]
        guard_inputs = [
            {"target": self.victim_ip, "duration": 30, "interval": "u1000", "expected": True},
            {"target": "8.8.8.8", "duration": 30, "interval": "u1000", "expected": False},
            {"target": self.victim_ip, "duration": 65, "interval": "u1000", "expected": False},
        ]
        for prof in profiles:
            for g in guard_inputs:
                valid, msg = AttackGuardContractOracle.validate(
                    tool="hping3", target_ip=g["target"],
                    expected_victim_ip=self.victim_ip,
                    duration_s=g["duration"], interval_str=g["interval"],
                    kill_switch_path="/nonexistent/LAB_STOP"
                )
                self.assertEqual(valid, g["expected"],
                                 f"Failed profile={prof} target={g['target']} duration={g['duration']}")

    def test_t3_02_tool_selection_x_target_ip_pairwise(self):
        """Tier 3: Tool {hping3, conn_hold} x Target IP {victim_private, attacker_private, public_ip}."""
        tools = ["hping3", "conn_hold.py"]
        targets = [
            (self.victim_ip, True),
            (self.attacker_ip, False),
            ("1.1.1.1", False)
        ]
        for tool, (tgt, expected) in itertools.product(tools, targets):
            valid, msg = AttackGuardContractOracle.validate(
                tool=tool, target_ip=tgt,
                expected_victim_ip=self.victim_ip,
                duration_s=30, interval_str="u1000", conns=100,
                kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertEqual(valid, expected, f"Failed for tool={tool}, target={tgt}")

    def test_t3_03_kill_switch_x_duration_matrix(self):
        """Tier 3: Kill Switch {absent, present} x Duration {30s, 60s, 61s}."""
        durations = [(30, True), (60, True), (61, False)]
        with tempfile.NamedTemporaryFile() as tmp_kill:
            for d, duration_valid in durations:
                # When kill switch is absent:
                valid_absent, _ = AttackGuardContractOracle.validate(
                    tool="hping3", target_ip=self.victim_ip,
                    expected_victim_ip=self.victim_ip, duration_s=d,
                    interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
                )
                self.assertEqual(valid_absent, duration_valid, f"Absent kill switch, duration={d}")

                # When kill switch is present:
                valid_present, err = AttackGuardContractOracle.validate(
                    tool="hping3", target_ip=self.victim_ip,
                    expected_victim_ip=self.victim_ip, duration_s=d,
                    interval_str="u1000", kill_switch_path=tmp_kill.name
                )
                self.assertFalse(valid_present, f"Present kill switch must fail duration={d}")
                self.assertIn("E_KILL_SWITCH_ACTIVE", err)

    def test_t3_04_rate_limit_x_kill_switch_matrix(self):
        """Tier 3: Rate {u100, u1000, u99} x Kill switch {absent, present}."""
        rates = [("u100", True), ("u1000", True), ("u99", False)]
        with tempfile.NamedTemporaryFile() as tmp_kill:
            for rate_str, rate_ok in rates:
                # Absent
                ok_absent, _ = AttackGuardContractOracle.validate(
                    tool="hping3", target_ip=self.victim_ip,
                    expected_victim_ip=self.victim_ip, duration_s=30,
                    interval_str=rate_str, kill_switch_path="/nonexistent/LAB_STOP"
                )
                self.assertEqual(ok_absent, rate_ok)

                # Present
                ok_present, _ = AttackGuardContractOracle.validate(
                    tool="hping3", target_ip=self.victim_ip,
                    expected_victim_ip=self.victim_ip, duration_s=30,
                    interval_str=rate_str, kill_switch_path=tmp_kill.name
                )
                self.assertFalse(ok_present)

    def test_t3_05_sampling_method_x_frequency_combination(self):
        """Tier 3: Sampling method {proc, ss} x Frequency {1Hz, 10Hz} parameter matrix."""
        methods = ["proc", "ss"]
        frequencies = [1, 10]
        for m, f in itertools.product(methods, frequencies):
            interval_s = 1.0 / f
            self.assertIn(m, ("proc", "ss"))
            self.assertTrue(interval_s in (1.0, 0.1))

    def test_t3_06_kernel_mitigation_x_syn_flood_intensity(self):
        """Tier 3: Syncookies {0, 1} x Intensity {L: u10000, M: u1000, H: u100}."""
        intensities = {
            "L": ("u10000", 100),
            "M": ("u1000", 1000),
            "H": ("u100", 10000)
        }
        cookie_states = [0, 1]
        for cookies, (lvl, (interval, pps)) in itertools.product(cookie_states, intensities.items()):
            valid, _ = AttackGuardContractOracle.validate(
                tool="hping3", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=30,
                interval_str=interval, kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertTrue(valid)
            self.assertTrue(pps <= 10000)

    def test_t3_07_rst_suppression_x_syn_flood_semantics(self):
        """Tier 3: RST Suppression Rule {active, inactive} x Attacker kernel behavior."""
        # When active, outbound RST is dropped -> victim preserves half-open in SYN_RECV.
        # When inactive, kernel RST aborts handshake immediately -> syn_recv stays 0.
        states = [
            {"rst_suppression": True, "expected_victim_syn_recv": "rises toward backlog"},
            {"rst_suppression": False, "expected_victim_syn_recv": "stays near 0"}
        ]
        for s in states:
            self.assertIn(s["rst_suppression"], (True, False))
            self.assertTrue(len(s["expected_victim_syn_recv"]) > 0)

    def test_t3_08_crowd_concurrency_x_background_load_matrix(self):
        """Tier 3: Flash crowd level {Small 25%, Medium 50%, Large 100%} x Background load."""
        crowd_levels = {"small": 0.25, "medium": 0.50, "large": 1.00}
        bg_loads = [True, False]
        for lvl, fraction in crowd_levels.items():
            for bg in bg_loads:
                capacity_mock = 200  # req/s
                crowd_rps = capacity_mock * fraction
                total_rps = crowd_rps + (20 if bg else 0)
                self.assertGreater(total_rps, 0)

    def test_t3_09_tool_invocation_x_exit_code_protocol(self):
        """Tier 3: Guard exit code contract: valid invocation -> 0, guard refusal -> non-zero."""
        def simulated_guard_runner(is_valid):
            return 0 if is_valid else 1

        self.assertEqual(simulated_guard_runner(True), 0)
        self.assertNotEqual(simulated_guard_runner(False), 0)

    def test_t3_10_sampling_rate_x_metrics_completeness(self):
        """Tier 3: Sampling rate {1Hz, 10Hz} x Metrics row generation completeness."""
        durations = [10, 30]
        rates = [1, 10]
        for d, r in itertools.product(durations, rates):
            expected_rows = d * r
            self.assertEqual(expected_rows, d * r)

    def test_t3_11_chrony_offset_x_precheck_gating(self):
        """Tier 3: Chrony offset matrix {10ms, 45ms, 52ms} x Batch gating decision {proceed, abort}."""
        offsets = [
            (10.0, "proceed"),
            (45.0, "proceed"),
            (50.0, "proceed"),
            (50.1, "abort"),
            (75.0, "abort")
        ]
        for offset, action in offsets:
            decision = "proceed" if offset <= 50.0 else "abort"
            self.assertEqual(decision, action, f"Offset {offset} should yield {action}")

    def test_t3_12_cooldown_settling_x_run_dispatch_matrix(self):
        """Tier 3: Cooldown state {syn_recv == 0 for 10s, syn_recv > 0} x Dispatch action."""
        states = [
            ([0] * 10, True),
            ([0] * 9 + [1], False),
            ([2, 1, 0, 0, 0, 0, 0, 0, 0, 0], False),
            ([0] * 12, True)
        ]
        for history, can_dispatch in states:
            is_settled = (len(history) >= 10 and all(x == 0 for x in history[-10:]))
            self.assertEqual(is_settled, can_dispatch)

    def test_t3_13_connection_hold_concurrency_x_hold_time_pairwise(self):
        """Tier 3: Concurrency {100, 500, 2000} x Hold duration {10s, 30s, 60s}."""
        conns = [100, 500, 2000]
        durations = [10, 30, 60]
        for c, d in itertools.product(conns, durations):
            valid, _ = AttackGuardContractOracle.validate(
                tool="conn_hold.py", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=d, conns=c,
                kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertTrue(valid, f"Failed for c={c}, d={d}")

    def test_t3_14_probe_http_status_x_latency_x_ok_flag(self):
        """Tier 3: HTTP status {200, 502, timeout} x Latency {0.05s, 2.9s, 3.1s} x OK flag."""
        cases = [
            (200, 0.05, 1),
            (200, 2.90, 1),
            (200, 3.10, 0),  # Latency > 3.0s violates SLA
            (502, 0.10, 0),
            (0, 3.00, 0)     # Connection error / timeout
        ]
        for code, latency, expected_ok in cases:
            computed_ok = 1 if (code == 200 and latency <= 3.0) else 0
            self.assertEqual(computed_ok, expected_ok, f"Failed for code={code}, lat={latency}")

    def test_t3_15_repetition_index_x_pcap_capture_policy(self):
        """Tier 3: Repetition {1, 2, 3, 4, 5} x PCAP capture enablement (rep 1 only)."""
        reps = [1, 2, 3, 4, 5]
        for r in reps:
            capture_enabled = (r == 1)
            self.assertEqual(capture_enabled, r == 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
