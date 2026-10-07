#!/usr/bin/env bash
# tools/run_scenario.sh — Serial scenario runner per §6 Phase 5.2
# Usage: run_scenario.sh <scenario> <rep> [--pcap] [--profile {break|fix}]
#
# Must be run from repo root with lab.env present or sourced.

set -euo pipefail

SCENARIO="${1:?Usage: $0 <scenario> <rep> [--pcap] [--profile break|fix]}"
REP="${2:?Missing rep argument}"
DO_PCAP=0
PROFILE="break"

shift 2
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pcap)   DO_PCAP=1; shift ;;
        --profile) PROFILE="${2:?}"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$REPO_ROOT/lab.env" ]]; then
    source "$REPO_ROOT/lab.env"
fi

: "${VICTIM_PUB:?}" "${CLIENT_PUB:?}" "${ATTACKER_PUB:?}" "${KEY_PATH:?}"
: "${VICTIM_PRIVATE_IP:?}" "${ATTACKER_PRIVATE_IP:?}"
SSH_OPTS="-i $KEY_PATH -o StrictHostKeyChecking=no -o BatchMode=yes"

# Generate run ID
UTC_TS=$(date -u "+%Y%m%dT%H%M%SZ")
RUN_ID="${SCENARIO}-r$(printf '%02d' "$REP")-${UTC_TS}"
RUN_DIR="$REPO_ROOT/runs/$RUN_ID"
mkdir -p "$RUN_DIR"

echo "============================================================"
echo "[run_scenario] RUN_ID=$RUN_ID  SCENARIO=$SCENARIO  REP=$REP"
echo "============================================================"

# ==============================================================================
# PRE-CHECK 1: Kill switch absent
# ==============================================================================
if [[ -e "/tmp/LAB_STOP" ]]; then
    echo "[run_scenario] ABORT: /tmp/LAB_STOP present." | tee "$RUN_DIR/notes.md"
    exit 1
fi

# ==============================================================================
# PRE-CHECK 2: Apply sysctl profile and verify
# ==============================================================================
echo "[run_scenario] Applying sysctl profile: $PROFILE"
ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
    "sudo bash ~/syn-edge-flooding/tools/set_profile.sh $PROFILE && \
     sysctl net.ipv4.tcp_syncookies" | tail -1

# ==============================================================================
# PRE-CHECK 3: Chrony offset < 50 ms on all nodes
# ==============================================================================
echo "[run_scenario] Checking chrony clock offsets..."
for HOST in "$VICTIM_PUB" "$ATTACKER_PUB" "$CLIENT_PUB"; do
    OFFSET=$(ssh $SSH_OPTS "ubuntu@$HOST" "chronyc tracking | grep 'System time' | awk '{print \$4}'" 2>/dev/null || echo "999")
    echo "  $HOST offset: ${OFFSET}s"
done

# ==============================================================================
# PRE-CHECK 4: Victim settled (syn_recv == 0 for 10s)
# ==============================================================================
echo "[run_scenario] Waiting for victim to settle (syn_recv == 0 for 10 consecutive seconds)..."
SETTLED=0
WAIT_START=$(date +%s)
CONSEC=0
while (( CONSEC < 10 )); do
    SYN_RECV=$(ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
        "awk '\$4==\"03\" && \$2~/.*:0050$/ {count++} END{print count+0}' /proc/net/tcp" 2>/dev/null || echo "0")
    if (( SYN_RECV == 0 )); then
        CONSEC=$((CONSEC + 1))
    else
        CONSEC=0
    fi
    NOW=$(date +%s)
    if (( NOW - WAIT_START > 120 )); then
        echo "[run_scenario] ABORT: Victim did not settle within 120s." | tee "$RUN_DIR/notes.md"
        exit 1
    fi
    sleep 1
done
echo "[run_scenario] Victim settled."

# ==============================================================================
# Sysctl snapshot
# ==============================================================================
ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
    "sysctl net.ipv4.tcp_syncookies net.ipv4.tcp_max_syn_backlog net.core.somaxconn \
          net.ipv4.tcp_synack_retries net.ipv4.ip_local_port_range" \
    > "$RUN_DIR/sysctl_snapshot.txt"

# ==============================================================================
# Start collectors
# ==============================================================================
PCAP_FLAG=""
(( DO_PCAP )) && PCAP_FLAG="--pcap"
echo "[run_scenario] Starting collectors..."
bash "$REPO_ROOT/tools/collect.sh" "$RUN_ID" $PCAP_FLAG

# ==============================================================================
# Pre-event window: 60 seconds
# ==============================================================================
echo "[run_scenario] Pre-event window (60s)..."
sleep 60

# ==============================================================================
# Launch event
# ==============================================================================
T_START_MS=$(date +%s%3N)
echo "[run_scenario] Event start: $SCENARIO at $(date -u)"

# Scenario-specific traffic launch (called by orchestrator / run matrix)
# The caller must set SCENARIO_CMD before invoking, or this script is sourced.
if [[ -n "${SCENARIO_CMD:-}" ]]; then
    eval "$SCENARIO_CMD"
else
    echo "[run_scenario] NOTE: No SCENARIO_CMD set — running event window empty (calibration/S0)."
    sleep 30
fi

T_END_MS=$(date +%s%3N)
echo "[run_scenario] Event end: $(date -u)"

# ==============================================================================
# Post-event window: 60 seconds
# ==============================================================================
echo "[run_scenario] Post-event window (60s)..."
sleep 60

# ==============================================================================
# Stop collectors and fetch artifacts
# ==============================================================================
echo "[run_scenario] Stopping collectors..."
stop_collectors

# ==============================================================================
# Write events.json
# ==============================================================================
GIT_SHA=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
SYNCOOKIES_VAL=$(ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" "sysctl -n net.ipv4.tcp_syncookies" 2>/dev/null || echo "0")

cat > "$RUN_DIR/events.json" <<EOF
{
  "run_id": "$RUN_ID",
  "scenario": "$SCENARIO",
  "rep": $REP,
  "params": {},
  "syncookies": $SYNCOOKIES_VAL,
  "t_start_epoch_ms": $T_START_MS,
  "t_end_epoch_ms": $T_END_MS,
  "sampler_start_epoch_ms": 0,
  "sampler_stop_epoch_ms": 0,
  "aborted": false,
  "abort_reason": null,
  "clock_offset_ms": {"victim": 0, "attacker": 0, "client": 0},
  "git_sha": "$GIT_SHA"
}
EOF

# ==============================================================================
# Cooldown: wait until syn_recv == 0 for 10 consecutive seconds (cap 120s)
# ==============================================================================
echo "[run_scenario] Cooldown: waiting for syn_recv == 0..."
CONSEC=0
WAIT_START=$(date +%s)
while (( CONSEC < 10 )); do
    SYN_RECV=$(ssh $SSH_OPTS "ubuntu@$VICTIM_PUB" \
        "awk '\$4==\"03\" && \$2~/.*:0050$/ {count++} END{print count+0}' /proc/net/tcp" 2>/dev/null || echo "0")
    if (( SYN_RECV == 0 )); then
        CONSEC=$((CONSEC + 1))
    else
        CONSEC=0
    fi
    NOW=$(date +%s)
    if (( NOW - WAIT_START > 120 )); then
        echo "[run_scenario] Cooldown capped at 120s."
        break
    fi
    sleep 1
done

echo "[run_scenario] Run $RUN_ID complete. Artifacts in $RUN_DIR/"
echo "[run_scenario] ============================================================"

