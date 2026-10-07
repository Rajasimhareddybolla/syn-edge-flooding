# Milestone 2 Exploration & Implementation Guide: Victim Environment, Tooling & Sysctl Break/Fix Profiles

**Document Version:** 1.0  
**Author:** `explorer_m2_env` (Teamwork Explorer)  
**Target Milestone:** Milestone 2 (M2 — Victim Environment, Tooling & Sysctl Break/Fix Profiles)  
**Project Root:** `/Users/raja/Documents/syn-edge-flooding`  
**Working Directory:** `/Users/raja/Documents/syn-edge-flooding/.agents/teamwork/explorer_m2_env`  
**Date / Timestamp:** 2026-10-07T08:00:00Z  
**Status:** COMPLETE (Hard Handoff)

---

## 1. Observation

1. **Host State & Kernel Baselines:**
   - Evaluated live instances via batch-mode SSH across the testbed (`lab.env`):
     - `victim`: `VICTIM_PUB=13.235.246.92`, `VICTIM_PRIVATE_IP=172.31.37.214`, `ens5`
     - `attacker`: `ATTACKER_PUB=65.2.190.166`, `ATTACKER_PRIVATE_IP=172.31.42.168`
     - `client`: `CLIENT_PUB=13.206.119.8`, `CLIENT_PRIVATE_IP=172.31.41.87`
   - Kernel OS on nodes: Ubuntu 24.04.5 LTS (`Noble Numbat`), Kernel `7.0.0-1014-aws` x86_64.
   - Live sysctl query on `victim` prior to modifications:
     ```bash
     sysctl net.ipv4.tcp_syncookies net.ipv4.tcp_max_syn_backlog net.core.somaxconn net.ipv4.tcp_synack_retries net.ipv4.ip_local_port_range
     ```
     Verbatim output:
     ```
     net.ipv4.tcp_syncookies = 1
     net.ipv4.tcp_max_syn_backlog = 128
     net.core.somaxconn = 4096
     net.ipv4.tcp_synack_retries = 5
     net.ipv4.ip_local_port_range = 32768	60999
     ```
   - Client baseline limits (`ssh ubuntu@$CLIENT_PUB "ulimit -n; sysctl net.ipv4.ip_local_port_range"`):
     ```
     1024
     net.ipv4.ip_local_port_range = 32768	60999
     ```

2. **Package Availability & Missing Package Audit:**
   - Audited existing packages via `dpkg -l` on all 3 nodes:
     - `victim`: `chrony` (4.5-1ubuntu4.2), `jq` (1.7.1), `sysstat` (12.6.1-2), `tcpdump` (4.99.4) already installed. Missing: `python3-pip`, `nginx`.
     - `attacker`: `chrony`, `jq`, `sysstat`, `tcpdump` already installed. Missing: `python3-pip`, `hping3`.
     - `client`: `chrony`, `jq`, `sysstat`, `tcpdump`, `curl` already installed. Missing: `python3-pip`, `apache2-utils`, `wrk`.
   - Verified candidate versions in Ubuntu 24.04 `noble`/`noble-updates` repository:
     - `nginx`: candidate `1.24.0-2ubuntu7.18` (main)
     - `hping3`: candidate `3.a2.ds2-10build2` (universe)
     - `wrk`: candidate `4.1.0-4build2` (universe)
     - `apache2-utils`: candidate `2.4.58-1ubuntu8.15` (main)
     - `python3-pip`: candidate `24.0+dfsg-1ubuntu1.3` (universe)
   - Note on APT invocation: `DEBIAN_FRONTEND=noninteractive` and `NEEDRESTART_MODE=a` with `-o DPkg::Lock::Timeout=60` are required on Ubuntu 24.04 to prevent `needrestart` interactive dialogs or lock race conditions.

3. **Security Group Egress Drift & CGNAT Resilience:**
   - When running automated commands from the operator environment, the mobile/cellular ISP rotates through CGNAT IPv4 gateways (`152.57.x.x`).
   - Adding the active egress IPv4 (e.g. `152.57.24.183/32`) via `aws ec2 authorize-security-group-ingress` restored instant SSH reachability while strictly maintaining RFC 2119 /32 ingress lockdown with zero `0.0.0.0/0` exposure.

---

## 2. Logic Chain

