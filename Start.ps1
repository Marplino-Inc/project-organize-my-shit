param(
    [switch]$Demo,
    [int]$Port = 8765
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/'
    }
    uv sync --locked --no-dev
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    $appArguments = @('run', '--no-dev', '--locked', 'python', 'main.py', '--port', "$Port")
    if ($Demo) { $appArguments += '--demo' }
    & uv @appArguments
    if ($LASTEXITCODE -ne 0) { throw 'The application stopped with an error.' }
} finally {
    Pop-Location
}
