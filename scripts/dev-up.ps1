# dev-up.ps1
# Starter et lokalt udviklingsmiljø:
#   - bridge i --fake mode (ingen ægte robot påkrævet)
#   - input-pipeline der peger på fake-bridge'en
#   - ui-server der peger på input
#
# Komponenterne starter i separate PowerShell-vinduer så de kan stoppes individuelt.
# Forudsætter at scripts/clone-all.ps1 er kørt og at venvs er sat op.

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot

$bridge = Join-Path $workspace "norma-robot-bridge"
$input  = Join-Path $workspace "norma-input"
$ui     = Join-Path $workspace "norma-ui"

if (-not (Test-Path $bridge)) {
    throw "norma-robot-bridge findes ikke. Kør scripts\clone-all.ps1 først."
}
if (-not (Test-Path $input)) {
    throw "norma-input findes ikke. Kør scripts\clone-all.ps1 først."
}
if (-not (Test-Path $ui)) {
    Write-Warning "norma-ui findes ikke endnu (det er OK i tidlige faser). Springer UI over."
}

# Bridge i fake-mode (Py 2.7 venv)
$bridgeCmd = "cd '$bridge'; .\.venv27\Scripts\Activate.ps1; python -m norma_bridge.main --fake --port 8080"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $bridgeCmd

Start-Sleep -Seconds 2

# Input-pipeline (Py 3.11 venv)
$inputCmd = "cd '$input'; .\.venv\Scripts\Activate.ps1; python -m norma_input.main --bridge http://localhost:8080"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $inputCmd

Start-Sleep -Seconds 2

# UI-server (Py 3.11 venv) — kun hvis repoet er klonet
if (Test-Path $ui) {
    $uiCmd = "cd '$ui'; .\.venv\Scripts\Activate.ps1; python -m norma_ui.main --input http://localhost:8090 --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiCmd
    Write-Host "Bridge, input og UI startet i separate vinduer. Luk dem for at stoppe."
} else {
    Write-Host "Bridge og input startet i separate vinduer. Luk dem for at stoppe."
}
