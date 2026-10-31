@echo off
REM ============================================================
REM  SPK Penilaian Tingkat Risiko Penyebaran Hoaks
REM  Pemasang awal: membuat database + mengisi data dasar.
REM
REM  Cukup dijalankan SEKALI, setelah MySQL (Laragon) menyala.
REM  Skrip ini menolak berjalan bila database sudah berisi
REM  jawaban kuesioner, supaya data asli tidak terhapus.
REM ============================================================
title SPK Risiko Hoaks - Impor Database

setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   IMPOR DATABASE SPK RISIKO HOAKS
echo ============================================================
echo.
echo Skrip ini:
echo   1. Membuat database "spk_hoaks" beserta tabelnya.
echo   2. Mengisi data awal: admin, 6 kriteria, 30 subkriteria,
echo      dan matriks perbandingan Fuzzy AHP.
echo.
pause

REM ---- Cari program mysql.exe -------------------------------
set "MYSQL="
for %%P in (mysql.exe) do if not defined MYSQL set "MYSQL=%%~$PATH:P"

if not defined MYSQL if exist "C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe" set "MYSQL=C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe"
if not defined MYSQL if exist "C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysql.exe" set "MYSQL=C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysql.exe"
if not defined MYSQL if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL=C:\xampp\mysql\bin\mysql.exe"
if not defined MYSQL for /d %%D in ("C:\laragon\bin\mysql\*") do if not defined MYSQL if exist "%%~fD\bin\mysql.exe" set "MYSQL=%%~fD\bin\mysql.exe"

if not defined MYSQL (
    echo [ERROR] Program mysql.exe tidak ditemukan.
    echo.
    echo Pastikan Laragon atau XAMPP sudah terpasang dan sudah
    echo dinyalakan, lalu jalankan file ini lagi.
    echo.
    echo Atau impor manual lewat terminal:
    echo     mysql -u root ^< db\schema.sql
    echo     mysql -u root spk_hoaks ^< db\seed.sql
    echo.
    pause
    exit /b 1
)

echo.
echo Memakai: %MYSQL%
echo.

REM ---- Pastikan MySQL menyala -------------------------------
"%MYSQL%" -u root -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Tidak bisa terhubung ke MySQL.
    echo.
    echo 1. Buka Laragon, klik Start All, tunggu MySQL berwarna hijau.
    echo 2. Kalau user root memakai password, impor manual:
    echo        mysql -u root -p ^< db\schema.sql
    echo        mysql -u root -p spk_hoaks ^< db\seed.sql
    echo.
    pause
    exit /b 1
)

REM ---- Jangan timpa data yang sudah ada ---------------------
if exist "%~dp0db\schema.sql" (
    "%MYSQL%" -u root -N -B -e "SELECT COUNT(*) FROM spk_hoaks.jawaban_kuesioner;" >"%TEMP%\spk_jw.txt" 2>nul
    set /p JUMLAH_JAWABAN=<"%TEMP%\spk_jw.txt"
    del "%TEMP%\spk_jw.txt" >nul 2>&1
)

if defined JUMLAH_JAWABAN if not "%JUMLAH_JAWABAN%"=="0" (
    echo [DIBATALKAN] Database "spk_hoaks" sudah berisi data.
    echo.
    echo Ditemukan %JUMLAH_JAWABAN% jawaban kuesioner tersimpan.
    echo Mengisi ulang data awal akan menghapus jawaban itu,
    echo jadi skrip ini berhenti demi keamanan.
    echo.
    echo Kalau memang ingin memulai dari nol, hapus dulu
    echo database-nya lewat Laragon, lalu jalankan skrip ini lagi.
    echo.
    pause
    exit /b 1
)

echo [1/2] Membuat tabel ...
"%MYSQL%" -u root < db\schema.sql
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal membuat tabel. Periksa pesan di atas.
    echo.
    pause
    exit /b 1
)

echo [2/2] Mengisi data awal ...
"%MYSQL%" -u root spk_hoaks < db\seed.sql
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal mengisi data awal. Periksa pesan di atas.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   SELESAI
echo ============================================================
echo.
echo Database "spk_hoaks" siap dipakai.
echo Login admin: admin / admin123
echo.
echo Langkah berikutnya: klik dua kali "Jalankan Aplikasi.bat".
echo.
pause
endlocal
