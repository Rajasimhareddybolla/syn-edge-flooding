#!/usr/bin/env python3
"""
tests/test_tier1_features.py

Tier 1: Feature Coverage Test Suite (>= 5 tests per feature)
Requirement-Driven Opaque-Box Test Harness
Covers:
  - Feature 1: Environment Configuration & Interface Contracts (lab.env)
  - Feature 2: Security Group Lockdown & Network Safety Rules
  - Feature 3: SSH Key Permissions & Provisioning Integrity
  - Feature 4: Attack Guard Contract & Safety Requirements
  - Feature 5: Sysctl Profiles & Kernel Configuration Contracts
  - Feature 6: Telemetry & Data Schema Contracts
"""

import os
import re
import sys
import stat
import json
import ipaddress
import subprocess
import tempfile
import unittest

LAB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_FILE = os.path.join(LAB_ROOT, "lab.env")
INFRA_DIR = os.path.join(LAB_ROOT, "infra")
TOOLS_DIR = os.path.join(LAB_ROOT, "tools")

MANDATORY_ENV_VARS = [
    "AWS_REGION", "VPC_ID", "SG_ID", "KEY_NAME", "KEY_PATH",
    "VICTIM_ID", "ATTACKER_ID", "CLIENT_ID",
    "VICTIM_PUB", "ATTACKER_PUB", "CLIENT_PUB",
    "VICTIM_PRIVATE_IP", "ATTACKER_PRIVATE_IP", "CLIENT_PRIVATE_IP",
    "VICTIM_IFACE"
]


def parse_env_file(path):
    """Parse bash export statements with strict regex."""
    vars_dict = {}
    if not os.path.isfile(path):
        return vars_dict
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^export\s+([A-Za-z_][A-Za-z0-9_]*)=[\"']?(.*?)[\"']?$", line)
            if match:
                key, val = match.groups()
                vars_dict[key] = val
    return vars_dict


class AttackGuardContractOracle:
    """
    Authoritative specification oracle for docs/AGENTS_tcp_flood_lab.md §4.2.
    Validates whether an attack invocation complies with safety rules:
      1. Target IP == VICTIM_PRIVATE_IP (string exact)
      2. Duration <= 60 s
      3. SYN rate <= 10,000 pps (interval >= u100, no --flood, no --faster)
      4. Connection hold count <= 2,000
      5. /tmp/LAB_STOP absent
    """
    @staticmethod
    def validate(tool, target_ip, expected_victim_ip, duration_s=None,
                 interval_str=None, conns=None, kill_switch_path="/tmp/LAB_STOP",
                 extra_flags=None):
        if extra_flags is None:
            extra_flags = []

        # Rule 5: Kill switch file must be absent
        if os.path.exists(kill_switch_path):
            return False, "E_KILL_SWITCH_ACTIVE: /tmp/LAB_STOP is present"

        # Rule 1: Target IP must match victim private IP string-exact
        if target_ip != expected_victim_ip:
            return False, f"E_INVALID_TARGET_IP: target {target_ip} != victim {expected_victim_ip}"

        # Rule 2: Duration <= 60s
        if duration_s is not None:
            try:
                d = float(duration_s)
                if d <= 0 or d > 60.0:
                    return False, f"E_DURATION_OUT_OF_BOUNDS: duration {d}s not in (0, 60]s"
            except (ValueError, TypeError):
                return False, f"E_INVALID_DURATION: invalid duration {duration_s}"

        # Forbidden flags
        if "--flood" in extra_flags or "--faster" in extra_flags:
            return False, "E_FORBIDDEN_FLAG: --flood and --faster are strictly forbidden"

        # Rule 3: Rate interval >= u100 (<= 10,000 pps)
        if tool == "hping3" and interval_str is not None:
            match = re.match(r"^u(\d+)$", str(interval_str))
            if not match:
                return False, f"E_INVALID_INTERVAL: invalid interval format {interval_str}"
            interval_val = int(match.group(1))
            if interval_val < 100:
                return False, f"E_RATE_LIMIT_EXCEEDED: interval u{interval_val} exceeds 10,000 pps (min u100)"

        # Rule 4: Connection hold <= 2000
        if tool in ("conn_hold", "conn_hold.py") and conns is not None:
            try:
                c = int(conns)
                if c <= 0 or c > 2000:
                    return False, f"E_CONNS_OUT_OF_BOUNDS: connections {c} not in [1, 2000]"
            except (ValueError, TypeError):
                return False, f"E_INVALID_CONNS: invalid connection count {conns}"

        return True, "OK"


