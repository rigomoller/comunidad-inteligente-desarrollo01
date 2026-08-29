$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$environmentPath = Join-Path $projectRoot ".venv"

function Find-Python {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) { return $pythonCommand.Source }
    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) { return $pyCommand.Source }
    throw "Falta Python. Instala Python 3.12 o superior y vuelve a ejecutar este archivo."
}

if (-not (Test-Path -LiteralPath $environmentPath)) {
    $systemPython = Find-Python
    & $systemPython -m venv $environmentPath
}

$python = Join-Path $environmentPath "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $projectRoot "auth_core-master\requirements.txt")
& $python -m pip install -r (Join-Path $projectRoot "organizacion_core-master\requirements.txt")

Push-Location (Join-Path $projectRoot "auth_core-master")
try {
    & $python manage.py migrate
    & $python manage.py seed_demo
} finally { Pop-Location }

Push-Location (Join-Path $projectRoot "organizacion_core-master")
try {
    & $python manage.py migrate
    & $python manage.py seed_demo
} finally { Pop-Location }

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
$pnpm = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
$bundledPnpm = "C:\Users\romer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
$bundledNode = "C:\Users\romer\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"
if (-not $npm -and -not $pnpm -and (Test-Path -LiteralPath $bundledPnpm)) {
    $env:PATH = "$bundledNode;" + $env:PATH
    $packageManager = $bundledPnpm
} elseif ($pnpm) { $packageManager = $pnpm.Source }
elseif ($npm) { $packageManager = $npm.Source }
else { throw "El backend está preparado, pero falta Node.js LTS para instalar la interfaz." }

Push-Location (Join-Path $projectRoot "vc-master")
try { & $packageManager install } finally { Pop-Location }

Write-Host "Proyecto preparado correctamente." -ForegroundColor Green
Write-Host "Ahora ejecutar: iniciar-aplicacion.ps1"
