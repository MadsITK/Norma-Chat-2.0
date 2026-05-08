#!/usr/bin/env bash
# clone-all.sh
# Kloner alle Norma sub-repos ind i workspace-mappen som søsterklones.
# Sub-repos er IKKE git submodules — de er løse klones der lever uafhængigt
# af workspace-repoet.
#
# Brug:
#   ./scripts/clone-all.sh
#
# Når et sub-repo allerede er klonet, gør scriptet intet.
# Tilpas $names / $urls nedenfor når sub-repos publiceres til en remote.

set -euo pipefail

workspace="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parallelle arrays: navn på lokal mappe -> git remote URL
# OPDATER disse URLs når sub-repos publiceres.
names=(
    "norma-robot-bridge"
    "norma-input"
    "norma-ui"
)
urls=(
    "TBD: <git remote URL for norma-robot-bridge>"
    "TBD: <git remote URL for norma-input>"
    "TBD: <git remote URL for norma-ui>"
)

for i in "${!names[@]}"; do
    name="${names[$i]}"
    url="${urls[$i]}"
    target="$workspace/$name"

    if [[ -d "$target/.git" ]]; then
        echo "[skip]  $name eksisterer allerede ($target)"
        continue
    fi

    if [[ "$url" == TBD:* ]]; then
        echo "[skip]  $name — remote-URL er ikke sat. Opret repoet manuelt."
        continue
    fi

    echo "[clone] $name <- $url"
    git clone "$url" "$target"
done

echo ""
echo "Færdig. Husk at sætte hvert sub-repos venv op:"
echo "  norma-robot-bridge: Python 2.7  (.venv27)"
echo "  norma-input       : Python 3.11+ (.venv)"
echo "  norma-ui          : Python 3.11+ (.venv)"
