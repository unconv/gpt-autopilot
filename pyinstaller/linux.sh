#!/bin/bash
cd "$(dirname "$0")"

# clone and cd into repo
git clone https://github.com/unconv/gpt-autopilot.git
cd gpt-autopilot

# run pyinstaller
pyinstaller gpt-autopilot.py

# add prompts to package
cp -r prompts dist/gpt-autopilot/

# make zip package
cd dist/
mkdir -p ../../zip/; 
zip -r "../../zip/gpt-autopilot-linux.zip" gpt-autopilot

# remove git repo
cd ../../; rm -rf gpt-autopilot/
