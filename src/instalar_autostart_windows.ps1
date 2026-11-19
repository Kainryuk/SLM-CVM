<#
.SYNOPSIS
Configura a inicialização automática do proxy CVM (porta 11435) no login do Windows,
aponta OLLAMA_HOST para o proxy e instala um fallback `ollama.cmd` no PATH que
liga o proxy automaticamente caso esteja desligado.
#>
param(
    [switch]$Remover,
    [int]$Porta = 11435,
    [int]$NumGpu = 16
)

$StartupDir = [Environment]::GetFolderPath("Startup")
$VbsPath = Join-Path $StartupDir "SLM-CVM-Proxy.vbs"
$Raiz = Split-Path -Parent $PSScriptRoot
$ProxyScript = Join-Path $Raiz "src\proxy_cvm.py"
$EnsureScript = Join-Path $Raiz "src\garantir_proxy.py"
$UserScripts = Join-Path $env:APPDATA "Python\Python314\Scripts"
$OllamaWrapper = Join-Path $UserScripts "ollama.cmd"

if ($Remover) {
    if (Test-Path $VbsPath) { Remove-Item $VbsPath -Force }
    if (Test-Path $OllamaWrapper) { Remove-Item $OllamaWrapper -Force }
    [Environment]::SetEnvironmentVariable("OLLAMA_HOST", $null, "User")
    Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%proxy_cvm.py%'" | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[ok] Auto-inicialização e fallback removidos; OLLAMA_HOST restaurado."
    exit 0
}

$PythonW = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonW) { $PythonW = (Get-Command python.exe).Source }
$PythonExe = (Get-Command python.exe).Source
$OllamaReal = (Get-Command ollama.exe -ErrorAction SilentlyContinue).Source
if (-not $OllamaReal) {
    $OllamaReal = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
}

$VbsContent = "Set WshShell = CreateObject(""WScript.Shell"")`r`nWshShell.Run """"""$PythonW"""" """"$ProxyScript"""" --port $Porta --num-gpu $NumGpu"", 0, False`r`n"
[System.IO.File]::WriteAllText($VbsPath, $VbsContent, [System.Text.UTF8Encoding]::new($false))

if (-not (Test-Path $UserScripts)) { New-Item -ItemType Directory -Force -Path $UserScripts | Out-Null }
$WrapperContent = "@echo off`r`nchcp 65001 >nul`r`nif /i ""%~1""==""serve"" goto :run_real`r`n""$PythonExe"" ""$EnsureScript"" --port $Porta --num-gpu $NumGpu`r`n:run_real`r`n""$OllamaReal"" %*`r`n"
[System.IO.File]::WriteAllText($OllamaWrapper, $WrapperContent, [System.Text.UTF8Encoding]::new($false))

[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "http://127.0.0.1:$Porta", "User")
Write-Host "[ok] Atalho Startup: $VbsPath"
Write-Host "[ok] Fallback automático instalado: $OllamaWrapper"
Write-Host "[ok] OLLAMA_HOST (Usuário): http://127.0.0.1:$Porta"
