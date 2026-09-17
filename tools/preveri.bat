@echo off
setlocal
cd /d "%~dp0"

echo.
echo ================================================
echo   Preverjanje, kateri kanali pri vas delajo
echo ================================================
echo.

if not exist "check.py" goto ni_skripte
if not exist "exyu.m3u" goto ni_seznama

set "PY="
where py >nul 2>nul && set "PY=py"
if defined PY goto imam_python
where python >nul 2>nul && set "PY=python"
:imam_python
if not defined PY goto ni_pythona

echo Uporabljam Python: %PY%
echo Odpiram tri hkratne povezave do vsakega kanala, kot bi to naredili boksi.
echo To traja nekaj minut. Datoteke ne spreminjam.
echo.

%PY% check.py exyu.m3u --android --devices 3
goto konec

:ni_skripte
echo NAPAKA: v tej mapi ni datoteke check.py
goto konec

:ni_seznama
echo NAPAKA: v tej mapi ni datoteke exyu.m3u
goto konec

:ni_pythona
echo NAPAKA: Python ni najden.
echo Namestite ga z naslova www.python.org/downloads

:konec
echo.
pause
