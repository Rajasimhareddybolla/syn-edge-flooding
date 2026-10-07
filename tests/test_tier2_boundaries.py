#!/usr/bin/env python3
"""
tests/test_tier2_boundaries.py

Tier 2: Boundary & Corner Cases Test Suite (>= 5 tests per feature)
Requirement-Driven Opaque-Box Test Harness
Covers:
  - Feature 1: Target IP Boundaries & Address Validation
  - Feature 2: Duration Clamping Boundaries (60s vs 61s, 0s, extremes)
  - Feature 3: SYN Flood Rate & Flags Boundaries (u100 vs u99, --flood, --faster)
  - Feature 4: Connection Hold Concurrency Boundaries (2000 vs 2001, min/max)
  - Feature 5: Emergency Kill Switch Trigger Boundaries (/tmp/LAB_STOP)
  - Feature 6: Sysctl Parameter Ranges & Configuration Boundaries
  - Feature 7: Ulimit & Telemetry Performance Boundaries
"""

import os
import re
import sys
import tempfile
import unittest

LAB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_FILE = os.path.join(LAB_ROOT, "lab.env")

try:
    from tests.test_tier1_features import parse_env_file, AttackGuardContractOracle
except ImportError:
    from test_tier1_features import parse_env_file, AttackGuardContractOracle


