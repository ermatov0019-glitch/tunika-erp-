@echo off
title Tunika ERP - Mobile Access (Host-Header Fix)
color 0b
echo ======================================================
echo          ERMATOV ERP - MOBIL ULASH TIZIMI
echo ======================================================
echo.

:: Eskilarini tozalash
taskkill /f /im python.exe >nul 2>&1

echo [1/2] Lokal server ishga tushmoqda (Port: 8000)...
start "SERVER" cmd /k "python server.py"

timeout /t 3 >nul

echo [2/2] Ngrok tunnel ochilmoqda...
echo.
if exist "ngrok.exe" (
    start "NGROK" cmd /k "ngrok http 8000 --host-header=rewrite --authtoken 3DnvrNwuhZpwap3sWDjGCjZnQqV_7U4LnEcMpqwNBwL8PNhdp"
) else (
    start "NGROK" cmd /k "ngrok http 8000 --host-header=rewrite --authtoken 3DnvrNwuhZpwap3sWDjGCjZnQqV_7U4LnEcMpqwNBwL8PNhdp"
)

echo.
echo ======================================================
echo MUHIM: 
echo 1. Ikkala oyna ham ochiq tursin.
echo 2. Ngrok oynasidagi yangi linkni iPhone'da oching.
echo ======================================================
pause
