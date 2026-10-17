@echo off
REM Instalasi follow up pembayaran: cek Python, pasang dependensi, siapkan folder data. Jalankan sekali.
cd /d "%~dp0"
title INSTALASI FOLLOW UP PEMBAYARAN

echo === Instalasi Follow Up Pembayaran ===
echo.

REM 1. Python 3.10 ke atas
set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
    echo [GAGAL] Python 3 tidak ditemukan di PATH.
    echo         Pasang Python 3.10 atau lebih baru dari https://www.python.org/downloads/
    echo         dan centang "Add python.exe to PATH" saat instalasi, lalu jalankan ulang berkas ini.
    pause
    exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [GAGAL] Versi Python terlalu lama. Dibutuhkan Python 3.10 atau lebih baru:
    %PY% --version
    pause
    exit /b 1
)
echo [OK] Python:
%PY% --version
echo.

REM 2. Dependensi
echo Memasang dependensi dari requirements.txt ...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [GAGAL] Pemasangan dependensi gagal. Periksa koneksi internet lalu jalankan ulang berkas ini.
    pause
    exit /b 1
)
%PY% -c "import DrissionPage" >nul 2>&1
if errorlevel 1 (
    echo [GAGAL] DrissionPage tidak bisa dimuat setelah dipasang.
    pause
    exit /b 1
)
echo [OK] Dependensi terpasang.
echo.

REM 3. Folder data per toko
%PY% -c "from src.stores import siapkan_folder; siapkan_folder()"
if errorlevel 1 (
    echo [GAGAL] Folder data tidak bisa dibuat.
    pause
    exit /b 1
)
echo [OK] Folder data siap di data\stores.
echo.

REM 4. Google Chrome (dipakai bot dan login toko)
set "ADA_CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "ADA_CHROME=1"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "ADA_CHROME=1"
set "P86=%ProgramFiles(x86)%"
if defined P86 if exist "%P86%\Google\Chrome\Application\chrome.exe" set "ADA_CHROME=1"
if defined ADA_CHROME (
    echo [OK] Google Chrome ditemukan.
) else (
    echo [PERINGATAN] Google Chrome tidak ditemukan. Pasang dari https://www.google.com/chrome/ sebelum menjalankan.
)
echo.

echo === Selesai ===
echo Jalankan follow_up_pembayaran.bat untuk membuka aplikasi.
echo Toko yang belum login: klik tombol Login pada kartu toko di aplikasi.
echo.
pause
