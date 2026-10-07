#!/usr/bin/env python3
"""
tests/test_update_sg_ip_edge_cases.py

Adversarial edge-case test suite for infra/update_sg_ip.sh.
Authored by challenger_m1_2.
"""

import os
import re
import subprocess
import tempfile
import unittest

LAB_ROOT = "/Users/raja/Documents/syn-edge-flooding"
UPDATE_SCRIPT = os.path.join(LAB_ROOT, "infra", "update_sg_ip.sh")

class TestUpdateSgIpEdgeCases(unittest.TestCase):

    def test_01_missing_lab_env_handled_gracefully(self):
        """Verify update_sg_ip.sh terminates with code 1 if lab.env is missing."""
        # Run in a sandbox directory where lab.env doesn't exist
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock script with modified LAB_ROOT
            with open(UPDATE_SCRIPT, "r") as f:
                content = f.read()
            tampered = content.replace(f'LAB_ROOT="{LAB_ROOT}"', f'LAB_ROOT="{tmpdir}"')
            test_script = os.path.join(tmpdir, "test_update.sh")
            with open(test_script, "w") as f:
                f.write(tampered)
            os.chmod(test_script, 0o755)

            res = subprocess.run(["bash", test_script], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("not found", res.stderr)

    def test_02_curl_failure_empty_ip_handled_gracefully(self):
        """Verify update_sg_ip.sh terminates with code 1 if curl returns empty string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(UPDATE_SCRIPT, "r") as f:
                content = f.read()
            # Mock curl to return nothing
            tampered = content.replace("curl -s https://checkip.amazonaws.com", "echo ''")
            test_script = os.path.join(tmpdir, "test_update.sh")
            with open(test_script, "w") as f:
                f.write(tampered)
            os.chmod(test_script, 0o755)

            res = subprocess.run(["bash", test_script], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Failed to resolve valid operator IPv4 address", res.stderr)

    def test_03_curl_returns_html_error_handled_gracefully(self):
        """Verify update_sg_ip.sh terminates with code 1 if curl returns HTML error page."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(UPDATE_SCRIPT, "r") as f:
                content = f.read()
            tampered = content.replace("curl -s https://checkip.amazonaws.com", "echo '<html>502 Bad Gateway</html>'")
            test_script = os.path.join(tmpdir, "test_update.sh")
            with open(test_script, "w") as f:
                f.write(tampered)
            os.chmod(test_script, 0o755)

            res = subprocess.run(["bash", test_script], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Failed to resolve valid operator IPv4 address", res.stderr)

    def test_04_curl_returns_ipv6_handled_gracefully(self):
        """Verify update_sg_ip.sh terminates with code 1 if curl returns an IPv6 address."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(UPDATE_SCRIPT, "r") as f:
                content = f.read()
            tampered = content.replace("curl -s https://checkip.amazonaws.com", "echo '2600:1f18:418:8f00::1'")
            test_script = os.path.join(tmpdir, "test_update.sh")
            with open(test_script, "w") as f:
                f.write(tampered)
            os.chmod(test_script, 0o755)

            res = subprocess.run(["bash", test_script], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Failed to resolve valid operator IPv4 address", res.stderr)

    def test_05_curl_returns_newline_injected_ips_handled_gracefully(self):
        """Verify update_sg_ip.sh terminates with code 1 on multi-line/injected output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(UPDATE_SCRIPT, "r") as f:
                content = f.read()
            tampered = content.replace("curl -s https://checkip.amazonaws.com", "echo -e '152.57.107.6\n152.57.129.48'")
            test_script = os.path.join(tmpdir, "test_update.sh")
            with open(test_script, "w") as f:
                f.write(tampered)
            os.chmod(test_script, 0o755)

            res = subprocess.run(["bash", test_script], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Failed to resolve valid operator IPv4 address", res.stderr)

    def test_06_cgnat_dual_egress_revocation_risk_analysis(self):
        """
        Adversarial simulation of the dual-egress / CGNAT issue:
        Demonstrate that if SG has both HTTPS checkip (152.57.107.6/32) and SSH TCP egress (152.57.129.48/32),
        the current loop will schedule the SSH TCP egress IP for deletion!
        """
        current_cidrs = ["152.57.107.6/32", "152.57.129.48/32"]
        detected_ip = "152.57.107.6"

        revoked_cidrs = []
        for cidr in current_cidrs:
            if cidr != f"{detected_ip}/32":
                revoked_cidrs.append(cidr)

        self.assertIn("152.57.129.48/32", revoked_cidrs,
            "CRITICAL VULNERABILITY: update_sg_ip.sh revokes 152.57.129.48/32, which is the active SSH egress IP!"
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
