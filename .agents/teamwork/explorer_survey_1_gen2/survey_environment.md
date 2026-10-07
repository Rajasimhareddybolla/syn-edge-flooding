# Technical Environment & Tooling Audit Report

**Date & Time:** 2026-10-07T06:37:00Z  
**Auditor Agent:** `explorer_survey_1_gen2` (Explorer Archetype)  
**Parent Orchestrator:** `orchestrator_1` (`f6cfd525-c586-41eb-8148-3a42cc6823d8`)  
**Working Directory:** `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_survey_1_gen2`  
**Target Project Directory:** `/Users/raja/Documents/syn-edge-flooding`  
**Governing Specification:** `docs/AGENTS_tcp_flood_lab.md` (Phase 0 Preflight & Section 5 Conventions)

---

## 1. Executive Summary

A comprehensive read-only audit of the AWS cloud environment, local development toolchain, Python data science ecosystem, and repository configuration was performed.

### Key Audit Highlights:
1. **AWS Infrastructure Readiness:** AWS CLI is fully authenticated as root IAM principal in region `ap-south-1`. Default VPC (`vpc-091281d6eb74da886`, `172.31.0.0/16`) and 3 healthy subnets (`ap-south-1a`, `ap-south-1b`, `ap-south-1c`) with 4,091 available IP addresses each are confirmed. Zero active EC2 instances, key pairs, or custom security groups exist, providing a clean slate. Official Ubuntu 24.04 LTS Noble Natively-supported x86_64 AMI was identified via SSM: `ami-065d2b03fb493085a`.
2. **Operator Public IP Verified:** Current operator public IP is `152.57.107.6`. Security group rule must strictly allow `152.57.107.6/32:22` (SSH), forbidding `0.0.0.0/0`.
3. **Local Tooling Health:** Core utilities (`python3`, `pip`, `jq`, `git`, `ssh`, `curl`, `uv`, `wireshark`/`tshark`) are installed and functional.
4. **Python Analysis Package Gap Identified:** Default system Python 3.14 (`/opt/homebrew/bin/python3`) lacks analysis libraries. Secondary Python 3.13 (`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`) has `pandas` (3.0.5), `numpy` (2.5.1), `scikit-learn` (1.9.1), and `pyyaml` (6.0.3) already pre-installed, but lacks `matplotlib`. `uv` (0.11.23) is available for instantaneous resolution.
5. **Repository Layout Gap:** The workspace `/Users/raja/Documents/syn-edge-flooding` is **not yet a git repository** (`fatal: not a git repository`). The standard project directories (`infra/`, `tools/`, `detector/`, `runs/`, `analysis/`, `report/`, `handoffs/`), `.gitignore`, `STATE.md`, and `LAB_LOG.md` are not yet created.

---

## 2. AWS Cloud Infrastructure Audit (`ap-south-1`)

### 2.1 Identity and Authentication
- **Command:** `aws sts get-caller-identity`
- **Caller ARN:** `arn:aws:iam::2042********:root` *(Account ID masked per security policy)*
- **User / Principal ID:** `2042********`
- **Configured Region:** `ap-south-1` (Mumbai)
- **Status:** **PASS** (Full EC2/VPC provisioning permissions available)

### 2.2 Default VPC Verification
- **Command:** `aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region ap-south-1`
- **VPC ID:** `vpc-091281d6eb74da886`
- **State:** `available`
- **CIDR Block:** `172.31.0.0/16`
- **Default Tenancy:** `default`
- **Internet Gateway Block Mode:** `off` (public egress/ingress available)
- **DHCP Options ID:** `dopt-0e24d3dc789751dad`
- **Status:** **PASS**

### 2.3 Subnet Topology and Placement Options
- **Command:** `aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-091281d6eb74da886" --region ap-south-1`
- **Subnet Details:**
  | Subnet ID | Availability Zone | CIDR Block | State | Available IPv4 Addresses | Recommendation |
  |---|---|---|---|---|---|
  | `subnet-0709c5a163cc423bb` | `ap-south-1a` | `172.31.32.0/20` | `available` | 4,091 | **Primary AZ for 3-node cluster** |
  | `subnet-0d173f9e2139ac04a` | `ap-south-1b` | `172.31.0.0/20`  | `available` | 4,091 | Backup / Alternative |
  | `subnet-0f928a79b161221b7` | `ap-south-1c` | `172.31.16.0/20` | `available` | 4,091 | Backup / Alternative |

*Architectural Note:* Per specification Section 3.1 & Section 6 Phase 1, all 3 EC2 nodes (`victim`, `attacker`, `client`) **MUST be launched in the exact same Availability Zone** (recommend `ap-south-1a`, `subnet-0709c5a163cc423bb`) to eliminate cross-AZ latency jitter and cross-AZ data transfer costs.