1. **Package Provisioning Consistency (Obs. 2):**
   - The three nodes share common telemetry and utility packages (`python3-pip`, `sysstat`, `jq`, `chrony`, `tcpdump`) while having distinct roles:
     - `victim` requires `nginx` to act as the web server target.
     - `attacker` requires `hping3` to generate raw TCP SYN traffic.
     - `client` requires `apache2-utils` (`ab`), `wrk`, and `curl` to generate legitimate quiet loads, flash crowds, and 1 Hz health probes.
   - Because APT repositories on Ubuntu 24.04 already index all required packages in `main` and `universe`, no PPAs, external repos, or compilation from source are necessary.
   - Setting `DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a` eliminates interactive prompts from `needrestart` during unattended deployment.

2. **Nginx Configuration & Backlog Grounding (Obs. 1, Obs. 2):**
   - In Linux, the effective socket accept queue length is governed by `min(backlog, somaxconn)`.
   - Configuring `listen 80 default_server backlog=128;` in `/etc/nginx/sites-available/default` sets the `listen()` system call parameter to 128.
   - When `net.core.somaxconn = 128` (break/fix profiles), the kernel caps the listen queue at exactly 128.
   - Generating a static `/var/www/html/index.html` of exactly 1,024 bytes (1 KB) satisfies the payload benchmark requirement, providing a deterministic response size for both legitimate loads (`wrk`, `ab`) and client probes (`curl`).
   - The socket listener can be verified via `ss -tlpn | grep :80`: for sockets in `LISTEN` state, `Send-Q` represents the backlog limit (128), while `Recv-Q` represents current unaccepted connections.

3. **Sysctl Defaults Snapshot & Scientific Rationale (Obs. 1):**
   - Capturing the pristine system parameters before any break profile is applied establishes the baseline in `infra/sysctl_defaults.txt`:
     - `net.ipv4.tcp_syncookies = 1`
     - `net.ipv4.tcp_max_syn_backlog = 128`
     - `net.core.somaxconn = 4096`
     - `net.ipv4.tcp_synack_retries = 5`
     - `net.ipv4.ip_local_port_range = 32768 60999`
     - client `ulimit -n = 1024`
   - In SYN flood research, the queue capacity must be small enough to saturate under modest attack rates without destabilizing the whole VM. Thus, both break and fix profiles constrain queues to `128` (`tcp_max_syn_backlog=128`, `somaxconn=128`).
   - The independent variable between break and fix is strictly `tcp_syncookies`:
     - In `break`: `tcp_syncookies=0`. When 128 half-open slots are occupied, the kernel drops further SYNs (`d_listen_drops` / `d_reqq_full_drop`), causing service failure.
     - In `fix`: `tcp_syncookies=1`. When 128 slots are saturated, the kernel falls back to cryptographic SYN cookies (`d_syncookies_sent`), preserving legitimate client connectivity.
     - In `default`: restores `tcp_syncookies=1`, `tcp_max_syn_backlog=128`, `somaxconn=4096`.

4. **Profile Switcher Script Architecture (`tools/set_profile.sh`):**
   - The switcher script must operate deterministically whether executed locally on the victim VM or remotely from the operator Mac workstation across SSH.
   - Reading live kernel values via `sysctl -n` immediately after modification provides an atomic assertion: if any value does not match the target profile, the script aborts with non-zero exit code.
   - Updating `/etc/sysctl.d/99-lab.conf` ensures persistence and auditability.

---

## 3. Caveats

1. **Operator IP Drift under CGNAT:**
   - If the operator's public IPv4 changes during execution, SSH connections will time out. The implementation worker must ensure the operator's current active `/32` is present in `lab-sg` prior to executing remote SSH commands.
2. **Attacker RST Suppression Rule:**
   - While package installation on `attacker` installs `hping3`, SYN flood realism requires the kernel RST drop rule (`iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $VICTIM_PRIVATE_IP -j DROP`) and `attack_guard.sh`. This is tracked in Milestone 2's traffic/guard scope.
3. **PEP 668 on Ubuntu 24.04:**
   - Python 3.12 enforces `externally-managed-environment`. Project tooling on the victim (`tools/sampler.py`) uses Python standard library only; `pip3` is installed per spec but not required for sampler runtime.

---

## 4. Conclusion & Actionable Implementation Plan

The exploration of Milestone 2 requirements is complete. The exact files, configurations, and commands are specified below for immediate implementation by `worker_m2`.

### 4.1 Step 1: APT Package Installation Across All 3 Nodes

#### Commands for Victim Node:
```bash
sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y -o DPkg::Lock::Timeout=60 \
  python3-pip sysstat jq chrony tcpdump nginx
```

