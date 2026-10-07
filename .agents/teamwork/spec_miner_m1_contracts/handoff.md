# Handoff Report — Milestone 1 Contract Specifications

**Agent:** `spec_miner_m1_contracts`  
**Recipient:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Mission:** Extract and formalize exact file contracts, schemas, and acceptance criteria for Milestone 1.  
**Delivered Specification Artifact:** `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m1_contracts/spec_m1_contracts.md`  

---

## 1. Observation

Direct observations from the authoritative sources and environment:

1. **`ORIGINAL_REQUEST.md` (lines 13–15, 30–34):**
   - R1: "Provision an isolated 3-node AWS EC2 testbed (victim, attacker, client; t3.micro Ubuntu 24.04 in default VPC) in accordance with the safety guardrails in docs/AGENTS_tcp_flood_lab.md."
   - AC: "AWS Security Group contains no 0.0.0.0/0 ingress rules; SSH allowed only from current operator /32."
   - AC: "lab.env generated with private IPs; inter-node reachability verified via ICMP ping."
2. **`PROJECT.md` (lines 65, 74–76, 104–118):**
   - M1 Scope: "Git repo init, local tools (`matplotlib`), AWS SG `lab-sg` (/32 only), EC2 key pair, launch 3 `t3.micro` nodes in `ap-south-1a`, generate `lab.env`, ICMP verification, `STATE.md`, `LAB_LOG.md`."
   - M1 -> M2 Contract: "`lab.env` exports: `AWS_REGION`, `VPC_ID`, `SG_ID`, `KEY_NAME`, `KEY_PATH`, `VICTIM_ID`, `ATTACKER_ID`, `CLIENT_ID`, `VICTIM_PUB`, `ATTACKER_PUB`, `CLIENT_PUB`, `VICTIM_PRIVATE_IP`, `ATTACKER_PRIVATE_IP`, `CLIENT_PRIVATE_IP`, `VICTIM_IFACE`."
3. **`docs/AGENTS_tcp_flood_lab.md`:**
   - Section 5.2 (lines 143–145): Enumerates the 15 mandatory `lab.env` variables.
   - Section 6 Phase 0 (lines 210–219): Identifies preflight steps: AWS STS/region, local tools, analysis libraries, git repo init, `.gitignore` (`*.pem`, `lab.env`, `runs/**/capture.pcap`), `STATE.md`, `LAB_LOG.md`, Human Gate G1.
   - Section 6 Phase 1 (lines 220–235): Identifies AWS provisioning steps: default VPC, operator public IP, `lab-sg` (/32 SSH and self-referential ingress only), `tcp-flood-lab` key pair (`chmod 400`), Ubuntu 24.04 AMI from SSM, 3 `t3.micro` nodes with standard CPU credits in same AZ, `lab.env` collection, SSH verification (`VICTIM_IFACE`), private ICMP ping reachability.
   - Section 4 Safety (lines 91–114): Prohibits `0.0.0.0/0` ingress rules; binds attack tools to victim private IP; requires kill switch `/tmp/LAB_STOP`.
4. **Environment Audit Command Results:**
   - `git status` -> `fatal: not a git repository (or any of the parent directories): .git`
   - `aws configure get region` -> `ap-south-1`
   - `aws sts get-caller-identity` -> `UserId: 204284492825`, `Account: 204284492825`, `Arn: arn:aws:iam::204284492825:root`
   - `curl -s https://checkip.amazonaws.com` -> `152.57.107.6`
   - `aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id` -> `ami-065d2b03fb493085a`
   - `aws ec2 describe-vpcs --filters Name=isDefault,Values=true` -> `vpc-091281d6eb74da886`
   - `aws ec2 describe-subnets ...` -> `subnet-0709c5a163cc423bb` in `ap-south-1a`
   - Framework Python 3.13 check -> `pandas`, `numpy`, `sklearn`, `yaml` present; `matplotlib` raises `ModuleNotFoundError: No module named 'matplotlib'`.

---

## 2. Logic Chain

1. **`lab.env` Schema & Syntax Derivation (linking Observations 1, 2, 3):**
   - The 15 variables mandated in §5.2 and `PROJECT.md` provide all connection coordinates required by downstream modules (Phases 2 through 10).
   - In shell environments, plain `VAR=val` does not propagate to child processes (e.g. `ssh`, `python`, `attack_guard.sh`), whereas `export VAR="val"` guarantees automatic inheritance.
   - Quoting `"~/.ssh/..."` prevents POSIX tilde expansion, which causes `ssh -i "$KEY_PATH"` to fail; therefore, `$HOME/.ssh/tcp-flood-lab.pem` or an absolute path is strictly specified.
   - A standard-library Python regex parser was specified to enable test harnesses and detectors to parse `lab.env` without external dependencies.