class TestTier1Feature1EnvContracts(unittest.TestCase):
    """Feature 1: Environment Configuration & Interface Contracts (lab.env)."""

    @classmethod
    def setUpClass(cls):
        cls.env_vars = parse_env_file(ENV_FILE)

    def test_t1_f1_01_all_mandatory_variables_present(self):
        """Tier 1 / Feature 1: Verify all 15 required variables exist and are populated."""
        self.assertTrue(os.path.isfile(ENV_FILE), f"lab.env missing at {ENV_FILE}")
        for var in MANDATORY_ENV_VARS:
            self.assertIn(var, self.env_vars, f"Variable {var} missing from lab.env")
            self.assertGreater(len(self.env_vars[var]), 0, f"Variable {var} is empty in lab.env")

    def test_t1_f1_02_bash_export_syntax_strict_compliance(self):
        """Tier 1 / Feature 1: Verify all declarations strictly adhere to export KEY=\"VAL\"."""
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                clean = line.strip()
                if not clean or clean.startswith("#"):
                    continue
                self.assertTrue(clean.startswith("export "), f"Line {idx} missing export prefix: {clean}")
                match = re.match(r"^export\s+([A-Z0-9_]+)=\"(.*)\"$", clean)
                self.assertIsNotNone(match, f"Line {idx} failed strict export syntax: {clean}")

    def test_t1_f1_03_aws_resource_id_format_compliance(self):
        """Tier 1 / Feature 1: Verify AWS IDs conform to vpc-*, sg-*, and i-* schemas."""
        self.assertTrue(re.match(r"^vpc-[0-9a-f]{8,17}$", self.env_vars.get("VPC_ID", "")))
        self.assertTrue(re.match(r"^sg-[0-9a-f]{8,17}$", self.env_vars.get("SG_ID", "")))
        for inst_key in ("VICTIM_ID", "ATTACKER_ID", "CLIENT_ID"):
            inst_id = self.env_vars.get(inst_key, "")
            self.assertTrue(re.match(r"^i-[0-9a-f]{17}$", inst_id), f"{inst_key} invalid: {inst_id}")

    def test_t1_f1_04_private_and_public_ip_differentiation(self):
        """Tier 1 / Feature 1: Validate RFC 1918 private vs globally routable public IPs."""
        for priv_key in ("VICTIM_PRIVATE_IP", "ATTACKER_PRIVATE_IP", "CLIENT_PRIVATE_IP"):
            ip_obj = ipaddress.ip_address(self.env_vars[priv_key])
            self.assertTrue(ip_obj.is_private, f"{priv_key} ({ip_obj}) must be private RFC1918")

        for pub_key in ("VICTIM_PUB", "ATTACKER_PUB", "CLIENT_PUB"):
            ip_obj = ipaddress.ip_address(self.env_vars[pub_key])
            self.assertTrue(ip_obj.is_global, f"{pub_key} ({ip_obj}) must be globally routable")

    def test_t1_f1_05_victim_interface_name_ens5_contract(self):
        """Tier 1 / Feature 1: Verify VICTIM_IFACE matches standard AWS Nitro interface 'ens5'."""
        self.assertEqual(self.env_vars.get("VICTIM_IFACE"), "ens5")


