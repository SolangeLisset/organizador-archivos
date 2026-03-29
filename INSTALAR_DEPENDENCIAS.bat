@echo off
REM ============================================================
REM INSTALAR_DEPENDENCIAS.BAT v2.0
REM Autor: SolangeLisset
REM ============================================================
echo.
echo  ============================================
echo   Organizador de Archivos v2.0 - Instalador
echo  ============================================
echo.
python -m pip install --upgrade pip --quiet
echo  [1/4] mutagen (metadatos de musica)...
python -m pip install mutagen
echo.
echo  [2/4] pypdf (metadatos de PDFs)...
python -m pip install pypdf
echo.
echo  [3/4] ebooklib (metadatos de EPUBs)...
python -m pip install ebooklib
echo.
echo  [4/6] Pillow (procesamiento de imagenes / EXIF)...
python -m pip install Pillow
echo.
echo  [5/6] requests (API HTTP)
python -m pip install requests
echo.
echo  [6/6] tkinterdnd2 (arrastrar y soltar - NUEVO v2.0)...
python -m pip install tkinterdnd2
echo.
echo  ============================================
echo   Instalacion completada. Ejecuta EJECUTAR_APP.bat
echo  ============================================
echo.
pause
