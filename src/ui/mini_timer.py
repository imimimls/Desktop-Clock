"""单题小计时器：独立的微型计时悬浮窗"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QFont


class MiniTimer(QWidget):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("单题计时")
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(160, 40)
        self._elapsed = 0
        self._running = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        self._label = QLabel("00:00")
        self._label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

        self._btn = QPushButton("▶")
        self._btn.setFixedWidth(30)
        self._btn.clicked.connect(self._toggle)
        layout.addWidget(self._btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(20)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _tick(self):
        if self._running:
            self._elapsed += 0.1
            mins = int(self._elapsed) // 60
            secs = int(self._elapsed) % 60
            self._label.setText(f"{mins:02d}:{secs:02d}")

    def _toggle(self):
        self._running = not self._running
        self._btn.setText("⏸" if self._running else "▶")

    def reset(self):
        self._elapsed = 0
        self._running = False
        self._btn.setText("▶")
        self._label.setText("00:00")

    def elapsed_seconds(self) -> float:
        return self._elapsed

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
