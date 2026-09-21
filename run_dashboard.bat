@echo off
title Dashboard Visualisasi QoS Telekomunikasi
cd /d "%~dp0"
echo ===================================================
echo   Memulai Dashboard Visualisasi QoS Telekomunikasi
echo ===================================================
echo Menjalankan aplikasi Streamlit...
echo Buka browser di http://localhost:8501 jika tidak terbuka otomatis.
echo.
python -m streamlit run app.py
pause
