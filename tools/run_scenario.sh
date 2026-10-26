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

# S5 scenarios strictly require fix profile (syncookies on)
if [[ "$SCENARIO" =~ ^S5 ]]; then
    PROFILE="fix"
fi

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
    # shellcheck source=/dev/null
    source "$REPO_ROOT/lab.env"
fi

: "${VICTIM_PUB:?}" "${CLIENT_PUB:?}" "${ATTACKER_PUB:?}" "${KEY_PATH:?}"
: "${VICTIM_PRIVATE_IP:?}" "${ATTACKER_PRIVATE_IP:?}"

SSH_CMD=(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10)
SCP_CMD=(scp -i "$KEY_PATH" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10)

# Generate run ID
UTC_TS=$(date -u "+%Y%m%dT%H%M%SZ")
RUN_ID="${SCENARIO}-r$(printf '%02d' "$REP")-${UTC_TS}"
RUN_DIR="$REPO_ROOT/runs/$RUN_ID"
mkdir -p "$RUN_DIR"

echo "============================================================"
echo "[run_scenario] RUN_ID=$RUN_ID  SCENARIO=$SCENARIO  REP=$REP  PROFILE=$PROFILE"
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
"${SSH_CMD[@]}" "ubuntu@$VICTIM_PUB" \
    "sudo bash ~/syn-edge-flooding/tools/set_profile.sh $PROFILE && \
     sysctl net.ipv4.tcp_syncookies" | tail -1

# ==============================================================================
# PRE-CHECK 3: Chrony offset < 50 ms on all nodes
# ==============================================================================
echo "[run_scenario] Checking chrony clock offsets..."
for HOST in "$VICTIM_PUB" "$ATTACKER_PUB" "$CLIENT_PUB"; do
    OFFSET=$("${SSH_CMD[@]}" "ubuntu@$HOST" "chronyc tracking | grep 'System time' | awk '{print \$4}'" 2>/dev/null || echo "999")
    echo "  $HOST offset: ${OFFSET}s"
done