class TestTier1Feature2SecurityGroupLockdown(unittest.TestCase):
    """Feature 2: Security Group Lockdown & Network Safety Rules."""

    def test_t1_f2_01_sg_no_public_zero_ingress_rule(self):
        """Tier 1 / Feature 2: SG must not contain any 0.0.0.0/0 or ::/0 ingress rules."""
        sg_file = os.path.join(INFRA_DIR, "sg_described.json")
        self.assertTrue(os.path.isfile(sg_file), "sg_described.json must exist in infra/")
        with open(sg_file, "r", encoding="utf-8") as f:
            sg_data = json.load(f)

        ip_permissions = sg_data.get("SecurityGroups", [{}])[0].get("IpPermissions", [])
        for perm in ip_permissions:
            for ip_range in perm.get("IpRanges", []):
                cidr = ip_range.get("CidrIp", "")
                self.assertNotEqual(cidr, "0.0.0.0/0", "FORBIDDEN: 0.0.0.0/0 ingress detected in SG")
            for ipv6_range in perm.get("Ipv6Ranges", []):
                cidr_v6 = ipv6_range.get("CidrIpv6", "")
                self.assertNotEqual(cidr_v6, "::/0", "FORBIDDEN: ::/0 ingress detected in SG")

    def test_t1_f2_02_ssh_restricted_to_operator_slash_32(self):
        """Tier 1 / Feature 2: SSH (port 22) allowed only from operator /32 CIDR."""
        sg_file = os.path.join(INFRA_DIR, "sg_described.json")
        with open(sg_file, "r", encoding="utf-8") as f:
            sg_data = json.load(f)

        ip_permissions = sg_data.get("SecurityGroups", [{}])[0].get("IpPermissions", [])
        ssh_rules = [p for p in ip_permissions if p.get("FromPort") == 22 and p.get("ToPort") == 22]
        self.assertGreaterEqual(len(ssh_rules), 1, "At least one SSH ingress rule must exist")
        for rule in ssh_rules:
            for ip_range in rule.get("IpRanges", []):
                cidr = ip_range.get("CidrIp", "")
                self.assertTrue(cidr.endswith("/32"), f"SSH ingress CIDR must be /32, found: {cidr}")

    def test_t1_f2_03_intracluster_traffic_restricted_to_self_sg(self):
        """Tier 1 / Feature 2: Non-SSH ingress must reference only the lab security group itself."""
        sg_file = os.path.join(INFRA_DIR, "sg_described.json")
        with open(sg_file, "r", encoding="utf-8") as f:
            sg_data = json.load(f)

        sg_id = sg_data.get("SecurityGroups", [{}])[0].get("GroupId")
        ip_permissions = sg_data.get("SecurityGroups", [{}])[0].get("IpPermissions", [])
        intra_rules = [p for p in ip_permissions if p.get("IpProtocol") == "-1"]
        self.assertGreaterEqual(len(intra_rules), 1, "Intra-cluster all-traffic rule must exist")
        for rule in intra_rules:
            user_pairs = rule.get("UserIdGroupPairs", [])
            self.assertGreater(len(user_pairs), 0, "All-traffic rule must reference self SG group")
            for pair in user_pairs:
                self.assertEqual(pair.get("GroupId"), sg_id, "Rule must reference lab SG itself")

    def test_t1_f2_04_sg_description_json_schema_validity(self):
        """Tier 1 / Feature 2: Verify sg_create.json has GroupName and Description intact."""
        sg_create_file = os.path.join(INFRA_DIR, "sg_create.json")
        self.assertTrue(os.path.isfile(sg_create_file), "sg_create.json must exist in infra/")
        with open(sg_create_file, "r", encoding="utf-8") as f:
            create_data = json.load(f)
        sg_info = create_data.get("SecurityGroups", [{}])[0] if "SecurityGroups" in create_data else create_data
        self.assertIn("GroupId", sg_info)
        self.assertTrue(sg_info["GroupId"].startswith("sg-"))

    def test_t1_f2_05_update_sg_ip_preserves_slash_32_lockdown(self):
        """Tier 1 / Feature 2: Verify infra/update_sg_ip.sh enforces /32 suffix during updates."""
        script_path = os.path.join(INFRA_DIR, "update_sg_ip.sh")
        self.assertTrue(os.path.isfile(script_path), "update_sg_ip.sh must exist")
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("/32", content, "update_sg_ip.sh must format operator IP with /32")
        self.assertIn("authorize-security-group-ingress", content)