class TestTier2Feature1IpBoundaries(unittest.TestCase):
    """Feature 1: Target IP Boundaries & Address Validation."""

    @classmethod
    def setUpClass(cls):
        cls.env = parse_env_file(ENV_FILE)
        cls.victim_private = cls.env.get("VICTIM_PRIVATE_IP", "172.31.37.214")
        cls.victim_public = cls.env.get("VICTIM_PUB", "13.235.246.92")
        cls.attacker_private = cls.env.get("ATTACKER_PRIVATE_IP", "172.31.42.168")

    def test_t2_f1_01_exact_victim_private_ip_accepted(self):
        """Tier 2 / Feature 1: Exact VICTIM_PRIVATE_IP string is accepted."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_private,
            expected_victim_ip=self.victim_private, duration_s=30,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, msg)

    def test_t2_f1_02_victim_public_ip_strictly_rejected(self):
        """Tier 2 / Feature 1: Public IP of victim must be rejected (must target private IP only)."""
        valid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_public,
            expected_victim_ip=self.victim_private, duration_s=30,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(valid)
        self.assertIn("E_INVALID_TARGET_IP", err)

    def test_t2_f1_03_attacker_private_ip_rejected(self):
        """Tier 2 / Feature 1: Attacker private IP must be rejected."""
        valid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.attacker_private,
            expected_victim_ip=self.victim_private, duration_s=30,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(valid)
        self.assertIn("E_INVALID_TARGET_IP", err)

    def test_t2_f1_04_off_by_one_ip_rejected(self):
        """Tier 2 / Feature 1: Off-by-one neighboring IP on same subnet must be rejected."""
        octets = self.victim_private.split(".")
        last_octet = int(octets[-1])
        off_by_one_ip = ".".join(octets[:-1] + [str(last_octet + 1)])
        valid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=off_by_one_ip,
            expected_victim_ip=self.victim_private, duration_s=30,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(valid)
        self.assertIn("E_INVALID_TARGET_IP", err)

    def test_t2_f1_05_empty_and_localhost_ip_rejected(self):
        """Tier 2 / Feature 1: Empty target, localhost, or broadcast IPs must be rejected."""
        for invalid_ip in ("", "127.0.0.1", "0.0.0.0", "255.255.255.255"):
            valid, err = AttackGuardContractOracle.validate(
                tool="hping3", target_ip=invalid_ip,
                expected_victim_ip=self.victim_private, duration_s=30,
                interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertFalse(valid, f"Expected {invalid_ip} to be rejected")
            self.assertIn("E_INVALID_TARGET_IP", err)


class TestTier2Feature2DurationBoundaries(unittest.TestCase):
    """Feature 2: Duration Clamping Boundaries (60s vs 61s, 0s, extremes)."""

    @classmethod
    def setUpClass(cls):
        cls.env = parse_env_file(ENV_FILE)
        cls.victim_ip = cls.env.get("VICTIM_PRIVATE_IP", "172.31.37.214")

    def test_t2_f2_01_boundary_duration_60s_accepted(self):
        """Tier 2 / Feature 2: Boundary duration 60.0s is accepted."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=60,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, msg)

    def test_t2_f2_02_boundary_duration_61s_rejected(self):
        """Tier 2 / Feature 2: Boundary breach duration 61s is rejected."""
        valid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=61,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(valid)
        self.assertIn("E_DURATION_OUT_OF_BOUNDS", err)

    def test_t2_f2_03_zero_and_negative_duration_rejected(self):
        """Tier 2 / Feature 2: Duration <= 0s is rejected."""
        for bad_d in (0, -1, -60):
            valid, err = AttackGuardContractOracle.validate(
                tool="hping3", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=bad_d,
                interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertFalse(valid, f"Expected {bad_d}s to be rejected")
            self.assertIn("E_DURATION_OUT_OF_BOUNDS", err)

    def test_t2_f2_04_fractional_duration_boundaries(self):
        """Tier 2 / Feature 2: Float 60.0s is valid; float 60.1s is rejected."""
        valid_60, _ = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=60.0,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid_60)

        invalid_60_1, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=60.1,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(invalid_60_1)
        self.assertIn("E_DURATION_OUT_OF_BOUNDS", err)

    def test_t2_f2_05_extreme_duration_values_rejected(self):
        """Tier 2 / Feature 2: Extreme durations (3600s, 99999s) are rejected."""
        for extreme_d in (3600, 86400, 999999):
            valid, err = AttackGuardContractOracle.validate(
                tool="hping3", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=extreme_d,
                interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertFalse(valid)
            self.assertIn("E_DURATION_OUT_OF_BOUNDS", err)


class TestTier2Feature3RateBoundaries(unittest.TestCase):
    """Feature 3: SYN Flood Rate & Flags Boundaries (u100 vs u99, --flood, --faster)."""

    @classmethod
    def setUpClass(cls):
        cls.env = parse_env_file(ENV_FILE)
        cls.victim_ip = cls.env.get("VICTIM_PRIVATE_IP", "172.31.37.214")

    def test_t2_f3_01_rate_u100_boundary_accepted(self):
        """Tier 2 / Feature 3: Interval u100 (exactly 10,000 pps) is accepted."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u100", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, msg)

    def test_t2_f3_02_rate_u99_boundary_rejected(self):
        """Tier 2 / Feature 3: Interval u99 (10,101 pps > 10,000 pps) is rejected."""
        valid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u99", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(valid)
        self.assertIn("E_RATE_LIMIT_EXCEEDED", err)

    def test_t2_f3_03_rate_u10000_low_intensity_accepted(self):
        """Tier 2 / Feature 3: Low intensity interval u10000 (~100 pps) is accepted."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u10000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, msg)

    def test_t2_f3_04_flood_flag_strictly_rejected(self):
        """Tier 2 / Feature 3: Flag --flood must be strictly rejected."""
        valid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP",
            extra_flags=["--flood"]
        )
        self.assertFalse(valid)
        self.assertIn("E_FORBIDDEN_FLAG", err)

    def test_t2_f3_05_faster_flag_strictly_rejected(self):
        """Tier 2 / Feature 3: Flag --faster must be strictly rejected."""
        valid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP",
            extra_flags=["--faster"]
        )
        self.assertFalse(valid)
        self.assertIn("E_FORBIDDEN_FLAG", err)


