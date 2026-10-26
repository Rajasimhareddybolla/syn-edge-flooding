#!/usr/bin/env bash
# tools/sync_from_cloud.sh — Sync completed run artifacts from cloud client instance to local Mac
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$REPO_ROOT/lab.env" ]]; then
    # shellcheck source=/dev/null
    source "$REPO_ROOT/lab.env"
fi

: "${CLIENT_PUB:?}" "${KEY_PATH:?}"

echo "[sync] Syncing runs/ and INDEX.csv from cloud client instance ($CLIENT_PUB)..."
rsync -avz --exclude '*.pcap' -e "ssh -i $KEY_PATH -o StrictHostKeyChecking=no" \
    "ubuntu@$CLIENT_PUB:~/syn-edge-flooding/runs/" "$REPO_ROOT/runs/"

echo "[sync] Current runs index:"
cat "$REPO_ROOT/runs/INDEX.csv"
echo "[sync] Total completed runs: $(($(wc -l < "$REPO_ROOT/runs/INDEX.csv") - 1))/65"

