#!/usr/bin/env bash
# tools/probe.sh — 1 Hz HTTP probe from client to victim (§5.6 schema)
# Usage: probe.sh <victim_ip> <out_csv>
# Outputs: ts_ms,http_code,t_connect_s,t_total_s,ok  (one row per second)
set -euo pipefail

VICTIM_IP="${1:-${VICTIM_PRIVATE_IP:-}}"
OUT="${2:-probe.csv}"

if [[ -z "$VICTIM_IP" ]]; then
    echo "Usage: $0 <victim_ip> <out_csv>" >&2
    exit 1
fi

echo "ts_ms,http_code,t_connect_s,t_total_s,ok" > "$OUT"

next_tick=$(date +%s%3N)

while true; do
    ts_ms=$(date +%s%3N)

    # curl: measure connect time, total time, http status code
    read -r http_code t_connect t_total < <(
        curl -s -o /dev/null \
            --max-time 3 \
            -w "%{http_code} %{time_connect} %{time_total}" \
            "http://$VICTIM_IP/" 2>/dev/null || echo "000 0 3"
    )

    ok=0
    if [[ "$http_code" == "200" && $(echo "$t_total < 3" | awk '{print ($1 < 3) ? 1 : 0}') == "1" ]]; then
        ok=1
    fi

    echo "$ts_ms,$http_code,$t_connect,$t_total,$ok" >> "$OUT"

    # Monotonic 1 Hz pacing
    next_tick=$((next_tick + 1000))
    now_ms=$(date +%s%3N)
    sleep_ms=$((next_tick - now_ms))
    if (( sleep_ms > 0 )); then
        sleep "$(echo "scale=3; $sleep_ms/1000" | bc)"
    fi
done