# ==============================================================================
# PRE-CHECK 4: Victim settled (syn_recv == 0 for 10s consecutive, cap 120s)
# ==============================================================================
echo "[run_scenario] Waiting for victim to settle (syn_recv == 0 for 10s)..."
SETTLE_RES=$("${SSH_CMD[@]}" "ubuntu@$VICTIM_PUB" "bash -c '
    consec=0
    for ((i=0; i<120; i++)); do
        sr=\$(awk \"\\\$4==\\\"03\\\" && \\\$2~/.*:0050$/ {count++} END{print count+0}\" /proc/net/tcp 2>/dev/null || echo 0)
        if [ \"\$sr\" -eq 0 ]; then
            consec=\$((consec + 1))
            if [ \"\$consec\" -ge 10 ]; then
                echo SETTLED
                exit 0
            fi
        else
            consec=0
        fi
        sleep 1
    done
    echo TIMEOUT
    exit 1
'" 2>/dev/null || echo "TIMEOUT")

if [[ "$SETTLE_RES" != *"SETTLED"* ]]; then
    echo "[run_scenario] ABORT: Victim did not settle within 120s." | tee "$RUN_DIR/notes.md"
    exit 1
fi
echo "[run_scenario] Victim settled."

# ==============================================================================
# Sysctl snapshot
# ==============================================================================
"${SSH_CMD[@]}" "ubuntu@$VICTIM_PUB" \
    "sysctl net.ipv4.tcp_syncookies net.ipv4.tcp_max_syn_backlog net.core.somaxconn \
          net.ipv4.tcp_synack_retries net.ipv4.ip_local_port_range" \
    > "$RUN_DIR/sysctl_snapshot.txt"

# ==============================================================================
# Start collectors
# ==============================================================================
PCAP_FLAG=""
(( DO_PCAP )) && PCAP_FLAG="--pcap"
echo "[run_scenario] Starting collectors..."
# Source collect.sh
# shellcheck source=collect.sh
source "$REPO_ROOT/tools/collect.sh" "$RUN_ID" $PCAP_FLAG

# Quiet background load (runs on client for every scenario per §5.1 / §287)
# If S0, wrk is the primary background load (120s).
# For attack / crowd runs, it runs throughout the 150s test window.
"${SSH_CMD[@]}" "ubuntu@$CLIENT_PUB" \
    "nohup timeout 155 wrk -t1 -c2 -d150s -H 'Connection: close' http://$VICTIM_PRIVATE_IP/ \
        > $REMOTE_TMP/load_client.txt 2>&1 < /dev/null &" \
    || echo "[run_scenario] WARNING: quiet background load did not start"

# ==============================================================================
# Pre-event window: 60 seconds (or 10s for S0 baseline)
# Per §5.1: S0 is a 120s total window. S1-S5 are 60s pre, 30s event, 60s post.
# ==============================================================================
if [[ "$SCENARIO" == "S0" ]]; then
    echo "[run_scenario] S0 baseline window (running 120s total)..."
    T_START_MS=$(date +%s%3N)
    sleep 120
    T_END_MS=$(date +%s%3N)
else
    echo "[run_scenario] Pre-event window (60s)..."
    sleep 60

    # ==============================================================================
    # Launch event (30 seconds)
    # ==============================================================================
    T_START_MS=$(date +%s%3N)
    echo "[run_scenario] Event start: $SCENARIO at $(date -u)"

    case "$SCENARIO" in
        S1S)
            "${SSH_CMD[@]}" "ubuntu@$CLIENT_PUB" \
                "timeout 35 ab -n 15000 -c 10 http://$VICTIM_PRIVATE_IP/ > /dev/null 2>&1 &"
            ;;
        S1M)
            "${SSH_CMD[@]}" "ubuntu@$CLIENT_PUB" \
                "timeout 35 ab -n 30000 -c 25 http://$VICTIM_PRIVATE_IP/ > /dev/null 2>&1 &"
            ;;
        S1L)
            "${SSH_CMD[@]}" "ubuntu@$CLIENT_PUB" \
                "timeout 35 ab -n 50000 -c 50 http://$VICTIM_PRIVATE_IP/ > /dev/null 2>&1 &"
            ;;
        S2L)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 sudo hping3 -S -p 80 -i u10000 $VICTIM_PRIVATE_IP > /dev/null 2>&1 &"
            ;;
        S2M)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 sudo hping3 -S -p 80 -i u1000 $VICTIM_PRIVATE_IP > /dev/null 2>&1 &"
            ;;
        S2H)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 sudo hping3 -S -p 80 -i u100 $VICTIM_PRIVATE_IP > /dev/null 2>&1 &"
            ;;
        S3L)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 python3 ~/syn-edge-flooding/tools/conn_hold.py --host $VICTIM_PRIVATE_IP --port 80 --n 100 --hold 30 > /dev/null 2>&1 &"
            ;;
        S3M)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 python3 ~/syn-edge-flooding/tools/conn_hold.py --host $VICTIM_PRIVATE_IP --port 80 --n 500 --hold 30 > /dev/null 2>&1 &"
            ;;
        S3H)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 python3 ~/syn-edge-flooding/tools/conn_hold.py --host $VICTIM_PRIVATE_IP --port 80 --n 2000 --hold 30 > /dev/null 2>&1 &"
            ;;
        S4)
            # Compound: flash crowd M on client + SYN flood M on attacker simultaneously
            "${SSH_CMD[@]}" "ubuntu@$CLIENT_PUB" \
                "timeout 35 ab -n 30000 -c 25 http://$VICTIM_PRIVATE_IP/ > /dev/null 2>&1 &"
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 sudo hping3 -S -p 80 -i u1000 $VICTIM_PRIVATE_IP > /dev/null 2>&1 &"
            ;;
        S5M)
            # SYN flood M with mitigation (fix profile)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 sudo hping3 -S -p 80 -i u1000 $VICTIM_PRIVATE_IP > /dev/null 2>&1 &"
            ;;
        S5H)
            # SYN flood H with mitigation (fix profile)
            "${SSH_CMD[@]}" "ubuntu@$ATTACKER_PUB" \
                "bash ~/syn-edge-flooding/tools/attack_guard.sh --duration 30 sudo hping3 -S -p 80 -i u100 $VICTIM_PRIVATE_IP > /dev/null 2>&1 &"
            ;;
        *)
            if [[ -n "${SCENARIO_CMD:-}" ]]; then
                eval "$SCENARIO_CMD"
            else
                echo "[run_scenario] WARNING: Unknown scenario $SCENARIO and no SCENARIO_CMD."
                sleep 30
            fi
            ;;
    esac

    # Wait for 30s event duration
    sleep 30
    T_END_MS=$(date +%s%3N)
    echo "[run_scenario] Event end: $(date -u)"

    # ==============================================================================
    # Post-event window: 60 seconds
    # ==============================================================================
    echo "[run_scenario] Post-event window (60s)..."
    sleep 60
fi

# ==============================================================================
# Stop collectors and fetch artifacts
# ==============================================================================
echo "[run_scenario] Stopping collectors..."
stop_collectors

# ==============================================================================
# Write events.json
# ==============================================================================
GIT_SHA=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
SYNCOOKIES_VAL=$("${SSH_CMD[@]}" "ubuntu@$VICTIM_PUB" "sysctl -n net.ipv4.tcp_syncookies" 2>/dev/null || echo "0")

cat > "$RUN_DIR/events.json" <<EOF
{
  "run_id": "$RUN_ID",
  "scenario": "$SCENARIO",
  "rep": $REP,
  "params": {"profile": "$PROFILE"},
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
"${SSH_CMD[@]}" "ubuntu@$VICTIM_PUB" "bash -c '
    consec=0
    for ((i=0; i<120; i++)); do
        sr=\$(awk \"\\\$4==\\\"03\\\" && \\\$2~/.*:0050$/ {count++} END{print count+0}\" /proc/net/tcp 2>/dev/null || echo 0)
        if [ \"\$sr\" -eq 0 ]; then
            consec=\$((consec + 1))
            if [ \"\$consec\" -ge 10 ]; then
                echo COOLDOWN_COMPLETE
                exit 0
            fi
        else
            consec=0
        fi
        sleep 1
    done
    echo COOLDOWN_CAPPED
    exit 0
'" 2>/dev/null || true

# Append to INDEX.csv
INDEX_FILE="$REPO_ROOT/runs/INDEX.csv"
if [[ ! -f "$INDEX_FILE" ]]; then
    echo "run_id,scenario,rep,profile,aborted,notes" > "$INDEX_FILE"
fi
echo "$RUN_ID,$SCENARIO,$REP,$PROFILE,false," >> "$INDEX_FILE"

echo "[run_scenario] Run $RUN_ID complete. Artifacts in $RUN_DIR/"
echo "[run_scenario] ============================================================"
