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

# Determine if running on operator workstation (Darwin or external host)
IS_LOCAL_VICTIM=0
if [[ "$(uname -s)" != "Darwin" ]]; then
  LOCAL_IPS=$(hostname -I 2>/dev/null || ip addr show 2>/dev/null | grep -oE 'inet [0-9.]+' | awk '{print $2}' || true)
  VICTIM_IP="${VICTIM_PRIVATE_IP:-172.31.37.214}"
  if echo "$LOCAL_IPS" | grep -q "$VICTIM_IP"; then
    IS_LOCAL_VICTIM=1
  fi
fi

if [[ "$IS_LOCAL_VICTIM" -eq 1 ]]; then
  apply_local
else
  # Running from operator Mac/workstation: dispatch to victim via SSH
  if [[ -f "$LAB_ROOT/lab.env" ]]; then
    # shellcheck source=/dev/null
    source "$LAB_ROOT/lab.env"
  elif [[ -f "./lab.env" ]]; then
    # shellcheck source=/dev/null
    source "./lab.env"
  else
    echo "❌ Error: lab.env not found to dispatch to victim host." >&2
    exit 1
  fi

  SSH_KEY_RESOLVED=$(eval echo "$KEY_PATH")
  SSH_ARGS=(-i "$SSH_KEY_RESOLVED" -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes)

  echo "Dispatching profile '$PROFILE' to victim ($VICTIM_PUB)..."
  ssh "${SSH_ARGS[@]}" ubuntu@"$VICTIM_PUB" "bash -s -- $PROFILE" <<'REMOTE_EOF'
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

fi
