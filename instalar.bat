@echo off
setlocal
title Instalar NexStage

set "NXS_TARGET=%~dp0start.bat"
set "NXS_WORKDIR=%~dp0"
set "NXS_ICON=%~dp0web\favicon.ico"

if not exist "%NXS_TARGET%" (
  echo ERRO: start.bat nao foi encontrado.
  echo Extraia e mantenha todos os arquivos do NexStage na mesma pasta.
  pause
  exit /b 1
)

if not exist "%NXS_ICON%" (
  echo ERRO: o icone do NexStage nao foi encontrado.
  echo Extraia e mantenha todos os arquivos do NexStage na mesma pasta.
  pause
  exit /b 1
)

where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo ERRO: o Windows PowerShell nao foi encontrado.
  pause
  exit /b 1
)

powershell.exe -NoProfile -NonInteractive -Command ^
  "$desktop=[Environment]::GetFolderPath('Desktop'); $shell=New-Object -ComObject WScript.Shell; $shortcut=$shell.CreateShortcut((Join-Path $desktop 'NexStage.lnk')); $shortcut.TargetPath=$env:NXS_TARGET; $shortcut.WorkingDirectory=$env:NXS_WORKDIR; $shortcut.IconLocation=($env:NXS_ICON + ',0'); $shortcut.Description='NexStage - Apresentacao para igrejas'; $shortcut.WindowStyle=7; $shortcut.Save()"

if errorlevel 1 (
  echo.
  echo Nao foi possivel criar o atalho.
  pause
  exit /b 1
)

echo.
echo NexStage instalado com sucesso!
echo O atalho foi criado na Area de Trabalho.
echo Voce ja pode fechar esta janela e abrir o NexStage pelo novo icone.
pause
endlocal
