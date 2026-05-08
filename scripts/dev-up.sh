#!/usr/bin/env bash
# dev-up.sh
# Starter et lokalt udviklingsmiljø:
#   - bridge i --fake mode (ingen ægte robot påkrævet)
#   - input-pipeline der peger på fake-bridge'en
#   - ui-server der peger på input
#
# Komponenterne starter som background-jobs i samme terminal og logger til
# logs/*.log. Ctrl+C dræber dem alle via trap.
# Forudsætter at scripts/clone-all.sh er kørt og at venvs er sat op.

set -euo pipefail

workspace="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bridge="$workspace/norma-robot-bridge"
input="$workspace/norma-input"
ui="$workspace/norma-ui"

if [[ ! -d "$bridge" ]]; then
    echo "norma-robot-bridge findes ikke. Kør scripts/clone-all.sh først." >&2
    exit 1
fi
if [[ ! -d "$input" ]]; then
    echo "norma-input findes ikke. Kør scripts/clone-all.sh først." >&2
    exit 1
fi
if [[ ! -d "$ui" ]]; then
    echo "[warn] norma-ui findes ikke endnu (det er OK i tidlige faser). Springer UI over." >&2
fi

logs="$workspace/logs"
mkdir -p "$logs"

pids=()

cleanup() {
    echo ""
    echo "[stop] Lukker komponenter ned..."
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Bridge i fake-mode (Py 2.7 venv)
echo "[start] bridge  -> http://localhost:8080  (logs/bridge.log)"
(
    cd "$bridge"
    # shellcheck disable=SC1091
    source .venv27/bin/activate
    exec python -m norma_bridge.main --fake --port 8080
) >"$logs/bridge.log" 2>&1 &
pids+=($!)

sleep 2

# Input-pipeline (Py 3.11 venv)
echo "[start] input   -> http://localhost:8090  (logs/input.log)"
(
    cd "$input"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    exec python -m norma_input.main --bridge http://localhost:8080
) >"$logs/input.log" 2>&1 &
pids+=($!)

sleep 2

# UI-server (Py 3.11 venv) — kun hvis repoet er klonet
if [[ -d "$ui" ]]; then
    echo "[start] ui      -> http://localhost:8000  (logs/ui.log)"
    (
        cd "$ui"
        # shellcheck disable=SC1091
        source .venv/bin/activate
        exec python -m norma_ui.main --input http://localhost:8090 --port 8000
    ) >"$logs/ui.log" 2>&1 &
    pids+=($!)
    echo ""
    echo "Bridge, input og UI startet i baggrunden. Ctrl+C for at stoppe alle."
else
    echo ""
    echo "Bridge og input startet i baggrunden. Ctrl+C for at stoppe alle."
fi

echo "Følg logs med:  tail -f logs/*.log"
echo ""

wait
