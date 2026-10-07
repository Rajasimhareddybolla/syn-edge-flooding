#!/usr/bin/env python3
"""
tests/test_m1_contracts_empirical.py

Milestone 1 Empirical Contract and Safety Stress-Test Suite
Authored by challenger_m1_2.
"""

import os
import re
import sys
import stat
import ipaddress
import subprocess
import tempfile
import unittest

LAB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_FILE = os.path.join(LAB_ROOT, "lab.env")

REQUIRED_VARS = [
    "AWS_REGION", "VPC_ID", "SG_ID", "KEY_NAME", "KEY_PATH",
    "VICTIM_ID", "ATTACKER_ID", "CLIENT_ID",
    "VICTIM_PUB", "ATTACKER_PUB", "CLIENT_PUB",
    "VICTIM_PRIVATE_IP", "ATTACKER_PRIVATE_IP", "CLIENT_PRIVATE_IP",
    "VICTIM_IFACE"
]

class TestM1ContractsEmpirical(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(ENV_FILE):
            raise FileNotFoundError(f"lab.env not found at {ENV_FILE}")
        cls.env_vars = cls._parse_env_file(ENV_FILE)

    @staticmethod
    def _parse_env_file(path):
        """Parse bash export statements with python regex."""
        vars_dict = {}
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r"^export\s+([A-Za-z_][A-Za-z0-9_]*)=[\"']?(.*?)[\"']?$", line)
                if match:
                    key, val = match.groups()
                    vars_dict[key] = val
                else:
                    raise ValueError(f"Line {line_no} does not match export VAR=\"VAL\" pattern: {line}")
        return vars_dict

    def test_01_all_required_variables_present_and_non_empty(self):
        """Verify all 15 required variables exist and are non-empty."""
        for var in REQUIRED_VARS:
            self.assertIn(var, self.env_vars, f"Variable {var} is missing from lab.env")
            self.assertTrue(len(self.env_vars[var]) > 0, f"Variable {var} is empty in lab.env")

    def test_02_clean_bash_subshell_sourcing_set_u(self):
        """Verify lab.env sources cleanly under bash -u without unbound variable errors."""
        cmd = f"set -u && source '{ENV_FILE}'"
        result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Bash sourcing under set -u failed: {result.stderr}")

    def test_03_aws_identifiers_schema(self):
        """Verify AWS identifiers follow correct naming and ID formats."""
        self.assertRegex(self.env_vars["AWS_REGION"], r"^[a-z]{2}-[a-z]+-\d+$")
        self.assertRegex(self.env_vars["VPC_ID"], r"^vpc-[0-9a-f]{8,17}$")
        self.assertRegex(self.env_vars["SG_ID"], r"^sg-[0-9a-f]{8,17}$")
        self.assertRegex(self.env_vars["VICTIM_ID"], r"^i-[0-9a-f]{8,17}$")
        self.assertRegex(self.env_vars["ATTACKER_ID"], r"^i-[0-9a-f]{8,17}$")
        self.assertRegex(self.env_vars["CLIENT_ID"], r"^i-[0-9a-f]{8,17}$")
        self.assertEqual(self.env_vars["VICTIM_IFACE"], "ens5")

    def test_04_ip_conformance_and_classification(self):
        """Strictly validate all 6 IP addresses using ipaddress module and regex."""
        # IPv4 regex matching standard dotted quad with 0-255 bounds
        strict_ipv4_regex = re.compile(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        )

        # 1. Private IPs
        private_vars = ["VICTIM_PRIVATE_IP", "ATTACKER_PRIVATE_IP", "CLIENT_PRIVATE_IP"]
        for var in private_vars:
            ip_str = self.env_vars[var]
            self.assertRegex(ip_str, strict_ipv4_regex, f"{var} '{ip_str}' is not a valid IPv4 string")
            ip = ipaddress.IPv4Address(ip_str)
            self.assertTrue(ip.is_private, f"{var} '{ip_str}' is not an RFC1918 private IP")
            # In AWS default VPC ap-south-1, subnet is typically in 172.31.0.0/16
            vpc_net = ipaddress.IPv4Network("172.31.0.0/16")
            self.assertIn(ip, vpc_net, f"{var} '{ip_str}' is not in default VPC subnet 172.31.0.0/16")

        # 2. Public IPs
        public_vars = ["VICTIM_PUB", "ATTACKER_PUB", "CLIENT_PUB"]
        for var in public_vars:
            ip_str = self.env_vars[var]
            self.assertRegex(ip_str, strict_ipv4_regex, f"{var} '{ip_str}' is not a valid IPv4 string")
            ip = ipaddress.IPv4Address(ip_str)
            self.assertFalse(ip.is_private, f"{var} '{ip_str}' should be public, but is private")
            self.assertFalse(ip.is_loopback, f"{var} '{ip_str}' is loopback")
            self.assertFalse(ip.is_link_local, f"{var} '{ip_str}' is link local")
            self.assertFalse(ip.is_multicast, f"{var} '{ip_str}' is multicast")

        # 3. Pairwise distinctness
        all_privates = [self.env_vars[v] for v in private_vars]
        self.assertEqual(len(set(all_privates)), 3, "Private IPs must all be distinct")
        all_publics = [self.env_vars[v] for v in public_vars]
        self.assertEqual(len(set(all_publics)), 3, "Public IPs must all be distinct")

    def test_05_ssh_key_file_and_permissions(self):
        """Verify SSH key file existence, octal permissions 400, and PEM header."""
        key_path = os.path.expanduser(self.env_vars["KEY_PATH"])
        self.assertTrue(os.path.isfile(key_path), f"Key file does not exist at {key_path}")
        mode = stat.S_IMODE(os.stat(key_path).st_mode)
        self.assertEqual(oct(mode), oct(0o400), f"Key file permissions {oct(mode)} != 0o400")

        with open(key_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("BEGIN RSA PRIVATE KEY", content)

    def test_06_validate_lab_env_script_clean_execution(self):
        """Test tools/validate_lab_env.sh on the actual lab.env (must exit 0)."""
        validator = os.path.join(LAB_ROOT, "tools", "validate_lab_env.sh")
        res = subprocess.run(["bash", validator, ENV_FILE], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"validate_lab_env.sh failed: {res.stderr}")
        self.assertIn("PASS: lab.env is complete and syntactically valid.", res.stdout)

    def test_07_validate_lab_env_fault_injection(self):
        """Adversarially inject faults to verify validate_lab_env.sh catches all errors."""
        validator = os.path.join(LAB_ROOT, "tools", "validate_lab_env.sh")

        # Fault 1: Non-existent file
        res = subprocess.run(["bash", validator, "/nonexistent/path/to/env"], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("does not exist", res.stderr)

        # Fault 2: Missing required variable
        with open(ENV_FILE, "r") as f:
            original_lines = f.readlines()

        for var_to_remove in ["VICTIM_PRIVATE_IP", "KEY_PATH", "SG_ID"]:
            tampered_lines = [l for l in original_lines if not l.startswith(f"export {var_to_remove}=")]
            with tempfile.NamedTemporaryFile("w", delete=False) as tf:
                tf.writelines(tampered_lines)
                tf_path = tf.name
            try:
                res = subprocess.run(["bash", validator, tf_path], capture_output=True, text=True)
                self.assertNotEqual(res.returncode, 0, f"Validator did not fail when {var_to_remove} was removed")
                self.assertIn(f"Required variable '{var_to_remove}' is unset or empty", res.stderr)
            finally:
                os.remove(tf_path)

        # Fault 3: Empty required variable
        for var_to_empty in ["CLIENT_PUB", "AWS_REGION"]:
            tampered_lines = [
                f"export {var_to_empty}=\"\"\n" if l.startswith(f"export {var_to_empty}=") else l
                for l in original_lines
            ]
            with tempfile.NamedTemporaryFile("w", delete=False) as tf:
                tf.writelines(tampered_lines)
                tf_path = tf.name
            try:
                res = subprocess.run(["bash", validator, tf_path], capture_output=True, text=True)
                self.assertNotEqual(res.returncode, 0, f"Validator did not fail when {var_to_empty} was empty")
                self.assertIn(f"Required variable '{var_to_empty}' is unset or empty", res.stderr)
            finally:
                os.remove(tf_path)

        # Fault 4: KEY_PATH points to non-existent file
        tampered_lines = [
            f"export KEY_PATH=\"/tmp/nonexistent_fake_key.pem\"\n" if l.startswith("export KEY_PATH=") else l
            for l in original_lines
        ]
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            tf.writelines(tampered_lines)
            tf_path = tf.name
        try:
            res = subprocess.run(["bash", validator, tf_path], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0, "Validator did not fail when KEY_PATH pointed to nonexistent file")
            self.assertIn("does not point to an existing file", res.stderr)
        finally:
            os.remove(tf_path)

    def test_08_update_sg_ip_edge_case_regex_robustness(self):
        """Stress-test IP extraction regex used in infra/update_sg_ip.sh against edge cases."""
        ip_regex = re.compile(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$")

        # Valid IPs
        self.assertTrue(ip_regex.match("152.57.107.6"))
        self.assertTrue(ip_regex.match("1.1.1.1"))

        # Malformed / adversarial inputs that MUST be rejected
        adversarial_inputs = [
            "",                       # empty response / timeout
            "   ",                    # pure whitespace
            "2001:db8::1",            # IPv6 address
            "<html>Error 502</html>", # proxy / gateway error page
            "152.57.107.6\n1.2.3.4",  # newline injection
            "152.57.107.6; rm -rf /", # command injection attempt
            "152.57.107.6/32",        # CIDR format before sanitization
            "152.57.107",             # truncated 3 octets
            "152.57.107.6.9",         # 5 octets
            "abc.def.ghi.jkl",        # non-digit octets
            "-1.0.0.1",               # negative number
        ]

        for bad_input in adversarial_inputs:
            # Notice in update_sg_ip.sh: NEW_IP=$(... | tr -d '[:space:]')
            sanitized = re.sub(r"\s+", "", bad_input)
            self.assertFalse(
                bool(ip_regex.match(sanitized)),
                f"Regex failed to reject adversarial input: {bad_input!r} (sanitized: {sanitized!r})"
            )

        # Boundary note: Note that ^[0-9]{1,3}... will accept "999.999.999.999".
        # Check whether an octet > 255 matches the simple bash regex:
        simple_match = bool(ip_regex.match("999.999.999.999"))
        self.assertTrue(
            simple_match,
            "Documented caveat: Bash regex [0-9]{1,3} matches 999.999.999.999 (not octet bounded)."
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
