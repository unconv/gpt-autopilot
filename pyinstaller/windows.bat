@echo off

REM clone and cd into repo
git clone https://github.com/unconv/gpt-autopilot.git
cd gpt-autopilot

REM run pyinstaller
pyinstaller gpt-autopilot.py

REM add system_message to package
copy system_message dist\gpt-autopilot\

REM get distro identifier
for /f "usebackq delims=" %%G in (`wmic os get Caption /value ^| findstr /r "^Caption="`) do set "distro=%%G"
set "distro=%distro: =-%"

REM make zip package using 7-Zip
cd dist
mkdir "..\..\zip\"
7z a "..\..\zip\gpt-autopilot-%distro%.zip" gpt-autopilot\*

REM remove git repo
cd ..\..\ & rmdir /s /q gpt-autopilot
