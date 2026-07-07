@echo off
cd /d "%~dp0"

echo Checking pygame...
python -m pip install pygame

echo Starting game...
python main.py

pause