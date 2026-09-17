@echo off
setlocal
cd /d "%~dp0"

echo.
echo ================================================
echo   Priprava seznama z najboljso sliko
echo ================================================
echo.

if not exist "kakovost.py" goto ni_skripte
if not exist "exyu.m3u" goto ni_seznama

set "PY="
where py >nul 2>nul && set "PY=py"
if defined PY goto imam_python
where python >nul 2>nul && set "PY=python"
:imam_python
if not defined PY goto ni_pythona

echo Uporabljam Python: %PY%
echo Povezujem se na streznike postaj. To traja minuto ali dve.
echo.

%PY% kakovost.py exyu.m3u --out exyu-hd.m3u

echo.
if exist "exyu-hd.m3u" goto uspeh
echo NEKAJ JE SLO NAROBE. Datoteka exyu-hd.m3u ni nastala.
echo Preberite sporocila zgoraj in mi jih pokazite.
goto konec

:uspeh
echo ================================================
echo   KONCANO. Nastala je datoteka exyu-hd.m3u
echo   Najdete jo v tej isti mapi.
echo ================================================
goto konec

:ni_skripte
echo NAPAKA: v tej mapi ni datoteke kakovost.py
echo Prenesite jo iz klepeta in jo dajte poleg te datoteke.
goto konec

:ni_seznama
echo NAPAKA: v tej mapi ni datoteke exyu.m3u
echo Prenesite jo iz klepeta in jo dajte poleg te datoteke.
goto konec

:ni_pythona
echo NAPAKA: Python ni najden.
echo.
echo Namestite ga z naslova www.python.org/downloads
echo Med namestitvijo OBVEZNO obkljukajte "Add python.exe to PATH".
goto konec

:konec
echo.
pause