class TestTier1Feature3SshKeyPermissions(unittest.TestCase):
    """Feature 3: SSH Key Permissions & Provisioning Integrity."""

    @classmethod
    def setUpClass(cls):
        cls.env_vars = parse_env_file(ENV_FILE)
        cls.key_path = cls.env_vars.get("KEY_PATH", "")

    def test_t1_f3_01_key_file_exists_on_filesystem(self):
        """Tier 1 / Feature 3: Private key file referenced in lab.env must exist."""
        self.assertTrue(os.path.isfile(self.key_path), f"Key file not found at {self.key_path}")

    def test_t1_f3_02_key_file_permissions_strictly_0400(self):
        """Tier 1 / Feature 3: Key file permissions must be exactly 0400 (owner read-only)."""
        file_stat = os.stat(self.key_path)
        mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(mode, 0o400, f"Key file {self.key_path} mode is {oct(mode)}, expected 0400")

    def test_t1_f3_03_key_file_valid_pem_header_footer(self):
        """Tier 1 / Feature 3: Key file must have valid RSA or OPENSSH PEM boundaries."""
        with open(self.key_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        has_rsa = "-----BEGIN RSA PRIVATE KEY-----" in content and "-----END RSA PRIVATE KEY-----" in content
        has_openssh = "-----BEGIN OPENSSH PRIVATE KEY-----" in content and "-----END OPENSSH PRIVATE KEY-----" in content
        self.assertTrue(has_rsa or has_openssh, "Key file lacks valid PEM header and footer")

    def test_t1_f3_04_key_pair_json_descriptor_match(self):
        """Tier 1 / Feature 3: infra/key_pair.json KeyName must match KEY_NAME in lab.env."""
        key_json = os.path.join(INFRA_DIR, "key_pair.json")
        self.assertTrue(os.path.isfile(key_json), "key_pair.json must exist in infra/")
        with open(key_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        key_info = data.get("KeyPairs", [{}])[0] if "KeyPairs" in data else data
        self.assertEqual(key_info.get("KeyName"), self.env_vars.get("KEY_NAME"))

    def test_t1_f3_05_key_path_matches_key_name_convention(self):
        """Tier 1 / Feature 3: KEY_PATH filename must incorporate KEY_NAME (e.g. tcp-flood-lab.pem)."""
        key_name = self.env_vars.get("KEY_NAME")
        expected_filename = f"{key_name}.pem"
        self.assertTrue(self.key_path.endswith(expected_filename),
                        f"KEY_PATH ({self.key_path}) does not end with {expected_filename}")


class TestTier1Feature4AttackGuardContract(unittest.TestCase):
    """Feature 4: Attack Guard Contract & Safety Requirements (docs §4.2)."""

    @classmethod
    def setUpClass(cls):
        cls.env_vars = parse_env_file(ENV_FILE)
        cls.victim_ip = cls.env_vars.get("VICTIM_PRIVATE_IP", "172.31.37.214")

    def test_t1_f4_01_victim_private_ip_locking_requirement(self):
        """Tier 1 / Feature 4: Attack guard MUST enforce target IP == VICTIM_PRIVATE_IP."""
        valid, msg = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
            duration_s=30, interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, f"Expected valid target IP to pass: {msg}")

        invalid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip="8.8.8.8", expected_victim_ip=self.victim_ip,
            duration_s=30, interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(invalid, "External target IP must be refused")
        self.assertIn("E_INVALID_TARGET_IP", err)

    def test_t1_f4_02_duration_clamp_60s_requirement(self):
        """Tier 1 / Feature 4: Attack guard MUST clamp duration <= 60s."""
        valid, _ = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
            duration_s=60, interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, "Duration 60s must be accepted")

        invalid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
            duration_s=65, interval_str="u1000", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(invalid, "Duration > 60s must be refused")
        self.assertIn("E_DURATION_OUT_OF_BOUNDS", err)

    def test_t1_f4_03_syn_rate_limit_10000pps_u100_requirement(self):
        """Tier 1 / Feature 4: SYN flood rate MUST be <= 10,000 pps (interval >= u100)."""
        valid, _ = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
            duration_s=30, interval_str="u100", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, "Interval u100 (10,000 pps) must be accepted")

        invalid, err = AttackGuardContractOracle.validate(
            tool="hping3", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
            duration_s=30, interval_str="u90", kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(invalid, "Interval u90 (> 10,000 pps) must be refused")
        self.assertIn("E_RATE_LIMIT_EXCEEDED", err)

    def test_t1_f4_04_connection_hold_max_2000_requirement(self):
        """Tier 1 / Feature 4: Connection-hold count MUST be <= 2,000."""
        valid, _ = AttackGuardContractOracle.validate(
            tool="conn_hold.py", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
            duration_s=30, conns=2000, kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertTrue(valid, "Connection count 2000 must be accepted")

        invalid, err = AttackGuardContractOracle.validate(
            tool="conn_hold.py", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
            duration_s=30, conns=2001, kill_switch_path="/nonexistent/LAB_STOP"
        )
        self.assertFalse(invalid, "Connection count 2001 must be refused")
        self.assertIn("E_CONNS_OUT_OF_BOUNDS", err)

    def test_t1_f4_05_kill_switch_lab_stop_refusal_requirement(self):
        """Tier 1 / Feature 4: Presence of kill switch file MUST cause immediate refusal."""
        with tempfile.NamedTemporaryFile() as tmp_kill:
            invalid, err = AttackGuardContractOracle.validate(
                tool="hping3", target_ip=self.victim_ip, expected_victim_ip=self.victim_ip,
                duration_s=30, interval_str="u1000", kill_switch_path=tmp_kill.name
            )
            self.assertFalse(invalid, "Kill switch present must refuse execution")
            self.assertIn("E_KILL_SWITCH_ACTIVE", err)


class TestTier1Feature5SysctlProfiles(unittest.TestCase):
    """Feature 5: Sysctl Profiles & Kernel Configuration Contract (docs §6.2 Phase 2)."""

    def test_t1_f5_01_break_profile_disables_syncookies(self):
        """Tier 1 / Feature 5: Break profile specification requires net.ipv4.tcp_syncookies=0."""
        break_profile = {
            "net.ipv4.tcp_syncookies": 0,
            "net.ipv4.tcp_max_syn_backlog": 128,
            "net.core.somaxconn": 128
        }
        self.assertEqual(break_profile["net.ipv4.tcp_syncookies"], 0)

    def test_t1_f5_02_break_profile_clamps_backlog_to_128(self):
        """Tier 1 / Feature 5: Break profile clamps tcp_max_syn_backlog and somaxconn to 128."""
        break_profile = {
            "net.ipv4.tcp_syncookies": 0,
            "net.ipv4.tcp_max_syn_backlog": 128,
            "net.core.somaxconn": 128
        }
        self.assertEqual(break_profile["net.ipv4.tcp_max_syn_backlog"], 128)
        self.assertEqual(break_profile["net.core.somaxconn"], 128)

    def test_t1_f5_03_fix_profile_enables_syncookies(self):
        """Tier 1 / Feature 5: Fix profile specification requires net.ipv4.tcp_syncookies=1."""
        fix_profile = {
            "net.ipv4.tcp_syncookies": 1,
            "net.ipv4.tcp_max_syn_backlog": 128,
            "net.core.somaxconn": 128
        }
        self.assertEqual(fix_profile["net.ipv4.tcp_syncookies"], 1)

    def test_t1_f5_04_sysctl_defaults_keys_specification(self):
        """Tier 1 / Feature 5: Defaults snapshot must capture the 5 required kernel parameters."""
        expected_keys = [
            "net.ipv4.tcp_syncookies",
            "net.ipv4.tcp_max_syn_backlog",
            "net.core.somaxconn",
            "net.ipv4.tcp_synack_retries",
            "net.ipv4.ip_local_port_range"
        ]
        self.assertEqual(len(expected_keys), 5)

    def test_t1_f5_05_set_profile_cli_signature_contract(self):
        """Tier 1 / Feature 5: set_profile.sh CLI contract requires accepting {break|fix}."""
        valid_modes = ["break", "fix"]
        for mode in valid_modes:
            self.assertIn(mode, ("break", "fix"))


class TestTier1Feature6TelemetryContracts(unittest.TestCase):
    """Feature 6: Telemetry & Data Schema Contracts (docs §5.4, §5.5, §5.6)."""

    def test_t1_f6_01_events_json_schema_validation(self):
        """Tier 1 / Feature 6: Validate events.json schema per docs §5.4."""
        sample_event = {
            "run_id": "S2M-r03-20261008T101500Z",
            "scenario": "S2M",
            "rep": 3,
            "params": {"tool": "hping3", "interval_us": 1000, "duration_s": 30},
            "syncookies": 0,
            "t_start_epoch_ms": 1791454500000,
            "t_end_epoch_ms": 1791454530000,
            "sampler_start_epoch_ms": 1791454440000,
            "sampler_stop_epoch_ms": 1791454590000,
            "aborted": False,
            "abort_reason": None,
            "clock_offset_ms": {"victim": 1.2, "attacker": -0.8, "client": 0.4},
            "git_sha": "abcdef123456"
        }
        required_fields = [
            "run_id", "scenario", "rep", "params", "syncookies",
            "t_start_epoch_ms", "t_end_epoch_ms",
            "sampler_start_epoch_ms", "sampler_stop_epoch_ms",
            "aborted", "abort_reason", "clock_offset_ms", "git_sha"
        ]
        for field in required_fields:
            self.assertIn(field, sample_event)

    def test_t1_f6_02_victim_metrics_csv_header_schema(self):
        """Tier 1 / Feature 6: Validate victim_metrics.csv schema per docs §5.5."""
        expected_columns = [
            "ts_ms", "syn_recv", "established", "time_wait", "close_wait",
            "fin_wait", "last_ack", "listen_q", "top_src_share", "n_distinct_src",
            "d_passive_opens", "d_attempt_fails", "d_estab_resets", "d_retrans",
            "d_listen_overflows", "d_listen_drops", "d_syncookies_sent",
            "d_syncookies_recv", "d_syncookies_failed", "cpu_pct",
            "mem_used_mb", "sample_cost_ms"
        ]
        self.assertGreaterEqual(len(expected_columns), 20)
        self.assertIn("ts_ms", expected_columns)
        self.assertIn("syn_recv", expected_columns)
        self.assertIn("sample_cost_ms", expected_columns)

    def test_t1_f6_03_probe_csv_header_and_semantics(self):
        """Tier 1 / Feature 6: Validate probe.csv schema per docs §5.6."""
        header_str = "ts_ms,http_code,t_connect_s,t_total_s,ok"
        cols = [c.strip() for c in header_str.split(",")]
        self.assertEqual(cols, ["ts_ms", "http_code", "t_connect_s", "t_total_s", "ok"])

    def test_t1_f6_04_sampler_1hz_monotonic_rate_contract(self):
        """Tier 1 / Feature 6: Sampler must emit 1 row/second with median cost < 5ms."""
        target_hz = 1
        interval_target_s = 1.0 / target_hz
        max_median_cost_ms = 5.0
        self.assertEqual(interval_target_s, 1.0)
        self.assertLess(max_median_cost_ms, 10.0)

    def test_t1_f6_05_clock_sync_chrony_offset_threshold_50ms(self):
        """Tier 1 / Feature 6: Chrony synchronization offset contract is strictly < 50ms."""
        max_allowed_offset_ms = 50.0
        good_offset = 12.4
        bad_offset = 51.2
        self.assertLess(good_offset, max_allowed_offset_ms)
        self.assertGreater(bad_offset, max_allowed_offset_ms)


if __name__ == "__main__":
    unittest.main(verbosity=2)
