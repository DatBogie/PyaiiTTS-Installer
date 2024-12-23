#!/bin/sh

# Create venv
python3 -m venv ./.venv

# Source venv
source ./.venv/bin/activate

# Install dependancies
pip3 install -r ./requirements.txt

# Build and copy assets
pyinstaller --onefile --noconsole --name PyaiiTTS-Installer ./installer.py && rm ./dist/PyaiiTTS-Installer

# Finish
read -p "Press return to exit."