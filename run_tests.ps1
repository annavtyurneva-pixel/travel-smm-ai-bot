$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

# Отдельная папка текущего процесса обходит конфликты прав системного TEMP.
$testTemp = Join-Path $projectRoot ".tmp\pytest-$PID"
New-Item -ItemType Directory -Path $testTemp -Force | Out-Null
$env:TEMP = $testTemp
$env:TMP = $testTemp

& ".\.venv\Scripts\python.exe" -m pytest -q -p no:cacheprovider
exit $LASTEXITCODE
