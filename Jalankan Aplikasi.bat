@echo off
REM ============================================================
REM  SPK Penilaian Tingkat Risiko Penyebaran Hoaks
REM  Peluncur aplikasi. Klik dua kali untuk menjalankan.
REM
REM  Syarat sebelum menjalankan:
REM    1. MySQL (Laragon/XAMPP) sudah Start / berjalan.
REM    2. File .venv sudah ada di folder ini.
REM ============================================================
title SPK Risiko Hoaks

REM Pindah ke folder tempat file .bat ini berada.
cd /d "%~dp0"

REM Cek apakah virtual environment sudah ada.
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [ERROR] Virtual environment .venv tidak ditemukan.
    echo.
    echo Buka terminal di folder ini lalu jalankan:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Menjalankan aplikasi SPK Risiko Hoaks...
echo (Jendela ini biarkan terbuka selama aplikasi dipakai)
echo.

".venv\Scripts\python.exe" main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Aplikasi berhenti dengan kesalahan.
    echo Periksa pesan di atas. Pastikan MySQL sudah berjalan.
    echo.
    pause
)
