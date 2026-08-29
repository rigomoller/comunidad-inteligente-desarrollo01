$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$code = Get-Command code -ErrorAction SilentlyContinue
if (-not $code) { throw "No se encontró Visual Studio Code. Ábrelo y selecciona Archivo > Abrir carpeta." }
& $code.Source $projectRoot
