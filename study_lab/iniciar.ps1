$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $python) {
    & $python -m http.server 8080 --bind 127.0.0.1
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m http.server 8080 --bind 127.0.0.1
} else {
    & python -m http.server 8080 --bind 127.0.0.1
}