#### Commands for Attacker Node:
```bash
sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y -o DPkg::Lock::Timeout=60 \
  python3-pip sysstat jq chrony tcpdump hping3
```

#### Commands for Client Node:
```bash
sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y -o DPkg::Lock::Timeout=60 \
  python3-pip sysstat jq chrony tcpdump apache2-utils wrk curl
```

---

### 4.2 Step 2: Nginx Setup & 1 KB Static Page on Victim

#### 1. Generate 1 KB Static `index.html`:
```bash
sudo python3 -c '
header = "<!DOCTYPE html>\n<html><head><title>TCP Flood Lab</title></head><body>\n<h1>TCP Flood Lab Edge Victim</h1>\n<p>"
footer = "</p>\n</body></html>\n"
pad_len = 1024 - len(header) - len(footer)
content = header + ("X" * pad_len) + footer
assert len(content.encode("utf-8")) == 1024
with open("/var/www/html/index.html", "w") as f:
    f.write(content)
'
sudo rm -f /var/www/html/index.nginx-debian.html
sudo chown www-data:www-data /var/www/html/index.html
sudo chmod 644 /var/www/html/index.html
```

#### 2. Configure `/etc/nginx/sites-available/default`:
```nginx
server {
    listen 80 default_server backlog=128;
    listen [::]:80 default_server backlog=128;

    root /var/www/html;
    index index.html;

    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

#### 3. Test, Reload & Enable Nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

#### 4. Immediate Local Verification:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/
# Must output: 200

curl -s http://127.0.0.1/ | wc -c
# Must output: 1024

ss -tlpn | grep ':80'
# Must show Send-Q == 128
```

---

### 4.3 Step 3: Snapshot System Defaults to `infra/sysctl_defaults.txt`

Execute from repository root (`/Users/raja/Documents/syn-edge-flooding`):
```bash
source lab.env
mkdir -p infra

SSH_KEY_RESOLVED=$(eval echo "$KEY_PATH")
SSH_CMD="ssh -i $SSH_KEY_RESOLVED -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes"

cat <<EOF > infra/sysctl_defaults.txt
# sysctl_defaults.txt — Captured baseline kernel parameters for tcp-flood-lab
# Captured: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Victim Kernel Defaults (host: $VICTIM_PRIVATE_IP):
$($SSH_CMD ubuntu@"$VICTIM_PUB" "sysctl net.ipv4.tcp_syncookies net.ipv4.tcp_max_syn_backlog net.core.somaxconn net.ipv4.tcp_synack_retries net.ipv4.ip_local_port_range")

# Client Defaults (host: $CLIENT_PRIVATE_IP):
client ulimit -n = $($SSH_CMD ubuntu@"$CLIENT_PUB" "ulimit -n")
client net.ipv4.ip_local_port_range = $($SSH_CMD ubuntu@"$CLIENT_PUB" "sysctl -n net.ipv4.ip_local_port_range")
EOF
```

Expected content in `infra/sysctl_defaults.txt`:
```
# sysctl_defaults.txt — Captured baseline kernel parameters for tcp-flood-lab
# Captured: 2026-10-07T...Z

# Victim Kernel Defaults (host: 172.31.37.214):
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 128
net.core.somaxconn = 4096
net.ipv4.tcp_synack_retries = 5
net.ipv4.ip_local_port_range = 32768	60999

# Client Defaults (host: 172.31.41.87):
client ulimit -n = 1024
client net.ipv4.ip_local_port_range = 32768	60999
```

---

### 4.4 Step 4: Sysctl Profile Switcher Script (`tools/set_profile.sh`)

Create `/Users/raja/Documents/syn-edge-flooding/tools/set_profile.sh` with permissions `chmod +x`:

