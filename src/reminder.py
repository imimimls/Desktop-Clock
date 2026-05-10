"""提醒系统：倒计时阈值提醒 + 结束提醒"""
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox


class Reminder(QObject):
    reminder_triggered = Signal(int)  # 剩余秒数

    THRESHOLDS = [300, 180, 60]  # 5分钟、3分钟、1分钟（秒）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = True
        self._sound_enabled = False
        self._flash_enabled = True
        self._fired_thresholds = set()

    @property
    def enabled(self): return self._enabled

    @enabled.setter
    def enabled(self, value: bool): self._enabled = value

    @property
    def sound_enabled(self): return self._sound_enabled

    @sound_enabled.setter
    def sound_enabled(self, value: bool): self._sound_enabled = value

    @property
    def flash_enabled(self): return self._flash_enabled

    @flash_enabled.setter
    def flash_enabled(self, value: bool): self._flash_enabled = value

    def reset(self):
        self._fired_thresholds.clear()

    def check(self, remaining_sec: int, elapsed_sec: int = 0):
        if not self._enabled:
            return
        for threshold in self.THRESHOLDS:
            if remaining_sec == threshold and threshold not in self._fired_thresholds:
                self._fired_thresholds.add(threshold)
                self.reminder_triggered.emit(threshold)
                return

    def show_timeout_dialog(self, parent=None):
        msg = QMessageBox(parent)
        msg.setWindowTitle("计时结束")
        msg.setText("本模块计时已结束！")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        if self._sound_enabled:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except ImportError:
                pass
