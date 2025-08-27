@echo off
set msg=%1
if "%msg%"=="" set msg=Actualización rápida
git add .
git commit -m "%msg%"
git push origin main
pause
