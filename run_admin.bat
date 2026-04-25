@echo off
:: Lance DiagPcNet directement en mode Administrateur
:: Ce script demande l'elevation UAC et utilise le venv Python du projet.

set "SCRIPT_DIR=%~dp0"
set "PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"
set "MAIN=%SCRIPT_DIR%main.py"

:: Verifier que le venv existe
if not exist "%PYTHON%" (
    echo [ERREUR] Python venv introuvable : %PYTHON%
    echo Verifiez que le venv est cree : python -m venv venv
    pause
    exit /b 1
)

:: Demande d'elevation via PowerShell (plus fiable que runas)
powershell -Command "Start-Process -FilePath '%PYTHON%' -ArgumentList '\"%MAIN%\"' -WorkingDirectory '%SCRIPT_DIR%' -Verb RunAs"