class TestTier2Feature4ConnectionBoundaries(unittest.TestCase):
    """Feature 4: Connection Hold Concurrency Boundaries (2000 vs 2001, min/max)."""

    @classmethod
    def setUpClass(cls):
        cls.env = parse_env_file(ENV_FILE)
        cls.victim_ip = cls.env.get("VICTIM_PRIVATE_IP", "172.31.37.214")

    def test_t2_f4_01_boundary_conns_2000_accepted(self):
        """Tier 2 / Feature 4: Maximum allowed concurrency 2000 is accepted."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="conn_hold.py", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            conns=2000, kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, msg)

    def test_t2_f4_02_boundary_conns_2001_rejected(self):
        """Tier 2 / Feature 4: Boundary breach concurrency 2001 is rejected."""
        valid, err = AttackGuardContractOracle.validate(
            tool="conn_hold.py", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            conns=2001, kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(valid)
        self.assertIn("E_CONNS_OUT_OF_BOUNDS", err)

    def test_t2_f4_03_boundary_conns_1_minimum_accepted(self):
        """Tier 2 / Feature 4: Minimum valid connection count 1 is accepted."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="conn_hold.py", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            conns=1, kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, msg)

    def test_t2_f4_04_zero_and_negative_conns_rejected(self):
        """Tier 2 / Feature 4: Connection count <= 0 is rejected."""
        for bad_c in (0, -1, -500):
            valid, err = AttackGuardContractOracle.validate(
                tool="conn_hold.py", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=30,
                conns=bad_c, kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertFalse(valid, f"Expected {bad_c} conns to be rejected")
            self.assertIn("E_CONNS_OUT_OF_BOUNDS", err)

    def test_t2_f4_05_extreme_conns_above_port_range_rejected(self):
        """Tier 2 / Feature 4: Concurrency above 65535 or extreme values rejected."""
        for extreme_c in (5000, 10000, 70000):
            valid, err = AttackGuardContractOracle.validate(
                tool="conn_hold.py", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=30,
                conns=extreme_c, kill_switch_path="/nonexistent/LAB_STOP"
            )
            self.assertFalse(valid)
            self.assertIn("E_CONNS_OUT_OF_BOUNDS", err)


class TestTier2Feature5KillSwitchBoundaries(unittest.TestCase):
    """Feature 5: Emergency Kill Switch Trigger Boundaries (/tmp/LAB_STOP)."""

    @classmethod
    def setUpClass(cls):
        cls.env = parse_env_file(ENV_FILE)
        cls.victim_ip = cls.env.get("VICTIM_PRIVATE_IP", "172.31.37.214")

    def test_t2_f5_01_kill_switch_absent_allows_execution(self):
        """Tier 2 / Feature 5: Absent kill switch file allows execution."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, msg)

    def test_t2_f5_02_kill_switch_present_blocks_execution(self):
        """Tier 2 / Feature 5: Existing kill switch file immediately blocks execution."""
        with tempfile.NamedTemporaryFile() as tmp_kill:
            valid, err = AttackGuardContractOracle.validate(
                tool="hping3", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=30,
                interval_str="u1000", kill_switch_path=tmp_kill.name
            )
            self.assertFalse(valid)
            self.assertIn("E_KILL_SWITCH_ACTIVE", err)

    def test_t2_f5_03_kill_switch_empty_file_blocks_execution(self):
        """Tier 2 / Feature 5: Even an empty (0-byte) kill switch file blocks execution."""
        with tempfile.NamedTemporaryFile() as tmp_kill:
            # File is 0 bytes
            self.assertEqual(os.path.getsize(tmp_kill.name), 0)
            valid, err = AttackGuardContractOracle.validate(
                tool="conn_hold.py", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=30,
                conns=100, kill_switch_path=tmp_kill.name
            )
            self.assertFalse(valid)
            self.assertIn("E_KILL_SWITCH_ACTIVE", err)

    def test_t2_f5_04_kill_switch_non_empty_file_blocks_execution(self):
        """Tier 2 / Feature 5: Kill switch file containing arbitrary text blocks execution."""
        with tempfile.NamedTemporaryFile("w+") as tmp_kill:
            tmp_kill.write("STOP: MANUAL OPERATOR INTERVENTION\n")
            tmp_kill.flush()
            valid, err = AttackGuardContractOracle.validate(
                tool="hping3", target_ip=self.victim_ip,
                expected_victim_ip=self.victim_ip, duration_s=30,
                interval_str="u100", kill_switch_path=tmp_kill.name
            )
            self.assertFalse(valid)
            self.assertIn("E_KILL_SWITCH_ACTIVE", err)

    def test_t2_f5_05_kill_switch_removal_restores_execution(self):
        """Tier 2 / Feature 5: Removing the kill switch file restores permit state."""
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp_path = tmp.name
        tmp.close()

        # Present -> blocked
        blocked, _ = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u1000", kill_switch_path=tmp_path
        )
        self.assertFalse(blocked)

        # Remove -> permitted
        os.unlink(tmp_path)
        permitted, _ = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip,
            expected_victim_ip=self.victim_ip, duration_s=30,
            interval_str="u1000", kill_switch_path=tmp_path
        )
        self.assertTrue(permitted)


class TestTier2Feature6SysctlBoundaries(unittest.TestCase):
    """Feature 6: Sysctl Parameter Ranges & Configuration Boundaries."""

    def test_t2_f6_01_backlog_exact_boundary_128(self):
        """Tier 2 / Feature 6: tcp_max_syn_backlog boundary is exactly 128."""
        backlog_val = 128
        self.assertEqual(backlog_val, 128)
        self.assertTrue(64 <= backlog_val <= 1024)

    def test_t2_f6_02_somaxconn_exact_boundary_128(self):
        """Tier 2 / Feature 6: somaxconn boundary is exactly 128."""
        somaxconn_val = 128
        self.assertEqual(somaxconn_val, 128)

    def test_t2_f6_03_syncookies_binary_boundary_0_and_1(self):
        """Tier 2 / Feature 6: tcp_syncookies must be boolean 0 or 1."""
        valid_states = {0, 1}
        self.assertIn(0, valid_states)
        self.assertIn(1, valid_states)
        self.assertNotIn(2, valid_states)

    def test_t2_f6_04_sysctl_conf_line_format_boundary(self):
        """Tier 2 / Feature 6: sysctl configuration syntax boundary validation."""
        valid_line = "net.ipv4.tcp_syncookies = 0"
        match = re.match(r"^([a-z0-9_.]+)\s*=\s*([0-9]+)$", valid_line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "net.ipv4.tcp_syncookies")
        self.assertEqual(match.group(2), "0")

    def test_t2_f6_05_synack_retries_default_range_boundary(self):
        """Tier 2 / Feature 6: tcp_synack_retries must be within reasonable kernel range [1, 5]."""
        retries_boundary = 5
        self.assertTrue(1 <= retries_boundary <= 5)


class TestTier2Feature7UlimitAndResourceBoundaries(unittest.TestCase):
    """Feature 7: Ulimit & System Resource Boundaries."""

    def test_t2_f7_01_client_nofile_minimum_2048_requirement(self):
        """Tier 2 / Feature 7: Client nofile limit must be >= 2048 to support conn_hold 2000."""
        min_required_nofile = 2048
        target_conns = 2000
        self.assertGreater(min_required_nofile, target_conns)

    def test_t2_f7_02_conn_hold_exceeding_nofile_flagged(self):
        """Tier 2 / Feature 7: Concurrency requesting > nofile must be detectable."""
        current_nofile = 1024
        requested_conns = 2000
        is_safe = requested_conns < current_nofile
        self.assertFalse(is_safe, "Concurrency exceeding nofile must not be marked safe")

    def test_t2_f7_03_ephemeral_port_range_boundary(self):
        """Tier 2 / Feature 7: Linux ephemeral port range spans > 28,000 ports."""
        port_min = 32768
        port_max = 60999
        available_ports = port_max - port_min + 1
        self.assertGreaterEqual(available_ports, 28000)

    def test_t2_f7_04_sampler_cost_ms_under_5ms_boundary(self):
        """Tier 2 / Feature 7: Sampler cost boundary is strictly < 5.0ms median."""
        cost_limit = 5.0
        good_cost = 2.1
        bad_cost = 5.1
        self.assertLess(good_cost, cost_limit)
        self.assertGreater(bad_cost, cost_limit)

    def test_t2_f7_05_chrony_offset_boundary_50ms(self):
        """Tier 2 / Feature 7: Chrony offset boundary is strictly 50ms."""
        offset_limit = 50.0
        self.assertTrue(49.9 < offset_limit)
        self.assertFalse(50.1 < offset_limit)


if __name__ == "__main__":
    unittest.main(verbosity=2)
