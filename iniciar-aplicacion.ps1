$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$frontend = Join-Path $projectRoot "vc-master"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Primero ejecutar preparar-proyecto.ps1."
}
if (-not (Test-Path -LiteralPath (Join-Path $frontend "node_modules"))) {
    throw "Primero ejecutar preparar-proyecto.ps1 para instalar la interfaz."
}

$authLog = Join-Path $projectRoot "auth_core.out.log"
$authErrorLog = Join-Path $projectRoot "auth_core.error.log"
$organizationLog = Join-Path $projectRoot "organizacion_core.out.log"
$organizationErrorLog = Join-Path $projectRoot "organizacion_core.error.log"
$frontendLog = Join-Path $projectRoot "frontend.out.log"
$frontendErrorLog = Join-Path $projectRoot "frontend.error.log"

Start-Process -FilePath $python -ArgumentList "manage.py", "runserver", "127.0.0.1:8000", "--noreload" -WorkingDirectory (Join-Path $projectRoot "auth_core-master") -RedirectStandardOutput $authLog -RedirectStandardError $authErrorLog -WindowStyle Hidden
Start-Process -FilePath $python -ArgumentList "manage.py", "runserver", "127.0.0.1:8001", "--noreload" -WorkingDirectory (Join-Path $projectRoot "organizacion_core-master") -RedirectStandardOutput $organizationLog -RedirectStandardError $organizationErrorLog -WindowStyle Hidden

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
$pnpm = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
$bundledPnpm = "C:\Users\romer\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
$bundledNode = "C:\Users\romer\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"
if (-not $npm -and -not $pnpm -and (Test-Path -LiteralPath $bundledPnpm)) {
    $env:PATH = "$bundledNode;" + $env:PATH
    $packageManager = $bundledPnpm
} elseif ($pnpm) { $packageManager = $pnpm.Source }
elseif ($npm) { $packageManager = $npm.Source }
else { throw "No se encontró Node.js. Instala Node.js LTS y vuelve a intentar." }
Start-Process -FilePath $packageManager -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" -WorkingDirectory $frontend -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendErrorLog -WindowStyle Hidden

Start-Sleep -Seconds 4
Start-Process "http://127.0.0.1:5173"
Write-Host "Comunidad Inteligente está iniciándose en http://127.0.0.1:5173" -ForegroundColor Green
