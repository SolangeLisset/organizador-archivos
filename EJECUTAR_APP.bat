@echo off
REM ============================================================
REM EJECUTAR_APP.BAT
REM Abre el Organizador de Archivos con doble clic
REM Autor: SolangeLisset
REM ============================================================

REM Cambia el directorio al lugar donde está este archivo .bat
cd /d "%~dp0"

REM Verifica que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python no esta instalado.
    echo  Descargalo desde: https://www.python.org/downloads/
    echo  Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b
)

REM Ejecutar la app (pythonw no abre la consola negra de fondo)
start pythonw organizador.py

REM Si pythonw falla, usar python normal
if errorlevel 1 (
    python organizador.py
)
