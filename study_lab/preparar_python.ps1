$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    $interpreters = (& py -0p 2>$null | Out-String)
    if ($interpreters -match '3\.11') { & py -3.11 -m venv .venv }
    else { & py -3 -m venv .venv }
  } else { & python -m venv .venv }
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual' }
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-study.txt
& .\.venv\Scripts\python.exe -c 'import numpy,pandas,matplotlib,sklearn;print("Entorno Python OK")'
Write-Host 'El entorno está listo. Activar: .\.venv\Scripts\Activate.ps1'
