# Update 008 — AWS Testbed Running & Milestone 1 Verification

- **Date / Time:** 2026-10-07 12:32 IST
- **Status:** Milestone 1 (AWS Provisioning) Active — EC2 Nodes Running
- **Manager:** Autonomous Lead Coordinator
- **Active Worker:** `worker_m1`
- **Reference Spec:** [docs/AGENTS_tcp_flood_lab.md](file:///Users/raja/Documents/syn-edge-flooding/docs/AGENTS_tcp_flood_lab.md)

---

## 1. Cloud Infrastructure Provisioned & Verified
All three target EC2 instances and networking components have been provisioned in `ap-south-1a` (`subnet-0709c5a163cc423bb`):

| Node | Instance ID | Private IPv4 | Public IPv4 | OS & Architecture | Tags |
|---|---|---|---|---|---|
| **victim** | `i-0f89c07ce382931f2` | `172.31.37.214` | `13.235.246.92` | Ubuntu 24.04 LTS (x86_64) | `Name=victim`, `Project=tcp-flood-lab` |
| **attacker** | `i-03e8f67a9cb58c94a` | `172.31.42.168` | `65.2.190.166` | Ubuntu 24.04 LTS (x86_64) | `Name=attacker`, `Project=tcp-flood-lab` |
| **client** | `i-07f191b24634a44ca` | `172.31.41.87` | `13.206.119.8` | Ubuntu 24.04 LTS (x86_64) | `Name=client`, `Project=tcp-flood-lab` |

---

## 2. Security & Guardrail Compliance
- **Security Group:** `lab-sg` (`sg-09e89875382c47277`) contains strictly:
  - TCP port 22 ingress from operator IP `152.57.107.6/32` only.
  - All-traffic ingress from self (`sg-09e89875382c47277`).
  - **Zero** `0.0.0.0/0` or `::/0` ingress rules present.
- **SSH Credentials:** Key pair `tcp-flood-lab` saved to `~/.ssh/tcp-flood-lab.pem` with `chmod 400` permissions.
- **Cost Controls:** All instances tagged `Project=tcp-flood-lab` and configured with `--credit-specification CpuCredits=standard`.

---

## 3. Current In-Flight Actions
`worker_m1` is currently:
1. Verifying SSH daemon responsiveness and retrieving network interface name (`VICTIM_IFACE`).
2. Exporting all 15 required environment variables to `lab.env`.
3. Running bi-directional ICMP pings over private IPs (`attacker` -> `victim`, `client` -> `victim`).
4. Executing `infra/verify_m1_safety.sh` to validate all Milestone 1 acceptance criteria.

---

## 4. Next Milestone
Upon completion of Milestone 1 handoff, `orchestrator_1` will trigger Milestone 2: deploying Nginx, establishing sysctl break/fix profiles, and testing fail-safe attack guards on `attacker`.

