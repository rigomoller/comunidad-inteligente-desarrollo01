$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$environmentFile = Join-Path $projectRoot ".env"

function Find-PostgreSqlTool([string]$toolName) {
    $command = Get-Command "$toolName.exe" -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    $installRoot = "C:\Program Files\PostgreSQL"
    if (Test-Path -LiteralPath $installRoot) {
        $candidate = Get-ChildItem -LiteralPath $installRoot -Directory |
            Sort-Object { [version]$_.Name } -Descending |
            ForEach-Object { Join-Path $_.FullName "bin\$toolName.exe" } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1
        if ($candidate) { return $candidate }
    }
    return $null
}

function ConvertTo-PlainText([Security.SecureString]$secureValue) {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}

function New-RandomSecret([int]$byteCount = 32) {
    $bytes = New-Object byte[] $byteCount
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToHexString($bytes).ToLowerInvariant()
}

function Read-EnvironmentValues([string]$path) {
    $values = @{}
    if (Test-Path -LiteralPath $path) {
        foreach ($line in Get-Content -LiteralPath $path) {
            if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                $values[$Matches[1]] = $Matches[2]
            }
        }
    }
    return $values
}

$psql = Find-PostgreSqlTool "psql"
if (-not $psql) {
    throw @"
PostgreSQL no está instalado. Instala PostgreSQL 14 o superior desde:
https://www.postgresql.org/download/windows/

Durante la instalación incluye PostgreSQL Server, pgAdmin y Command Line Tools.
Después vuelve a ejecutar este archivo.
"@
}

$postgresHost = Read-Host "Servidor PostgreSQL [127.0.0.1]"
if ([string]::IsNullOrWhiteSpace($postgresHost)) { $postgresHost = "127.0.0.1" }
$postgresPort = Read-Host "Puerto PostgreSQL [5432]"
if ([string]::IsNullOrWhiteSpace($postgresPort)) { $postgresPort = "5432" }
$adminUser = Read-Host "Usuario administrador de PostgreSQL [postgres]"
if ([string]::IsNullOrWhiteSpace($adminUser)) { $adminUser = "postgres" }
$adminSecurePassword = Read-Host "Contraseña elegida al instalar PostgreSQL" -AsSecureString
$adminPassword = ConvertTo-PlainText $adminSecurePassword

$appUser = "comunidad_app"
$authDatabase = "comunidad_auth"
$organizationDatabase = "comunidad_organizacion"
$values = Read-EnvironmentValues $environmentFile
$appPassword = $values["POSTGRES_PASSWORD"]
if ([string]::IsNullOrWhiteSpace($appPassword)) { $appPassword = New-RandomSecret 24 }

$sqlFile = Join-Path ([IO.Path]::GetTempPath()) ("comunidad-postgresql-" + [guid]::NewGuid().ToString("N") + ".sql")
$sql = @"
DO `$setup`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$appUser') THEN
        CREATE ROLE $appUser LOGIN PASSWORD '$appPassword';
    ELSE
        ALTER ROLE $appUser WITH LOGIN PASSWORD '$appPassword';
    END IF;
END
`$setup`$;

SELECT 'CREATE DATABASE $authDatabase OWNER $appUser'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$authDatabase')\gexec
SELECT 'CREATE DATABASE $organizationDatabase OWNER $appUser'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$organizationDatabase')\gexec
ALTER DATABASE $authDatabase OWNER TO $appUser;
ALTER DATABASE $organizationDatabase OWNER TO $appUser;
"@

try {
    [IO.File]::WriteAllText($sqlFile, $sql, (New-Object Text.UTF8Encoding($false)))
    $env:PGPASSWORD = $adminPassword
    & $psql --host $postgresHost --port $postgresPort --username $adminUser --dbname postgres --set ON_ERROR_STOP=1 --file $sqlFile
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL rechazó la configuración. Revisa usuario, contraseña, puerto y servicio." }
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    $adminPassword = $null
    Remove-Item -LiteralPath $sqlFile -Force -ErrorAction SilentlyContinue
}

if (-not $values.ContainsKey("DJANGO_SECRET_KEY") -or [string]::IsNullOrWhiteSpace($values["DJANGO_SECRET_KEY"])) {
    $values["DJANGO_SECRET_KEY"] = New-RandomSecret 32
}
$values["DEBUG"] = if ($values.ContainsKey("DEBUG")) { $values["DEBUG"] } else { "1" }
$values["POSTGRES_HOST"] = $postgresHost
$values["POSTGRES_PORT"] = $postgresPort
$values["POSTGRES_USER"] = $appUser
$values["POSTGRES_PASSWORD"] = $appPassword
$values["AUTH_POSTGRES_DB"] = $authDatabase
$values["ORGANIZATION_POSTGRES_DB"] = $organizationDatabase
$values["POSTGRES_CONN_MAX_AGE"] = "60"
$values["POSTGRES_CONNECT_TIMEOUT"] = "5"
$values["USE_SQLITE"] = "0"
foreach ($optionalKey in @("AI_API_URL", "AI_API_KEY", "AI_MODEL")) {
    if (-not $values.ContainsKey($optionalKey)) {
        $values[$optionalKey] = if ($optionalKey -eq "AI_MODEL") { "gpt-4.1-mini" } else { "" }
    }
}

$orderedKeys = @(
    "DJANGO_SECRET_KEY", "DEBUG", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER",
    "POSTGRES_PASSWORD", "AUTH_POSTGRES_DB", "ORGANIZATION_POSTGRES_DB",
    "POSTGRES_CONN_MAX_AGE", "POSTGRES_CONNECT_TIMEOUT", "USE_SQLITE",
    "AI_API_URL", "AI_API_KEY", "AI_MODEL"
)
$environmentLines = foreach ($key in $orderedKeys) { "$key=$($values[$key])" }
$extraKeys = $values.Keys | Where-Object { $_ -notin $orderedKeys } | Sort-Object
$environmentLines += foreach ($key in $extraKeys) { "$key=$($values[$key])" }
[IO.File]::WriteAllLines($environmentFile, $environmentLines, (New-Object Text.UTF8Encoding($false)))

Write-Host "PostgreSQL quedó configurado correctamente." -ForegroundColor Green
Write-Host "Bases creadas: $authDatabase y $organizationDatabase"
Write-Host "La clave técnica quedó guardada únicamente en .env (protegido por .gitignore)."
Write-Host "Siguiente paso: ejecutar preparar-proyecto.ps1"
