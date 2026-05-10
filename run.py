"""开发启动脚本"""
import sys
import os

# 设置 Qt 插件路径（修复 "Could not find the Qt platform plugin" 错误）
conda_lib = os.path.join(os.path.dirname(sys.executable), "Library", "lib", "qt6", "plugins")
if os.path.isdir(conda_lib):
    os.environ["QT_PLUGIN_PATH"] = conda_lib

sys.path.insert(0, os.path.dirname(__file__))
from src.main import main
main()
