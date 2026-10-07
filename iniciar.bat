@echo off
rem ============================================================
rem  QBASWING COVERS v1.0
rem  Cada coleccion merece su portada.
rem  Un producto de QBASwing Designer
rem ============================================================
chcp 65001 >nul
title QBASWING COVERS v1.0
cd /d "%~dp0"
color 07

echo.
echo  ============================================================
echo   QBASWING COVERS v1.0
echo   Cada coleccion merece su portada.
echo   Un producto de QBASwing Designer
echo  ============================================================
echo.

rem --- 1) Elegir el ejecutable para la arquitectura de Windows -------
set "EJECUTABLE=QBASWING COVERS.exe"
if /i "%PROCESSOR_ARCHITECTURE%"=="AMD64" set "EJECUTABLE=QBASWING COVERS x64.exe"
if defined PROCESSOR_ARCHITEW6432 set "EJECUTABLE=QBASWING COVERS x64.exe"

if exist "%EJECUTABLE%" (
    echo   Ejecutable encontrado. Iniciando...
    echo   Arquitectura seleccionada: %EJECUTABLE%
    echo   Se abrira el navegador. No cierres esta ventana mientras lo usas.
    echo.
    "%EJECUTABLE%" %*
    set "CODIGO=%ERRORLEVEL%"
    goto terminar
)

rem --- 2) Si no hay exe, se intenta con Python instalado -------------
echo   No se encontro "QBASWING COVERS.exe". Se intentara con Python.
echo.

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py" )
if not defined PY (
    for %%D in ("C:\Python313\python.exe" "C:\Python312\python.exe" "C:\Python311\python.exe" "C:\Python310\python.exe") do (
        if not defined PY if exist %%D set "PY=%%D"
    )
)

if not defined PY (
    echo   No se encontro Python en esta computadora.
    echo.
    echo   Para usar esta version necesitas Python, que es gratuito y oficial.
    echo   Descargalo aqui:  https://www.python.org/downloads/
    echo.
    echo   Durante la instalacion marca la casilla "Add Python to PATH".
    echo.
    echo   O usa el archivo "QBASWING COVERS.exe", que no necesita Python.
    echo.
    pause
    exit /b 1
)

echo   Python encontrado: %PY%
echo   Verificando version...
%PY% -c "import sys;print('   Python',sys.version.split()[0]);raise SystemExit(0 if sys.version_info>=(3,8) else 1)"
if errorlevel 1 (
    echo.
    echo   La version de Python es demasiado antigua. Se necesita 3.8 o mayor.
    echo   Descarga una version nueva en: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo   Iniciando QBASWING COVERS...
echo   Se abrira el navegador. No cierres esta ventana mientras lo usas.
echo.
%PY% "qbaswing_covers.py" %*
set "CODIGO=%ERRORLEVEL%"

:terminar
if not "%CODIGO%"=="0" (
    echo.
    echo   ============================================================
    echo   El programa termino con un aviso. Codigo: %CODIGO%
    echo   Revisa el archivo  qbawing_covers.log  para ver el detalle.
    echo   ============================================================
    echo.
    pause
)
exit /b %CODIGO%