2. **`STATE.md` and `LAB_LOG.md` State Machine Formalization (linking Observation 3):**
   - `docs/AGENTS_tcp_flood_lab.md` requires tracking Human Gates G1–G3, Phase gating (Phases 0–10), active resources, and non-repudiation audit logging.
   - `STATE.md` was structured as an operational dashboard capturing Gate states (G1 CONFIRMED, G2 PENDING, G3 NONE), the 11-phase lifecycle matrix, active cloud resource metadata, blockers, and next actions.
   - `LAB_LOG.md` was formalized as an append-only journal with ISO 8601 UTC headers, structured event categories (`[GATE_CONFIRMATION]`, `[PHASE_TRANSITION]`, etc.), and initial seed entries documenting Phase 0 initialization and Gate G1 confirmation.
3. **`.gitignore` Isolation Contract Derivation (linking Observations 3, 4):**
   - `AGENTS.md` explicitly mandates ignoring `*.pem`, `lab.env`, and `runs/**/capture.pcap`.
   - To guard against accidental leaks and repository bloat, the specification expands these rules to cover SSH keys (`*.key`, `*.pub`), environment files (`*.env`), pcaps (`*.pcapng`), archives (`*.tar.gz`), Python cache (`__pycache__/`, `.venv/`), and OS artifacts (`.DS_Store`).
4. **Milestone 1 Acceptance Criteria Checklist (linking Observations 1, 2, 3, 4):**
   - Decomposed Milestone 1 into 7 Phase 0 criteria (AC-0.1 to AC-0.7) and 11 Phase 1 criteria (AC-1.1 to AC-1.11).
   - For every criterion, defined the governing clause, executable CLI verification command, expected output, evaluation logic, failure threshold, and evidence capture artifact.
5. **Specification Discovery Tables (linking all observations):**
   - Formulated 15 discovered features across configuration, state, auditability, safety, security, cost control, networking, and telemetry.
   - Documented 10 edge cases with concrete observed behaviors and required mitigations.

---

## 3. Caveats

1. **Pending Cloud Resource IDs:**
   The exact values for `SG_ID`, `VICTIM_ID`, `ATTACKER_ID`, `CLIENT_ID`, and node IP addresses cannot exist until the Milestone 1 Worker provisions the AWS resources in Phase 1. The specification provides the exact schema, constraints, and template format to be populated.
2. **Python Environment:**
   The specification mandates installing `matplotlib` into Framework Python 3.13 (`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`) via `uv`, since default system Python 3.14 lacks all analysis packages.

---

## 4. Conclusion

The authoritative specification report `spec_m1_contracts.md` has been authored and published to:
`/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m1_contracts/spec_m1_contracts.md`

It provides all required file schemas, syntax standards, initial state templates, `.gitignore` patterns, and an executable 18-point acceptance criteria checklist for Phase 0 and Phase 1. The Milestone 1 Worker and subsequent testing harnesses can immediately consume this specification without ambiguity.

---

## 5. Verification Method

To independently verify the deliverables:

1. **Inspect the formal specification report:**
   ```bash
   cat /Users/raja/Documents/syn-edge-flooding/.agents/teamwork/spec_miner_m1_contracts/spec_m1_contracts.md
   ```
2. **Verify that all 4 required dispatch items are fully addressed:**
   - Section 2: `lab.env` 15-variable schema, `export` syntax, bash/Python loaders, validation script.
   - Section 3: `STATE.md` and `LAB_LOG.md` initial file templates and schemas.
   - Section 4: `.gitignore` verbatim template and pattern verification commands.
   - Section 5: Acceptance criteria checklist (AC-0.1 through AC-0.7; AC-1.1 through AC-1.11) with commands and failure thresholds.
   - Section 6: Specification Miner Discovery Tables (15 Features, 10 Edge Cases).
3. **Verify validation script syntax:**
   The shell snippet in Section 2.4 can be extracted and run against any generated `lab.env` to verify 100% compliance.
4. **Invalidation conditions:**
   The specification would be invalidated if:
   - Any of the 15 mandatory `lab.env` variables are omitted or misspelled.
   - Ingress `0.0.0.0/0` is permitted in `lab-sg`.
   - `KEY_PATH` uses unexpanded tilde syntax in scripts without resolution.
