@echo off
setlocal
cd /d "%~dp0"
title Poker AI - Local Sandbox
set "PATH=%LOCALAPPDATA%\Programs\Python\Launcher;%LOCALAPPDATA%\Programs\Python\Python312;%ProgramFiles%\Git\cmd;%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
py -3.12 -c "import sys; assert sys.version_info[:2]==(3,12)" >nul 2>&1
if not errorlevel 1 goto python_ready
python -c "import sys; assert sys.version_info[:2]==(3,12)" >nul 2>&1
if not errorlevel 1 goto python_fallback
where winget >nul 2>&1
if errorlevel 1 goto missing_python
echo Installing free Python 3.12 via winget...
winget install --id Python.Python.3.12 --exact --source winget --scope user --accept-source-agreements --accept-package-agreements
set "PATH=%LOCALAPPDATA%\Programs\Python\Launcher;%LOCALAPPDATA%\Programs\Python\Python312;%PATH%"
py -3.12 -c "import sys; assert sys.version_info[:2]==(3,12)" >nul 2>&1
if errorlevel 1 goto missing_python
:python_ready
set "POKER_PY=py -3.12"
goto git_check
:python_fallback
set "POKER_PY=python"
:git_check
where git >nul 2>&1
if not errorlevel 1 goto run
where winget >nul 2>&1
if errorlevel 1 goto missing_git
echo Installing free Git for Windows via winget...
winget install --id Git.Git --exact --source winget --accept-source-agreements --accept-package-agreements
set "PATH=%ProgramFiles%\Git\cmd;%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
where git >nul 2>&1
if errorlevel 1 goto missing_git
:run
%POKER_PY% scripts\bootstrap_sandbox.py %*
if errorlevel 1 goto failed
exit /b 0
:missing_python
echo Python 3.12 is unavailable. Install Python 3.12 and run this file again.
goto failed
:missing_git
echo Git is unavailable. Install Git for Windows and run this file again.
:failed
echo Poker sandbox could not start. Read the error above. Your files have been preserved.
pause
exit /b 1
