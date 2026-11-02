@echo off
setlocal EnableExtensions
title Compilar NexStage 0.5.4
cd /d "%~dp0"

echo.
echo ========================================
echo   NexStage 0.5.4 - Build para Windows
echo ========================================
echo.

where py.exe >nul 2>nul
if errorlevel 1 (
  echo ERRO: Python 3 nao foi encontrado.
  echo Instale o Python 64 bits e marque "Add Python to PATH".
  goto :failure
)

if not exist ".venv-build\Scripts\python.exe" (
  echo Criando ambiente isolado de compilacao...
  py -3 -m venv .venv-build
  if errorlevel 1 goto :failure
)

set "NXS_PYTHON=%CD%\.venv-build\Scripts\python.exe"
echo Instalando ferramentas de build...
"%NXS_PYTHON%" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto :failure

echo Executando testes...
"%NXS_PYTHON%" -m unittest discover -s tests -v
if errorlevel 1 goto :failure

echo Gerando NexStage.exe sem console...
"%NXS_PYTHON%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --windowed ^
  --noupx ^
  --name NexStage ^
  --icon "web\favicon.ico" ^
  --version-file "packaging\windows\version_info.txt" ^
  --contents-directory app ^
  --add-data "web;web" ^
  --hidden-import pystray._win32 ^
  --collect-all imageio_ffmpeg ^
  windows_launcher.py
if errorlevel 1 goto :failure

copy /Y "README.md" "dist\NexStage\README.md" >nul
copy /Y "LICENSE.txt" "dist\NexStage\LICENSE.txt" >nul
copy /Y "CHANGELOG-0.5.4.md" "dist\NexStage\CHANGELOG-0.5.4.md" >nul

set "NXS_ISCC="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "NXS_ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "NXS_ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined NXS_ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "NXS_ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined NXS_ISCC for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined NXS_ISCC set "NXS_ISCC=%%I"

if not defined NXS_ISCC (
  echo.
  echo ERRO: Inno Setup 6 nao foi encontrado.
  echo Instale pelo site https://jrsoftware.org/isdl.php e execute este arquivo novamente.
  goto :failure
)

if not exist "release" mkdir "release"
echo Criando o instalador tradicional...
"%NXS_ISCC%" "packaging\windows\NexStage.iss"
if errorlevel 1 goto :failure

echo.
echo BUILD CONCLUIDO.
echo Arquivo: release\NexStage-Setup.exe
echo Publique esse EXE como asset da release do GitHub com exatamente esse nome.
echo.
pause
exit /b 0

:failure
echo.
echo A compilacao foi interrompida. Leia o erro acima, corrija e tente novamente.
echo.
pause
exit /b 1
