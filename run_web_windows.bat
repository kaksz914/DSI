@echo off
title DSI WEB AUDITOR - Windows C2 Backend
color 0A

echo [*] Inicializando Suite DSI - WEB AUDITOR (Versão Windows)

:: Tenta instalar o Flask
echo [*] Verificando servidor Web Flask...
python -m pip install flask >nul 2>&1

:: Inicia o servidor web no background ou em terminal
echo =================================================
echo        [ DSI CYBERPUNK WEB AUDITOR ]             
echo =================================================
echo 1. O Servidor Local (C2) esta online.
echo 2. Nao feche esta janela CMD.
echo 3. Acesse http://localhost:5000 no navegador.
echo =================================================

:: Aguarda 2 segundos e abre o navegador padrao do Windows
timeout /t 2 /nobreak >nul
start http://localhost:5000

:: Lanca o Backend do Windows
python web_auditor_windows.py

pause
