#!/usr/bin/env bash
# ==============================================================================
# attack_guard.sh — Fail-Safe Bounded Attack Execution Wrapper
# Reference: docs/AGENTS_tcp_flood_lab.md §4.2, §4.4; PROJECT.md Features 1–5
# ==============================================================================
# Invariants Enforced (Fail-Closed):
# 1. Target IP == VICTIM_PRIVATE_IP from lab.env (exact string match).
# 2. Duration <= 60 s (enforced via system timeout).
# 3. SYN rate <= 10,000 pps (hping3 interval >= u100; strictly reject --flood and --faster).
# 4. Connection-hold count <= 2,000.
# 5. Kill switch file /tmp/LAB_STOP is absent (checked pre-launch and monitored live).
# ==============================================================================
set -euo pipefail

# ------------------------------------------------------------------------------
# 1. Check Pre-Launch Kill Switch
# ------------------------------------------------------------------------------
if [[ -e "/tmp/LAB_STOP" ]]; then
    echo "❌ GUARD REFUSAL: Emergency kill switch active (/tmp/LAB_STOP exists)." >&2
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. Load Environment Contract (lab.env)
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." 2>/dev/null && pwd || echo "")"

if [[ -z "${VICTIM_PRIVATE_IP:-}" ]]; then
    if [[ -n "${LAB_ENV:-}" && -f "$LAB_ENV" ]]; then
        # shellcheck source=/dev/null
        source "$LAB_ENV"
    elif [[ -f "$PWD/lab.env" ]]; then
        # shellcheck source=/dev/null
        source "$PWD/lab.env"
    elif [[ -n "$REPO_ROOT" && -f "$REPO_ROOT/lab.env" ]]; then
        # shellcheck source=/dev/null
        source "$REPO_ROOT/lab.env"
    elif [[ -f "/home/ubuntu/tcp-flood-lab/lab.env" ]]; then
        # shellcheck source=/dev/null
        source "/home/ubuntu/tcp-flood-lab/lab.env"
    elif [[ -f "/home/ubuntu/syn-edge-flooding/lab.env" ]]; then
        # shellcheck source=/dev/null
        source "/home/ubuntu/syn-edge-flooding/lab.env"
    fi
fi

if [[ -z "${VICTIM_PRIVATE_IP:-}" ]]; then
    echo "❌ GUARD REFUSAL: Unable to resolve VICTIM_PRIVATE_IP from lab.env." >&2
    exit 1
fi

# ------------------------------------------------------------------------------
# 3. Parse Wrapper Options and Tool Invocation
# ------------------------------------------------------------------------------
DRY_RUN="${GUARD_DRY_RUN:-0}"
DECLARED_DURATION="${GUARD_DURATION:-}"

# Parse leading guard options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run|--check)
            DRY_RUN=1
            shift
            ;;
        --duration|-d)
            if [[ $# -lt 2 ]]; then
                echo "❌ GUARD REFUSAL: --duration requires a seconds argument." >&2
                exit 1
            fi
            DECLARED_DURATION="$2"
            shift 2
            ;;
        --help|-h)
            cat <<EOF
Usage: attack_guard.sh [--dry-run] [--duration <secs>] <tool> <tool_args...>

Fail-safe execution wrapper enforcing safety invariants:
  - Target must match VICTIM_PRIVATE_IP ($VICTIM_PRIVATE_IP)
  - Duration <= 60 seconds
  - SYN flood rate <= 10,000 pps (interval >= u100; no --flood or --faster)
  - Connection hold count <= 2,000
  - Emergency kill switch /tmp/LAB_STOP absent
EOF
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -eq 0 ]]; then
    echo "❌ GUARD REFUSAL: No command provided to attack_guard.sh." >&2
    exit 1
fi

# ------------------------------------------------------------------------------
# 4. Handle leading 'timeout' command if supplied
# ------------------------------------------------------------------------------
COMMAND=("$@")
TOOL_OFFSET=0

