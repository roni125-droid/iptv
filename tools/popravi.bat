@echo off
setlocal
cd /d "%~dp0"

echo.
echo ================================================
echo   Popravljanje seznama
echo ================================================
echo.

if not exist "popravi.py" goto ni_skripte
if not exist "exyu.m3u" goto ni_seznama

set "PY="
where py >nul 2>nul && set "PY=py"
if defined PY goto imam_python
where python >nul 2>nul && set "PY=python"
:imam_python
if not defined PY goto ni_pythona

echo Uporabljam Python: %PY%
echo.
echo Delam troje:
echo   1. odstranim kanale, ki jih streznik dokoncno zavraca
echo   2. kanale s pokvarjenim potrdilom preklopim na HTTP
echo   3. kanale z vec kakovostmi pripnem na najboljso sliko
echo.
echo Traja nekaj minut. Datoteke exyu.m3u ne spreminjam.
echo.

%PY% popravi.py exyu.m3u --out exyu-ok.m3u > porocilo-popravilo.txt 2>&1
type porocilo-popravilo.txt

echo.
if exist "exyu-ok.m3u" goto uspeh
echo NEKAJ JE SLO NAROBE. Datoteka exyu-ok.m3u ni nastala.
goto konec

:uspeh
echo ================================================
echo   KONCANO. Nastala je datoteka exyu-ok.m3u
echo   To prenesite na bokse.
echo ================================================
echo.
echo Izpis je shranjen v porocilo-popravilo.txt v tej mapi.
echo To datoteko lahko prilozite v klepet namesto fotografije.
goto konec

:ni_skripte
echo NAPAKA: v tej mapi ni datoteke popravi.py
echo Prenesite jo iz klepeta in jo dajte poleg te datoteke.
goto konec

:ni_seznama
echo NAPAKA: v tej mapi ni datoteke exyu.m3u
echo Prenesite jo iz klepeta in jo dajte poleg te datoteke.
goto konec

:ni_pythona
echo NAPAKA: Python ni najden.
echo Namestite ga z naslova www.python.org/downloads
echo Med namestitvijo OBVEZNO obkljukajte "Add python.exe to PATH".

:konec
echo.
pause
