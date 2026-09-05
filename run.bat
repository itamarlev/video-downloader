@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting YouTube Downloader...
python app.py
pause
