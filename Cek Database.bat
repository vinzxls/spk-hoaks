@echo off
REM ============================================================
REM  SPK Penilaian Tingkat Risiko Penyebaran Hoaks
REM  Pemeriksa database: membaca saja, tidak mengubah data.
REM
REM  Pakai file ini kalau login gagal, untuk tahu penyebabnya.
REM ============================================================
title SPK Risiko Hoaks - Cek Database

setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [ERROR] Lingkungan Python belum dibuat.
    echo.
    echo Jalankan dulu di folder ini:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" cek_database.py
echo.
pause
endlocal
