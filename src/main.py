"""公考计时器 - 主入口"""
import sys
import os

# 修复 Qt 插件路径：conda 环境下 PySide6 和 Qt 插件分开放置
_conda_prefix = os.path.dirname(os.path.dirname(sys.executable))
_qt_plugin_path = os.path.join(_conda_prefix, "Library", "lib", "qt6", "plugins")
if os.path.isdir(_qt_plugin_path):
    os.environ.setdefault("QT_PLUGIN_PATH", _qt_plugin_path)

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from .data_manager import DataManager
from .exam_manager import ExamManager, ExamMode
from .reminder import Reminder
from .anti_screensaver import AntiScreensaver
from .hotkey_manager import HotkeyManager
from .ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("公考计时器")
    app.setQuitOnLastWindowClosed(False)

    # 初始化各模块
    data_mgr = DataManager()
    config = data_mgr.load_config()

    exam_mgr = ExamManager()
    modules = config.get("xingce_modules", [])
    exam_mgr.set_mode(ExamMode.XINGCE, modules, 120)

    reminder = Reminder()
    reminder_cfg = config.get("reminder", {})
    reminder.enabled = reminder_cfg.get("enabled", True)
    reminder.sound_enabled = reminder_cfg.get("sound", False)
    reminder.flash_enabled = reminder_cfg.get("flash", True)

    anti_ss = AntiScreensaver()
    hotkey_mgr = HotkeyManager()

    # 创建主窗口
    window = MainWindow(exam_mgr, data_mgr, reminder, hotkey_mgr, anti_ss)

    # 应用外观设置
    appearance = config.get("appearance", {})
    window._set_theme(appearance.get("theme", "dark"))
    window.setWindowOpacity(appearance.get("opacity", 0.9))

    # 注册快捷键（需要 window handle，先 show 再注册）
    window.show()

    hotkeys = config.get("hotkeys", {})
    for name, key_str in hotkeys.items():
        hotkey_mgr.register_hotkey(name, key_str, window)
    # 空格键固定为切换下一模块
    hotkey_mgr.register_hotkey("next_module", "Space", window)

    # 快捷键响应
    def on_hotkey(name):
        if name == "start_pause":
            window.start_pause()
        elif name == "reset":
            window.reset()
        elif name == "switch_mode":
            window._toggle_mode()
        elif name == "toggle_clickthrough":
            window._toggle_clickthrough()
        elif name == "toggle_focus":
            window._toggle_focus()
        elif name == "next_module":
            window.switch_next_module()

    hotkey_mgr.hotkey_triggered.connect(on_hotkey)

    # 系统托盘
    tray = QSystemTrayIcon(window)
    tray.setToolTip("公考计时器")

    tray_menu = QMenu()
    show_action = QAction("显示/隐藏", tray_menu)
    show_action.triggered.connect(lambda: window.show() if window.isHidden() else window.hide())
    tray_menu.addAction(show_action)
    tray_menu.addSeparator()
    quit_action = QAction("退出", tray_menu)
    quit_action.triggered.connect(window._quit_app)
    tray_menu.addAction(quit_action)
    tray.setContextMenu(tray_menu)

    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if window.isHidden():
                window.show()
            else:
                window.hide()

    tray.activated.connect(on_tray_activated)
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
