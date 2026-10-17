@echo off
REM Follow up pembayaran - buka UI web (http://127.0.0.1:8765). Tutup jendela ini untuk menghentikan.
cd /d "%~dp0"
title FOLLOW UP PEMBAYARAN

set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
    echo [GAGAL] Python 3 tidak ditemukan di PATH.
    pause
    exit /b 1
)

%PY% -c "import DrissionPage" >nul 2>&1
if errorlevel 1 (
    echo Memasang DrissionPage...
    %PY% -m pip install DrissionPage || (pause & exit /b 1)
)

%PY% -m src.web
set "KODE=%errorlevel%"
if not "%KODE%"=="0" echo [GAGAL] Program berhenti dengan kode %KODE%.
pause
exit /b %KODE%
