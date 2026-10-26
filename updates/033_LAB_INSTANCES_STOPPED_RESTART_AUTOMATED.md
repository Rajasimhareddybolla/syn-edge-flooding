# Update 033 — EC2 Instances Safely Stopped; Automated Restart Tooling Deployed

**Time:** 2026-10-07T17:05:00Z (22:35 IST)  
**Phase:** Phase 10 — Cost Preservation & Reconnection Tooling  
**Status:** 🟢 INSTANCES STOPPED (0 COMPUTE CHARGES ACCRUING)  

---

## 1. Action Taken

Per operator instruction, the 3 AWS EC2 instances have been transitioned to the `stopped` state rather than permanently terminated:
- **Victim:** `i-0f89c07ce382931f2` (State: `stopped`)
- **Attacker:** `i-03e8f67a9cb58c94a` (State: `stopped`)
- **Client:** `i-07f191b24634a44ca` (State: `stopped`)

**Compute charges are immediately halted.** Storage and configurations remain completely intact.

---

## 2. Automated Lifecycle Scripts

Two dedicated scripts have been provided in `infra/`:

1. **Restart Script (`infra/restart_lab.sh`):**
   - Powers on all 3 instances via `aws ec2 start-instances`.
   - Waits for instances to reach `running` state.
   - Automatically queries newly assigned dynamic public IPv4 addresses.
   - Refreshes `lab.env` with the updated public IPs (preserving private IPs and keys).
   - Executes `infra/update_sg_ip.sh` to update Security Group rules with the current operator IP.
   - Verifies SSH reachability across all 3 nodes.

   **Usage:**
   ```bash
   bash infra/restart_lab.sh
   ```

2. **Stop Script (`infra/stop_lab.sh`):**
   - Safely halts all 3 instances via `aws ec2 stop-instances` and waits for `stopped` state.

   **Usage:**
   ```bash
   bash infra/stop_lab.sh
   ```

