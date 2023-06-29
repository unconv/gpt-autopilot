@echo off
cd /d "%~dp0"

REM clone and cd into repo
git clone https://github.com/unconv/gpt-autopilot.git
cd gpt-autopilot

REM run pyinstaller
pyinstaller gpt-autopilot.py

REM add prompts to package
xcopy /E prompts dist\gpt-autopilot\prompts\

REM make zip package using 7-Zip
cd dist
mkdir "..\..\zip\"
7z a "..\..\zip\gpt-autopilot-windows.zip" gpt-autopilot\*

REM remove git repo
cd ..\..\ & rmdir /s /q gpt-autopilot
