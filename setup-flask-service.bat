@echo off
echo Setting up Flask API as Windows Service...
echo.
echo Please make sure NSSM is installed in C:\nssm\win64
echo.
pause

cd C:\nssm\win64

echo Installing FlaskAPI service...
nssm install FlaskAPI

echo.
echo Service installed! Please configure it manually:
echo 1. Path: C:\Python\python.exe (or your Python path)
echo 2. Startup directory: C:\Users\USER\Desktop\Mitmproxy\Check ID LOGIN
echo 3. Arguments: server.py
echo.
echo Then run: nssm start FlaskAPI
pause

