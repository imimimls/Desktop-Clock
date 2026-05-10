@echo off
chcp 65001 >nul
cd /d "%~dp0"
set QT_PLUGIN_PATH=D:\Miniconda3\Library\lib\qt6\plugins
python run.py
pause
