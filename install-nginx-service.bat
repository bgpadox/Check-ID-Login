@echo off
echo Installing Nginx as Windows Service...
sc create nginx binPath= "C:\nginx\nginx.exe" start= auto
sc description nginx "Nginx Web Server"
sc start nginx
echo Nginx service installed and started!
pause