### 2.4 Ubuntu 24.04 LTS Official AMI Resolution
- **Lookup Method:** AWS Systems Manager (SSM) Parameter Store
- **Parameter Name:** `/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id`
- **AMI ID:** `ami-065d2b03fb493085a`
- **Image Name:** `ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20261004`
- **Architecture:** `x86_64` (amd64) — mandatory for `t3.micro`
- **Creation Date:** `2026-10-04T10:46:31.000Z`
- **Root Volume Type:** gp3 EBS
- **Status:** **PASS**

### 2.5 Active Cloud Resources (Baseline State)
- **EC2 Instances:** 0 instances active, stopped, or pending.
- **Key Pairs:** 0 existing key pairs found in `ap-south-1`.
- **Security Groups:** 1 existing group (`sg-0221386d1b9d1e9e8`, the default VPC group). No lab security group (`lab-sg`) exists yet.
- **Cost / Leakage Risk:** **ZERO** running cloud resources incurring charges.

### 2.6 Operator Public IP & Ingress Boundary
- **Command:** `curl -s https://checkip.amazonaws.com`
- **Detected Operator IPv4:** `152.57.107.6`
- **Mandatory Ingress Rule for `lab-sg`:**
  - Protocol: `tcp`
  - Port: `22`
  - Source CIDR: `152.57.107.6/32`
  - Ingress `0.0.0.0/0` or `::/0`: **STRICTLY PROHIBITED (Hard Invariant 4.1)**

---

## 3. Local Development Tooling & Utilities Audit

### 3.1 System Utilities
| Utility | Path | Installed Version | Requirement / Baseline | Status |
|---|---|---|---|---|
| **Python 3 (Default)** | `/opt/homebrew/bin/python3` | `3.14.8` | $\ge 3.10$ | **PASS** |
| **Python 3 (Framework)**| `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` | `3.13.2` | $\ge 3.10$ | **PASS** |
| **pip (Default)** | `/opt/homebrew/bin/pip3` | `26.2.1` | Modern pip | **PASS** |
| **pip (3.13)** | `/Library/Frameworks/Python.framework/Versions/3.13/bin/pip3` | `25.0.1` | Modern pip | **PASS** |
| **uv** | `/Library/Frameworks/Python.framework/Versions/3.13/bin/uv` | `0.11.23` | High-speed package manager | **PASS** |
| **jq** | `/opt/homebrew/bin/jq` | `jq-1.7.1-apple` | JSON processing | **PASS** |
| **git** | `/opt/homebrew/bin/git` | `git version 2.54.0` | VCS | **PASS** |
| **OpenSSH** | `/usr/bin/ssh` | `OpenSSH_10.3p1, LibreSSL 3.3.6` | EC2 remote access | **PASS** |
| **curl** | `/usr/bin/curl` | `8.7.1` | HTTP probing / IP detection | **PASS** |
| **Wireshark** | `/Applications/Wireshark.app/Contents/MacOS/wireshark` | GUI installed | Packet capture inspection | **PASS** |
| **tshark** | `/Applications/Wireshark.app/Contents/MacOS/tshark` | `4.6.7` | CLI PCAP analysis | **PASS** |

### 3.2 Python Data Science & Analysis Libraries
Phase 0 step 3 requires: `pandas`, `numpy`, `matplotlib`, `scikit-learn`, `pyyaml`.

| Package | Default Python 3.14 (`/opt/homebrew/bin/python3`) | Framework Python 3.13 (`.../3.13/bin/python3`) | Lab Requirement Status |
|---|---|---|---|
| `pandas` | ❌ Not Installed | ✅ `3.0.5` | Required for analysis/metrics.csv |
| `numpy` | ❌ Not Installed | ✅ `2.5.1` | Required for baseline EWMA & math |
| `matplotlib` | ❌ Not Installed | ❌ **Not Installed** | Required for Figures F1–F8 (300 DPI) |
| `scikit-learn` | ❌ Not Installed | ✅ `1.9.1` | Required for ROC / AUC evaluation |
| `pyyaml` | ❌ Not Installed | ✅ `6.0.3` | Required for `params.yaml` parsing |
| `scipy` | ❌ Not Installed | ✅ `1.18.1` | Statistical significance testing |
| `boto3` | ❌ Not Installed | ✅ `1.43.99` | AWS automation scripting |
| `pytest` | ❌ Not Installed | ✅ `9.1.1` | Test suite execution |

#### Actionable Finding on Python Environment:
1. Framework Python 3.13 already has 4 out of the 5 required analysis packages installed (`pandas`, `numpy`, `scikit-learn`, `pyyaml`), plus `scipy`, `boto3`, and `pytest`.
2. **Only `matplotlib` is missing** in the Python 3.13 environment.
3. Installing `matplotlib` into Python 3.13 via `pip3` or `uv pip install matplotlib` (or establishing a virtualenv via `uv venv .venv --python 3.13 && uv pip install -r requirements.txt`) will complete all Phase 0 Python requirements immediately.

---

## 4. Repository Structure and Git Status Audit

### 4.1 Git Repository Status
- **Current Git Status:**
  ```
  fatal: not a git repository (or any of the parent directories): .git
  ```