```bash
#!/usr/bin/env bash
# ==============================================================================
# tools/set_profile.sh — Sysctl Break/Fix Profile Switcher for tcp-flood-lab
#
# Profiles:
#   break:   net.ipv4.tcp_syncookies=0, net.ipv4.tcp_max_syn_backlog=128, net.core.somaxconn=128
#   fix:     net.ipv4.tcp_syncookies=1, net.ipv4.tcp_max_syn_backlog=128, net.core.somaxconn=128
#   default: net.ipv4.tcp_syncookies=1, net.ipv4.tcp_max_syn_backlog=128, net.core.somaxconn=4096
#
# Usage:
#   tools/set_profile.sh {break|fix|default}
# ==============================================================================
set -euo pipefail

PROFILE="${1:-}"

if [[ -z "$PROFILE" || ! "$PROFILE" =~ ^(break|fix|default)$ ]]; then
  echo "❌ Error: Invalid profile '$PROFILE'." >&2
  echo "Usage: $0 {break|fix|default}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

apply_local() {
  local target_syncookies
  local target_backlog
  local target_somaxconn

  case "$PROFILE" in
    break)
      target_syncookies=0
      target_backlog=128
      target_somaxconn=128
      ;;
    fix)
      target_syncookies=1
      target_backlog=128
      target_somaxconn=128
      ;;
    default)
      target_syncookies=1
      target_backlog=128
      target_somaxconn=4096
      ;;
  esac

  echo "Applying '$PROFILE' profile to kernel..."
  sudo sysctl -w net.ipv4.tcp_syncookies="$target_syncookies" >/dev/null
  sudo sysctl -w net.ipv4.tcp_max_syn_backlog="$target_backlog" >/dev/null
  sudo sysctl -w net.core.somaxconn="$target_somaxconn" >/dev/null

  cat <<EOF | sudo tee /etc/sysctl.d/99-lab.conf >/dev/null
# /etc/sysctl.d/99-lab.conf — tcp-flood-lab $PROFILE profile
net.ipv4.tcp_syncookies = $target_syncookies
net.ipv4.tcp_max_syn_backlog = $target_backlog
net.core.somaxconn = $target_somaxconn
EOF

  local cur_syncookies
  local cur_backlog
  local cur_somaxconn

  cur_syncookies=$(sysctl -n net.ipv4.tcp_syncookies)
  cur_backlog=$(sysctl -n net.ipv4.tcp_max_syn_backlog)
  cur_somaxconn=$(sysctl -n net.core.somaxconn)

  if [[ "$cur_syncookies" != "$target_syncookies" || \
        "$cur_backlog" != "$target_backlog" || \
        "$cur_somaxconn" != "$target_somaxconn" ]]; then
    echo "❌ Verification FAILED for profile '$PROFILE':" >&2
    echo "  Expected: syncookies=$target_syncookies, backlog=$target_backlog, somaxconn=$target_somaxconn" >&2
    echo "  Actual:   syncookies=$cur_syncookies, backlog=$cur_backlog, somaxconn=$cur_somaxconn" >&2
    exit 1
  fi

  echo "✅ Profile '$PROFILE' active and verified:"
  echo "  net.ipv4.tcp_syncookies = $cur_syncookies"
  echo "  net.ipv4.tcp_max_syn_backlog = $cur_backlog"
  echo "  net.core.somaxconn = $cur_somaxconn"
}

if [[ -f "$LAB_ROOT/lab.env" ]]; then
  # Sourced on operator Mac: dispatch remotely to victim node
  # shellcheck source=/dev/null
  source "$LAB_ROOT/lab.env"
  SSH_KEY_RESOLVED=$(eval echo "$KEY_PATH")
  SSH_CMD="ssh -i $SSH_KEY_RESOLVED -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes"

  echo "Dispatching profile '$PROFILE' to victim ($VICTIM_PUB)..."
  $SSH_CMD ubuntu@"$VICTIM_PUB" "bash -s -- $PROFILE" <<'REMOTE_EOF'
PROFILE="$1"
target_syncookies=""
target_backlog=""
target_somaxconn=""

case "$PROFILE" in
  break)
    target_syncookies=0
    target_backlog=128
    target_somaxconn=128
    ;;
  fix)
    target_syncookies=1
    target_backlog=128
    target_somaxconn=128
    ;;
  default)
    target_syncookies=1
    target_backlog=128
    target_somaxconn=4096
    ;;
esac

sudo sysctl -w net.ipv4.tcp_syncookies="$target_syncookies" >/dev/null
sudo sysctl -w net.ipv4.tcp_max_syn_backlog="$target_backlog" >/dev/null
sudo sysctl -w net.core.somaxconn="$target_somaxconn" >/dev/null

cat <<EOF | sudo tee /etc/sysctl.d/99-lab.conf >/dev/null
# /etc/sysctl.d/99-lab.conf — tcp-flood-lab $PROFILE profile
net.ipv4.tcp_syncookies = $target_syncookies
net.ipv4.tcp_max_syn_backlog = $target_backlog
net.core.somaxconn = $target_somaxconn
EOF

cur_syncookies=$(sysctl -n net.ipv4.tcp_syncookies)
cur_backlog=$(sysctl -n net.ipv4.tcp_max_syn_backlog)
cur_somaxconn=$(sysctl -n net.core.somaxconn)

if [[ "$cur_syncookies" != "$target_syncookies" || \
      "$cur_backlog" != "$target_backlog" || \
      "$cur_somaxconn" != "$target_somaxconn" ]]; then
  echo "❌ Verification FAILED for profile '$PROFILE':" >&2
  echo "  Expected: syncookies=$target_syncookies, backlog=$target_backlog, somaxconn=$target_somaxconn" >&2
  echo "  Actual:   syncookies=$cur_syncookies, backlog=$cur_backlog, somaxconn=$cur_somaxconn" >&2
  exit 1
fi

echo "✅ Profile '$PROFILE' active and verified on victim:"
echo "  net.ipv4.tcp_syncookies = $cur_syncookies"
echo "  net.ipv4.tcp_max_syn_backlog = $cur_backlog"
echo "  net.core.somaxconn = $cur_somaxconn"
REMOTE_EOF

else
  # Direct invocation on victim host
  apply_local
fi
```

