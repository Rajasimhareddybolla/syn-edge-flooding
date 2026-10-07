#!/usr/bin/env bash
# tools/collect.sh — Orchestrate run collection across victim/attacker/client.
# Usage: collect.sh <run_id> [--pcap]
#
# Starts sampler + pidstat on victim, probe on client, fetches artifacts after run.
# Must be run with lab.env sourced (or present in cwd).

set -euo pipefail

RUN_ID="${1:?Usage: $0 <run_id> [--pcap]}"
DO_PCAP=0
if [[ "${2:-}" == "--pcap" ]]; then
    DO_PCAP=1
fi

# Load environment
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$REPO_ROOT/lab.env" ]]; then
    # shellcheck source=/dev/null
    source "$REPO_ROOT/lab.env"
fi

: "${VICTIM_PUB:?VICTIM_PUB not set}"
: "${CLIENT_PUB:?CLIENT_PUB not set}"
: "${ATTACKER_PUB:?ATTACKER_PUB not set}"
: "${KEY_PATH:?KEY_PATH not set}"
: "${VICTIM_PRIVATE_IP:?VICTIM_PRIVATE_IP not set}"
: "${VICTIM_IFACE:=ens5}"

RUN_DIR="$REPO_ROOT/runs/$RUN_ID"
mkdir -p "$RUN_DIR"

SSH_OPTS="-i $KEY_PATH -o StrictHostKeyChecking=no -o BatchMode=yes"

REMOTE_TMP="/tmp/lab_run_$RUN_ID"

echo "[collect] Starting collection for run: $RUN_ID"

# ==============================================================================
# 1. Start sampler on victim
# ==============================================================================
ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" bash -s <<'EOF'
mkdir -p /tmp/lab_run_PLACEHOLDER
EOF

ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
    "mkdir -p $REMOTE_TMP && \
     nohup python3 ~/syn-edge-flooding/tools/sampler.py \
         --out $REMOTE_TMP/victim_metrics.csv --hz 1 --method proc \
         > $REMOTE_TMP/sampler.log 2>&1 & echo \$! > $REMOTE_TMP/sampler.pid" \
    || echo "[collect] WARNING: sampler start returned non-zero on victim"

# ==============================================================================
# 2. Start pidstat on victim
# ==============================================================================
ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
    "nohup pidstat -u -r -p ALL 1 \
         > $REMOTE_TMP/victim_cpu_pidstat.txt 2>&1 & echo \$! > $REMOTE_TMP/pidstat.pid" \
    || echo "[collect] WARNING: pidstat start returned non-zero"

# ==============================================================================
# 3. Start tcpdump on victim (rep 1 only if --pcap)
# ==============================================================================
if (( DO_PCAP )); then
    echo "[collect] Starting tcpdump (snaplen 96, port 80) on victim..."
    ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
        "sudo timeout 180 tcpdump -i $VICTIM_IFACE -s 96 \
             -w $REMOTE_TMP/capture.pcap 'tcp port 80' \
             > $REMOTE_TMP/tcpdump.log 2>&1 &" \
        || echo "[collect] WARNING: tcpdump start returned non-zero"
fi

# ==============================================================================
# 4. Start probe on client
# ==============================================================================
ssh $SSH_OPTS "ubuntu@$CLIENT_PUB" \
    "mkdir -p $REMOTE_TMP && \
     nohup bash ~/syn-edge-flooding/tools/probe.sh $VICTIM_PRIVATE_IP \
         $REMOTE_TMP/probe.csv \
         > $REMOTE_TMP/probe.log 2>&1 & echo \$! > $REMOTE_TMP/probe.pid" \
    || echo "[collect] WARNING: probe start returned non-zero on client"

echo "[collect] All collectors started. Waiting for caller signal to stop..."

# ==============================================================================
# 5. stop() function — called by run_scenario.sh after event window
# ==============================================================================
stop_collectors() {
    echo "[collect] Stopping collectors..."
    # Stop sampler
    ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
        "kill \$(cat $REMOTE_TMP/sampler.pid 2>/dev/null) 2>/dev/null || true; \
         kill \$(cat $REMOTE_TMP/pidstat.pid 2>/dev/null) 2>/dev/null || true" || true

    # Stop probe
    ssh $SSH_OPTS "ubuntu@$CLIENT_PUB" \
        "kill \$(cat $REMOTE_TMP/probe.pid 2>/dev/null) 2>/dev/null || true" || true

    sleep 2

    # Fetch artifacts from victim
    echo "[collect] Fetching artifacts from victim..."
    scp $SSH_OPTS "ubuntu@$VICTIM_PUB:$REMOTE_TMP/victim_metrics.csv" "$RUN_DIR/" 2>/dev/null || echo "[collect] victim_metrics.csv missing"
    scp $SSH_OPTS "ubuntu@$VICTIM_PUB:$REMOTE_TMP/victim_cpu_pidstat.txt" "$RUN_DIR/" 2>/dev/null || echo "[collect] pidstat missing"
    scp $SSH_OPTS "ubuntu@$VICTIM_PUB:/var/log/nginx/access.log" "$RUN_DIR/nginx_access.log" 2>/dev/null || true
    if (( DO_PCAP )); then
        scp $SSH_OPTS "ubuntu@$VICTIM_PUB:$REMOTE_TMP/capture.pcap" "$RUN_DIR/" 2>/dev/null || echo "[collect] pcap missing"
    fi

    # Fetch artifacts from client
    echo "[collect] Fetching artifacts from client..."
    scp $SSH_OPTS "ubuntu@$CLIENT_PUB:$REMOTE_TMP/probe.csv" "$RUN_DIR/" 2>/dev/null || echo "[collect] probe.csv missing"

    # Cleanup remote tmp
    ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" "rm -rf $REMOTE_TMP" 2>/dev/null || true
    ssh $SSH_OPTS "ubuntu@$CLIENT_PUB" "rm -rf $REMOTE_TMP" 2>/dev/null || true

    echo "[collect] Artifacts fetched to $RUN_DIR/"
}

# Export stop function for sourcing
export -f stop_collectors 2>/dev/null || true