- **Finding:** Git has not yet been initialized in `/Users/raja/Documents/syn-edge-flooding`.
- **Git Config Identity:**
  - `user.name`: `C-hetha-N`
  - `user.email`: `chethannchethann80@gmail.com`
- **Required Action:** Run `git init`, set branch to `main`, and commit initial repository state.

### 4.2 Existing Filesystem Contents
```
/Users/raja/Documents/syn-edge-flooding
├── .agents/
│   └── teamwork/
│       ├── ORIGINAL_REQUEST.md
│       ├── sentinel/
│       ├── orchestrator_1/
│       ├── spec_miner_survey_1/
│       ├── explorer_survey_1/
│       ├── explorer_survey_1_gen2/
│       ├── explorer_survey_2/
│       └── explorer_survey_2_gen2/
├── docs/
│   ├── AGENTS_tcp_flood_lab.md    # Normative Specification v1.0
│   └── design.md                  # Project motivation and abstract draft
└── updates/
    ├── 000_PROJECT_INITIALIZATION.md
    ├── 001_DISPATCH_AND_SENTINEL.md
    ├── 002_PHASE0_SURVEY_AND_DECOMPOSITION.md
    └── 003_SPEC_MINING_COMPLETE_AND_RESILIENCE.md
```

### 4.3 Missing Specification-Mandated Layout Components (Section 5.1)
The following directories and files are pending creation during Phase 0 implementation:
1. **Root Files:**
   - `STATE.md` (orchestrator state machine, current phase, blockers)
   - `LAB_LOG.md` (append-only ledger of deviations, human gates, parameter changes)
   - `.gitignore` (critical: MUST ignore `*.pem`, `lab.env`, `runs/**/capture.pcap`, `.venv/`)
2. **Directories:**
   - `handoffs/` (phase handoff reports: A1.md through A7.md)
   - `infra/` (AWS CLI wrappers, security group rules, crowd_levels.json, teardown verification)
   - `tools/` (`sampler.py`, `probe.sh`, `attack_guard.sh`, `conn_hold.py`, `run_scenario.sh`)
   - `detector/` (`detector.py`, `replay.py`, `params.yaml`)
   - `runs/` (raw experiment artifacts per run: `runs/<run_id>/`, `runs/INDEX.csv`)
   - `analysis/` (`metrics.csv`, `overhead.csv`, analysis scripts)
   - `report/` (`report.md`, figure generation scripts, figures F1–F8)

---

## 5. Security & Safety Compliance Checklist

| Check / Requirement | Observed Value | Spec Rule | Status |
|---|---|---|---|
| AWS Account ID Masking | Masked to `2042********` | Sec 6 Phase 0 Step 1 | **COMPLIANT** |
| Security Group Ingress | Operator IP `152.57.107.6/32:22` | Sec 4.1 (No 0.0.0.0/0) | **READY** |
| Target IP Confinement | Pending `lab.env` (`VICTIM_PRIVATE_IP`) | Sec 4.1 | **PENDING PHASE 1** |
| Max Duration & Rate Limits | Planned in `attack_guard.sh` ($\le 60$ s, $\le 10,000$ pps) | Sec 4.2 | **PENDING PHASE 2** |
| Kill Switch File | `/tmp/LAB_STOP` check required | Sec 4.2 | **PENDING PHASE 2** |
| EC2 Credit Specification | `--credit-specification CpuCredits=standard` | Sec 4.5 | **READY FOR PHASE 1** |
| Human Safety Gate G1 | Policy acknowledgement in `updates/000_PROJECT_INITIALIZATION.md` | Sec 4.3 | **LOGGED** |

---

## 6. Actionable Recommendations for Orchestrator (`orchestrator_1`)

1. **Initialize Git & Protection:**
   - Execute `git init` in `/Users/raja/Documents/syn-edge-flooding`.
   - Create `.gitignore` immediately to prevent accidental commits of keys (`*.pem`), credentials, environment files (`lab.env`), and large PCAP captures (`runs/**/capture.pcap`).
2. **Setup Phase 0 Tracking Files & Tree:**
   - Create `STATE.md`, `LAB_LOG.md`, and directory scaffolding (`infra/`, `tools/`, `detector/`, `runs/`, `analysis/`, `report/`, `handoffs/`).
3. **Resolve `matplotlib` Dependency:**
   - Run `pip3 install matplotlib` (or `uv pip install matplotlib` against Python 3.13) to complete all five required analysis packages (`pandas`, `numpy`, `matplotlib`, `scikit-learn`, `pyyaml`).
4. **Trigger Phase 1 (Infrastructure):**
   - Target VPC: `vpc-091281d6eb74da886` in `ap-south-1`.
   - Target Subnet: `subnet-0709c5a163cc423bb` (Availability Zone `ap-south-1a`).
   - Target AMI: `ami-065d2b03fb493085a` (Ubuntu 24.04 LTS x86_64 gp3).
   - Target Operator SSH Ingress: `152.57.107.6/32` on port 22.
