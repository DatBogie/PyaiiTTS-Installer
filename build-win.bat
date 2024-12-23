@echo off

REM Create venv
python3 -m venv .\.venv

REM Source venv
call .\.venv\Scripts\activate

REM Install dependancies
pip install -r .\requirements.txt

REM Build and copy assets
pyinstaller --onefile --noconsole --name PyaiiTTS-Installer .\installer.py

REM Finish
echo "Press return to exit."
pause