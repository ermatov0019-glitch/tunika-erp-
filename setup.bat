@echo off
title ERMATOV ERP - O'rnatish Tizimi
echo [1/4] Papkalarni yaratish...
if not exist "libs" mkdir libs

echo [2/4] Excel kutubxonasini (SheetJS) yuklab olish...
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js' -OutFile 'libs\xlsx.full.min.js'"

echo [3/4] Python kutubxonalarini o'rnatish (Flask, Flask-CORS)...
python -m pip install flask flask-cors --quiet

echo [4/4] Sozlamalarni tekshirish...
echo.
echo ======================================================
echo   O'rnatish muvaffaqiyatli yakunlandi!
echo   Endi tizimni 'START_ERP.bat' orqali ochishingiz mumkin.
echo ======================================================
pause
