$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspace = Join-Path $projectRoot "Comunidad-Inteligente.code-workspace"
$code = Get-Command code -ErrorAction SilentlyContinue
if (-not $code) { throw "No se encontró Visual Studio Code. Ábrelo y selecciona Archivo > Abrir área de trabajo desde archivo." }
& $code.Source $workspace
