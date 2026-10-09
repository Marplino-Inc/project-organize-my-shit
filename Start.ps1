param(
    [switch]$Demo,
    [ValidateRange(1024, 65535)]
    [int]$Port = 8765,
    [string]$Database,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
if ($Demo -and $Database) { throw 'Choose either -Demo or -Database, not both.' }
if ($Demo -and -not $PSBoundParameters.ContainsKey('Port')) { $Port = 8766 }
# Resolve caller-relative database paths before switching to the application folder.
if ($Database) { $Database = [System.IO.Path]::GetFullPath($Database) }
Push-Location $PSScriptRoot
try {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $uvPath = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local\bin\uv.exe' }
    if (-not (Test-Path -LiteralPath $uvPath)) {
        throw 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/'
    }
    & $uvPath sync --locked --no-dev
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    $appArguments = @('run', '--no-dev', '--locked', 'python', 'main.py', '--port', "$Port")
    if ($Demo) { $appArguments += '--demo' }
    if ($Database) { $appArguments += @('--db', $Database) }
    if ($NoBrowser) { $appArguments += '--no-browser' }
    $logDirectory = Join-Path $env:LOCALAPPDATA 'ProjectOrganize/logs'
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $runLog = Join-Path $logDirectory ("startup-{0}-{1}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'), $PID)
    Write-Host "Organize is opening at http://127.0.0.1:$Port. Keep this window open; press Ctrl+C to stop."
    Write-Host "Startup log: $runLog"
    # Windows PowerShell treats native stderr as error records. Preserve it without
    # replacing Python's actual exit code and diagnosis with a generic exception.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $uvPath @appArguments 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $runLog
        $appExit = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previousPreference }
    if ($appExit -ne 0) { throw "Organize exited with code $appExit. The cause is shown above and saved in $runLog" }
} finally {
    Pop-Location
}