if [[ "${COMMAND[0]}" == "timeout" ]]; then
    # Parse timeout command options and duration
    idx=1
    while [[ $idx -lt ${#COMMAND[@]} ]]; do
        arg="${COMMAND[$idx]}"
        if [[ "$arg" =~ ^-- ]]; then
            idx=$((idx + 1))
        elif [[ "$arg" =~ ^-[a-zA-Z] && ! "$arg" =~ ^-[0-9] ]]; then
            idx=$((idx + 1))
        else
            # Found timeout duration argument
            raw_dur="$arg"
            # Strip trailing unit if present
            dur_num="${raw_dur%[smhd]}"
            dur_unit="${raw_dur#"${dur_num}"}"
            dur_sec="$dur_num"
            if [[ "$dur_unit" == "m" ]]; then
                dur_sec=$((dur_num * 60))
            fi
            DECLARED_DURATION="$dur_sec"
            TOOL_OFFSET=$((idx + 1))
            break
        fi
    done
fi

# Extract sub-command after timeout
ACTUAL_CMD=("${COMMAND[@]:$TOOL_OFFSET}")
if [[ ${#ACTUAL_CMD[@]} -eq 0 ]]; then
    echo "❌ GUARD REFUSAL: No attack tool found after timeout prefix." >&2
    exit 1
fi

# Keep the command that will be executed separate from the normalized form
# used for validation below.
EXEC_CMD=("${ACTUAL_CMD[@]}")

# hping3 requires CAP_NET_RAW on Ubuntu.  Permit only a bare leading sudo,
# then validate the command it elevates exactly as if sudo were absent.  This
# avoids turning the wrapper into a generic privileged-command launcher.
if [[ "${ACTUAL_CMD[0]}" == "sudo" ]]; then
    if [[ ${#ACTUAL_CMD[@]} -lt 2 || "${ACTUAL_CMD[1]}" == -* ]]; then
        echo "❌ GUARD REFUSAL: sudo may only prefix a supported attack tool." >&2
        exit 1
    fi
    ACTUAL_CMD=("${ACTUAL_CMD[@]:1}")
fi

# Identify base tool name
TOOL_NAME="$(basename "${ACTUAL_CMD[0]}")"
if [[ "$TOOL_NAME" == "python" || "$TOOL_NAME" == "python3" ]]; then
    if [[ ${#ACTUAL_CMD[@]} -gt 1 ]]; then
        TOOL_NAME="$(basename "${ACTUAL_CMD[1]}")"
    fi
fi

# ------------------------------------------------------------------------------
# 5. Invariant Check: Duration Clamping (<= 60 s)
# ------------------------------------------------------------------------------
# Also scan arguments for tool-specific duration flags (e.g. --hold <N>, -d <N>)
for ((i=0; i<${#ACTUAL_CMD[@]}; i++)); do
    arg="${ACTUAL_CMD[$i]}"
    case "$arg" in
        --hold|--duration|-d)
            if (( i + 1 < ${#ACTUAL_CMD[@]} )); then
                val="${ACTUAL_CMD[$((i + 1))]}"
                val="${val%[smhd]}"
                if [[ "$val" =~ ^[0-9]+$ ]]; then
                    if [[ -z "$DECLARED_DURATION" ]] || (( val > DECLARED_DURATION )); then
                        DECLARED_DURATION="$val"
                    fi
                fi
            fi
            ;;
        --hold=*|--duration=*)
            val="${arg#*=}"
            val="${val%[smhd]}"
            if [[ "$val" =~ ^[0-9]+$ ]]; then
                if [[ -z "$DECLARED_DURATION" ]] || (( val > DECLARED_DURATION )); then
                    DECLARED_DURATION="$val"
                fi
            fi
            ;;
    esac
done

if [[ -n "$DECLARED_DURATION" ]]; then
    if ! [[ "$DECLARED_DURATION" =~ ^[0-9]+$ ]]; then
        echo "❌ GUARD REFUSAL: Invalid duration '$DECLARED_DURATION'. Must be integer seconds." >&2
        exit 1
    fi
    if (( DECLARED_DURATION > 60 )); then
        echo "❌ GUARD REFUSAL: Duration ${DECLARED_DURATION}s exceeds maximum allowed cap of 60s." >&2
        exit 1
    fi
    ENFORCED_TIMEOUT="$DECLARED_DURATION"
else
    # Default to hard clamp of 60 seconds if unspecified
    ENFORCED_TIMEOUT=60
fi

# ------------------------------------------------------------------------------
# 6. Invariant Check: Tool Specific Rules (hping3 / conn_hold.py)
# ------------------------------------------------------------------------------
if [[ "$TOOL_NAME" == *"hping"* ]]; then
    # Invariant: SYN rate <= 10,000 pps (interval >= u100; strictly reject --flood and --faster)
    for ((i=0; i<${#ACTUAL_CMD[@]}; i++)); do
        arg="${ACTUAL_CMD[$i]}"
        
        # Check forbidden rate flags
        if [[ "$arg" == "--flood" ]]; then
            echo "❌ GUARD REFUSAL: Forbidden flag --flood detected. Attack rate exceeds safety bounds." >&2
            exit 1
        fi
        if [[ "$arg" == "--faster" ]]; then
            echo "❌ GUARD REFUSAL: Forbidden flag --faster detected. Attack rate exceeds safety bounds." >&2
            exit 1
        fi

        # Check interval specifications
        interval_val=""
        if [[ "$arg" == "-i" || "$arg" == "--interval" ]]; then
            if (( i + 1 < ${#ACTUAL_CMD[@]} )); then
                interval_val="${ACTUAL_CMD[$((i + 1))]}"
            fi
        elif [[ "$arg" =~ ^-i.+ ]]; then
            interval_val="${arg#-i}"
        elif [[ "$arg" =~ ^--interval=.+ ]]; then
            interval_val="${arg#--interval=}"
        fi

        if [[ -n "$interval_val" ]]; then
            if [[ "$interval_val" =~ ^u([0-9]+)$ ]]; then
                usec="${BASH_REMATCH[1]}"
                if (( usec < 100 )); then
                    echo "❌ GUARD REFUSAL: SYN rate exceeds limit. Interval 'u${usec}' (< u100) exceeds 10,000 pps." >&2
                    exit 1
                fi
            elif [[ "$interval_val" =~ ^m([0-9]+)$ ]]; then
                msec="${BASH_REMATCH[1]}"
                if (( msec == 0 )); then
                    echo "❌ GUARD REFUSAL: Zero interval specified ('$interval_val')." >&2
                    exit 1
                fi
            elif [[ "$interval_val" =~ ^([0-9]+)$ ]]; then
                sec="${BASH_REMATCH[1]}"
                if (( sec == 0 )); then
                    echo "❌ GUARD REFUSAL: Zero interval specified ('$interval_val')." >&2
                    exit 1
                fi
            fi
        fi
    done
fi

if [[ "$TOOL_NAME" == *"conn_hold"* ]]; then
    # Invariant: connection-hold count <= 2,000
    for ((i=0; i<${#ACTUAL_CMD[@]}; i++)); do
        arg="${ACTUAL_CMD[$i]}"
        conn_count=""
        if [[ "$arg" == "-n" || "$arg" == "--n" || "$arg" == "--connections" || "$arg" == "--count" ]]; then
            if (( i + 1 < ${#ACTUAL_CMD[@]} )); then
                conn_count="${ACTUAL_CMD[$((i + 1))]}"
            fi
        elif [[ "$arg" =~ ^--n=([0-9]+) || "$arg" =~ ^--connections=([0-9]+) || "$arg" =~ ^--count=([0-9]+) || "$arg" =~ ^-n([0-9]+) ]]; then
            conn_count="${BASH_REMATCH[1]}"
        fi

        if [[ -n "$conn_count" ]]; then
            if ! [[ "$conn_count" =~ ^[0-9]+$ ]]; then
                echo "❌ GUARD REFUSAL: Invalid connection count '$conn_count'." >&2
                exit 1
            fi
            if (( conn_count > 2000 )); then
                echo "❌ GUARD REFUSAL: Connection count $conn_count exceeds maximum allowed cap of 2,000." >&2
                exit 1
            fi
        fi
    done
fi

# ------------------------------------------------------------------------------
# 7. Invariant Check: Target IP Verification (String-Exact to VICTIM_PRIVATE_IP)
# ------------------------------------------------------------------------------
TARGET_MATCHED=0

for ((i=0; i<${#ACTUAL_CMD[@]}; i++)); do
    arg="${ACTUAL_CMD[$i]}"

    # Check explicit host flags (e.g. --host <ip>, -H <ip>)
    if [[ "$arg" == "--host" || "$arg" == "-H" ]]; then
        if (( i + 1 < ${#ACTUAL_CMD[@]} )); then
            target_ip="${ACTUAL_CMD[$((i + 1))]}"
            if [[ "$target_ip" != "$VICTIM_PRIVATE_IP" ]]; then
                echo "❌ GUARD REFUSAL: Unauthorized target IP '$target_ip' does not match VICTIM_PRIVATE_IP ($VICTIM_PRIVATE_IP)." >&2
                exit 1
            fi
            TARGET_MATCHED=1
        fi
    elif [[ "$arg" =~ ^--host=(.+) ]]; then
        target_ip="${BASH_REMATCH[1]}"
        if [[ "$target_ip" != "$VICTIM_PRIVATE_IP" ]]; then
            echo "❌ GUARD REFUSAL: Unauthorized target IP '$target_ip' does not match VICTIM_PRIVATE_IP ($VICTIM_PRIVATE_IP)." >&2
            exit 1
        fi
        TARGET_MATCHED=1
    elif [[ "$arg" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        # Standalone IPv4 literal detected
        if [[ "$arg" != "$VICTIM_PRIVATE_IP" ]]; then
            echo "❌ GUARD REFUSAL: Unauthorized target IP '$arg' does not match VICTIM_PRIVATE_IP ($VICTIM_PRIVATE_IP)." >&2
            exit 1
        fi
        TARGET_MATCHED=1
    fi
done

if (( TARGET_MATCHED == 0 )); then
    echo "❌ GUARD REFUSAL: Target IP is missing or does not match VICTIM_PRIVATE_IP ($VICTIM_PRIVATE_IP)." >&2
    exit 1
fi

# ------------------------------------------------------------------------------
# 8. Execution or Dry-Run Output
# ------------------------------------------------------------------------------
if (( DRY_RUN == 1 )); then
    echo "[GUARD_AUTHORIZED] All safety invariants verified."
    echo "  Target IP:        $VICTIM_PRIVATE_IP (MATCH)"
    echo "  Timeout Enforced: ${ENFORCED_TIMEOUT}s"
    echo "  Kill Switch:      ABSENT"
    echo "  Command:          ${ACTUAL_CMD[*]}"
    exit 0
fi

# Real Execution: Launch wrapped in system timeout and active kill-switch watchdog
timeout --preserve-status --kill-after=5s "${ENFORCED_TIMEOUT}s" "${EXEC_CMD[@]}" &
ATTACK_PID=$!

# Live watchdog for emergency kill switch
while kill -0 "$ATTACK_PID" 2>/dev/null; do
    if [[ -e "/tmp/LAB_STOP" ]]; then
        echo "❌ EMERGENCY HALT: /tmp/LAB_STOP detected during execution. Terminating process $ATTACK_PID." >&2
        kill -TERM "$ATTACK_PID" 2>/dev/null || true
        sleep 0.5
        kill -KILL "$ATTACK_PID" 2>/dev/null || true
        wait "$ATTACK_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 0.2
done

wait "$ATTACK_PID"
EXIT_CODE=$?
exit $EXIT_CODE
