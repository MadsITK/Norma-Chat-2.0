# clone-all.ps1
# Kloner alle Norma sub-repos ind i workspace-mappen som søsterklones.
# Sub-repos er IKKE git submodules — de er løse klones der lever uafhængigt
# af workspace-repoet.
#
# Brug:
#   .\scripts\clone-all.ps1
#
# Når et sub-repo allerede er klonet, gør scriptet intet.
# Tilpas $repos-tabellen når sub-repos publiceres til en remote.

$ErrorActionPreference = "Stop"

# Find workspace-roden (parent til scripts/)
$workspace = Split-Path -Parent $PSScriptRoot

# Liste over sub-repos: navn på lokal mappe -> git remote URL
# OPDATER disse URLs når sub-repos publiceres.
$repos = @{
    "norma-robot-bridge" = "TBD: <git remote URL for norma-robot-bridge>"
    "norma-input"        = "TBD: <git remote URL for norma-input>"
    "norma-ui"           = "TBD: <git remote URL for norma-ui>"
}

foreach ($name in $repos.Keys) {
    $target = Join-Path $workspace $name
    $url = $repos[$name]

    if (Test-Path (Join-Path $target ".git")) {
        Write-Host "[skip]  $name eksisterer allerede ($target)"
        continue
    }

    if ($url -like "TBD:*") {
        Write-Host "[skip]  $name — remote-URL er ikke sat. Opret repoet manuelt."
        continue
    }

    Write-Host "[clone] $name <- $url"
    git clone $url $target
}

Write-Host ""
Write-Host "Færdig. Husk at sætte hvert sub-repos venv op:"
Write-Host "  norma-robot-bridge: Python 2.7  (.venv27)"
Write-Host "  norma-input       : Python 3.11+ (.venv)"
Write-Host "  norma-ui          : Python 3.11+ (.venv)"
