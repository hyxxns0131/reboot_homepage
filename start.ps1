param([int]$Port = 5000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    & ./.venv/Scripts/python.exe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
& ./.venv/Scripts/python.exe scripts/setup_local.py
& ./.venv/Scripts/python.exe -m flask --app app:create_app setup-db
if ($LASTEXITCODE -ne 0) { throw 'Database setup failed.' }

# Another local app (e.g. a separate dashboard project) may already own the port.
# Opening that port would show the other app's login screen instead of this homepage.
function Test-PortBusy([int]$Number) {
    $null -ne (Get-NetTCPConnection -LocalPort $Number -State Listen -ErrorAction SilentlyContinue)
}
if (Test-PortBusy $Port) {
    $busy = $Port
    $Port = 5050
    while (Test-PortBusy $Port) { $Port++ }
    Write-Host "Port $busy is used by another program. Reboot homepage will use port $Port instead." -ForegroundColor Yellow
}
Write-Host "Reboot homepage: http://127.0.0.1:$Port" -ForegroundColor Green
& ./.venv/Scripts/python.exe -m flask --app app:create_app run --host 127.0.0.1 --port $Port
