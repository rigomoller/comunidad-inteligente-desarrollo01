$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$frontend = Join-Path $projectRoot "vc-master"
$environmentFile = Join-Path $projectRoot ".env"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Primero ejecutar preparar-proyecto.ps1."
}
if (-not (Test-Path -LiteralPath (Join-Path $frontend "node_modules"))) {
    throw "Primero ejecutar preparar-proyecto.ps1 para instalar la interfaz."
}
if (-not (Test-Path -LiteralPath $environmentFile)) {
    throw "Falta .env. Ejecuta configurar-postgresql.ps1 y luego preparar-proyecto.ps1."
}

Push-Location (Join-Path $projectRoot "auth_core-master")
try {
    & $python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        throw "No hay conexión con comunidad_auth. Confirma que el servicio PostgreSQL esté iniciado."
    }
} finally { Pop-Location }

Push-Location (Join-Path $projectRoot "organizacion_core-master")
try {
    & $python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        throw "No hay conexión con comunidad_organizacion. Confirma que el servicio PostgreSQL esté iniciado."
    }
} finally { Pop-Location }

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

if (-not (Get-Command node.exe -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath (Join-Path $bundledNode "node.exe"))) {
    $env:PATH = "$bundledNode;" + $env:PATH
}

if (-not $npm -and -not $pnpm -and (Test-Path -LiteralPath $bundledPnpm)) {
    $packageManager = $bundledPnpm
} elseif ($pnpm) { $packageManager = $pnpm.Source }
elseif ($npm) { $packageManager = $npm.Source }
else { throw "No se encontró Node.js. Instala Node.js LTS y vuelve a intentar." }
Start-Process -FilePath $packageManager -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" -WorkingDirectory $frontend -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendErrorLog -WindowStyle Hidden

Start-Sleep -Seconds 4
try {
    Start-Process "http://127.0.0.1:5173"
} catch {
    Write-Warning "La aplicación quedó iniciada, pero Windows no permitió abrir el navegador automáticamente. Abrir manualmente http://127.0.0.1:5173"
}
Write-Host "Comunidad Inteligente está iniciándose en http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "Base de datos activa: PostgreSQL (comunidad_auth + comunidad_organizacion)."