---

## 5. Verification Method

The implementation can be independently verified via the following sequential steps:

1. **Verify Package Presence Across All Nodes:**
   ```bash
   source lab.env
   SSH_CMD="ssh -i $(eval echo $KEY_PATH) -o BatchMode=yes"
   
   # Victim check:
   $SSH_CMD ubuntu@"$VICTIM_PUB" "dpkg -l python3-pip sysstat jq chrony tcpdump nginx | grep '^ii' | wc -l"
   # Expected: 6
   
   # Attacker check:
   $SSH_CMD ubuntu@"$ATTACKER_PUB" "dpkg -l python3-pip sysstat jq chrony tcpdump hping3 | grep '^ii' | wc -l"
   # Expected: 6
   
   # Client check:
   $SSH_CMD ubuntu@"$CLIENT_PUB" "dpkg -l python3-pip sysstat jq chrony tcpdump apache2-utils wrk curl | grep '^ii' | wc -l"
   # Expected: 7
   ```

2. **Verify Nginx Server, Backlog & HTTP 200 (1 KB) Response:**
   ```bash
   source lab.env
   SSH_CMD="ssh -i $(eval echo $KEY_PATH) -o BatchMode=yes"
   
   # 1. Active service check
   $SSH_CMD ubuntu@"$VICTIM_PUB" "systemctl is-active nginx"
   # Expected: active
   
   # 2. Backlog check on port 80
   $SSH_CMD ubuntu@"$VICTIM_PUB" "ss -tlpn | grep ':80'"
   # Expected: Send-Q is 128
   
   # 3. Inter-node client probe to victim private IP
   $SSH_CMD ubuntu@"$CLIENT_PUB" "curl -s -o /dev/null -w '%{http_code}\n' http://$VICTIM_PRIVATE_IP/"
   # Expected: 200
   
   # 4. Payload size check
   $SSH_CMD ubuntu@"$CLIENT_PUB" "curl -s http://$VICTIM_PRIVATE_IP/ | wc -c"
   # Expected: 1024
   ```

3. **Verify Sysctl Defaults Snapshot File:**
   ```bash
   test -s infra/sysctl_defaults.txt && grep -q "net.ipv4.tcp_syncookies" infra/sysctl_defaults.txt && echo "SNAPSHOT_OK"
   # Expected: SNAPSHOT_OK
   ```

4. **Verify Profile Switcher (`tools/set_profile.sh`):**
   ```bash
   bash tools/set_profile.sh break
   # Expected exit code 0; tcp_syncookies=0, tcp_max_syn_backlog=128, somaxconn=128
   
   bash tools/set_profile.sh fix
   # Expected exit code 0; tcp_syncookies=1, tcp_max_syn_backlog=128, somaxconn=128
   
   bash tools/set_profile.sh default
   # Expected exit code 0; tcp_syncookies=1, tcp_max_syn_backlog=128, somaxconn=4096
   
   bash tools/set_profile.sh invalid || echo "HANDLED_OK"
   # Expected: Non-zero exit code, HANDLED_OK
   ```

### Invalidation Conditions:
- If `curl http://$VICTIM_PRIVATE_IP/` returns a non-200 status or a body size other than 1024 bytes.
- If `ss -tlpn` shows a Send-Q other than 128 on port 80.
- If `set_profile.sh break` fails to set `tcp_syncookies=0`.
- If `infra/sysctl_defaults.txt` is missing baseline values for `somaxconn` or `tcp_syncookies`.
