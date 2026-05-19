@echo off
title ERMATOV ERP - Ishga tushirish
color 0b
echo ======================================================
echo             ERMATOV ERP TIZIMI
echo ======================================================
echo.
echo Tizim yuklanmoqda (Port: 8000)...

:: Eskilarini tozalash
taskkill /f /im python.exe >nul 2>&1

:: Serverni fon oyna sifatida ishga tushirish
start "Tizim Serveri" cmd /c "python server.py"

:: Server ishga tushishini kutish
timeout /t 2 >nul

:: Brauzerda ochish
start "" "http://localhost:8000"
exit
