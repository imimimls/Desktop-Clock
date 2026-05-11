"""主悬浮窗：紧凑横条布局，置顶/拖拽/缩放/穿透/专注"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import (
    QFont, QColor, QPalette, QAction, QMouseEvent, QKeySequence, QShortcut
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QMenu, QApplication, QSizePolicy, QSlider
)

from ..timer_engine import TimerEngine, TimerState, TimerMode
from ..exam_manager import ExamMode

# ---- 深色/浅色调色板 ----
DARK_BG = "#1e1e2e"
DARK_SURFACE = "#313244"
DARK_TEXT = "#cdd6f4"
DARK_ACCENT = "#89b4fa"
DARK_PROGRESS_BG = "#45475a"
DARK_PROGRESS_FG = "#a6e3a1"
DARK_WARNING = "#f9e2af"
DARK_DANGER = "#f38ba8"

LIGHT_BG = "#eff1f5"
LIGHT_SURFACE = "#ccd0da"
LIGHT_TEXT = "#4c4f69"
LIGHT_ACCENT = "#1e66f5"
LIGHT_PROGRESS_BG = "#bcc0cc"
LIGHT_PROGRESS_FG = "#40a02b"
LIGHT_WARNING = "#df8e1d"
LIGHT_DANGER = "#d20f39"


class MainWindow(QMainWindow):
    def __init__(self, exam_manager, data_manager, reminder, hotkey_manager, anti_screensaver):
        super().__init__()
        self._exam = exam_manager
        self._data = data_manager
        self._reminder = reminder
        self._hotkeys = hotkey_manager
        self._anti_ss = anti_screensaver

        self._theme = "dark"
        self._focus_mode = False
        self._clickthrough = False
        self._mini_timer = None
        self._drag_pos = None

        # 计时引擎
        self._timer = TimerEngine(self)

        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._connect_signals()
        self._setup_context_menu()
        self._sync_initial_state()

    # ============ 窗口设置 ============

    def _setup_window(self):
        self.setWindowTitle("公考计时器")
        self.setMinimumSize(360, 100)
        self.resize(500, 130)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # 初始显示模式标签
        self._mode_label = None
        self._module_label = None
        self._time_label = None
        self._progress_label = None
        self._settings_btn = None

    def _setup_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        self._root_layout = QVBoxLayout(central)
        self._root_layout.setContentsMargins(10, 6, 10, 6)
        self._root_layout.setSpacing(4)

        # 顶部行
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._mode_label = QLabel("行测")
        self._mode_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self._mode_label)

        self._module_label = QLabel("常识判断")
        self._module_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self._module_label)

        top_row.addStretch(1)

        self._time_label = QLabel("120:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self._time_label)

        top_row.addStretch(1)

        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFixedSize(28, 28)
        self._settings_btn.setFlat(True)
        self._settings_btn.clicked.connect(self._show_settings)
        top_row.addWidget(self._settings_btn)

        self._root_layout.addLayout(top_row)

        # 进度条
        self._progress_label = QLabel("")
        self._progress_label.setFixedHeight(5)
        self._progress_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._root_layout.addWidget(self._progress_label)

        # ============================================================
        # DEBUG: 可拖动滑块，手动控制剩余秒数，用于快速测试超时效果
        # 测试完成后注释掉此行到 _on_debug_slider 方法即可隐藏
        # ============================================================
        self._debug_slider = QSlider(Qt.Orientation.Horizontal)
        self._debug_slider.setFixedHeight(12)
        self._debug_slider.setVisible(False)  # 改为 True 即可恢复
        self._debug_slider.valueChanged.connect(self._on_debug_slider)
        self._root_layout.addWidget(self._debug_slider)
        # ============================================================

        # 底部按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._start_btn = QPushButton("开始")
        self._start_btn.setMinimumHeight(28)
        self._start_btn.clicked.connect(self.start_pause)
        btn_row.addWidget(self._start_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.setMinimumHeight(28)
        self._reset_btn.clicked.connect(self.reset)
        btn_row.addWidget(self._reset_btn)

        self._root_layout.addLayout(btn_row)

    # ============ 主题 ============

    def _apply_theme(self):
        if self._theme == "dark":
            bg, text, accent = DARK_BG, DARK_TEXT, DARK_ACCENT
            progress_bg = DARK_PROGRESS_BG
            surface = DARK_SURFACE
        else:
            bg, text, accent = LIGHT_BG, LIGHT_TEXT, LIGHT_ACCENT
            progress_bg = LIGHT_PROGRESS_BG
            surface = LIGHT_SURFACE

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {bg}; border-radius: 10px; }}
            QLabel {{ color: {text}; background: transparent; }}
            QPushButton {{ color: {text}; background: transparent; border: none; border-radius: 4px; }}
            QPushButton:hover {{ background: {progress_bg}; }}
        """)
        # 底部按钮使用填充样式
        btn_style = f"""
            QPushButton {{
                color: {text}; background: {surface}; border: 1px solid {progress_bg};
                border-radius: 4px; padding: 2px 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {accent}; color: {bg}; }}
        """
        self._start_btn.setStyleSheet(btn_style)
        self._reset_btn.setStyleSheet(btn_style)
        self._update_fonts()
        self._update_progress()

    def _update_fonts(self):
        h = self.height()
        time_font_size = max(18, int(h * 0.45))
        label_font_size = max(10, int(h * 0.15))
        self._time_label.setFont(QFont("Consolas", time_font_size, QFont.Weight.Bold))
        body_font = QFont("Microsoft YaHei", label_font_size)
        self._mode_label.setFont(body_font)
        self._module_label.setFont(body_font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_fonts()
        self._update_progress()

    # ============ 进度条 ============

    # ============================================================
    # DEBUG: 滑块拖动 → 手动设置剩余秒数，拖到 0 触发超时弹窗
    # ============================================================
    def _on_debug_slider(self, value: int):
        if not hasattr(self, '_debug_slider'):
            return
        # 更新计时器剩余秒数
        self._timer.set_remaining(value)
        # 手动刷新 UI 时间和进度条
        self._on_tick(value, self._timer.elapsed_sec)
        # 拖到 0 秒 → 触发完整超时收尾逻辑
        if value == 0:
            self._timer.pause()
            self._reminder.show_timeout_dialog(self)
    # ============================================================

    def _update_progress(self):
        total = self._exam.total_duration_sec
        if total <= 0:
            self._progress_label.setStyleSheet("background: transparent;")
            return
        ratio = min(self._timer.elapsed_sec / total, 1.0)
        if self._theme == "dark":
            fg, bg = DARK_PROGRESS_FG, DARK_PROGRESS_BG
        else:
            fg, bg = LIGHT_PROGRESS_FG, LIGHT_PROGRESS_BG
        self._progress_label.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {fg}, stop:{ratio} {fg}, "
            f"stop:{ratio} {bg}, stop:1 {bg});"
            f"border-radius: 2px;"
        )

    # ============ 信号连接 ============

    def _connect_signals(self):
        self._timer.tick.connect(self._on_tick)
        self._timer.state_changed.connect(self._on_state_changed)
        self._timer.timeout.connect(self._on_timeout)
        self._reminder.reminder_triggered.connect(self._on_reminder)
        self._exam.module_changed.connect(self._on_module_changed)
        self._exam.all_modules_done.connect(self._on_all_modules_done)

    def _sync_initial_state(self):
        """从 exam_manager 同步初始显示状态，避免硬编码默认值"""
        self._mode_label.setText("行测" if self._exam.mode == ExamMode.XINGCE else "申论")
        self._module_label.setText(self._exam.current_module_name)
        total = self._exam.total_duration_sec
        m = total // 60
        self._time_label.setText(f"{m:02d}:00")
        self._update_debug_slider_range()

    # ============================================================
    # DEBUG: 根据当前计时模式更新滑块范围
    # ============================================================
    def _update_debug_slider_range(self):
        if not hasattr(self, '_debug_slider'):
            return
        total = self._exam.total_duration_sec
        self._debug_slider.blockSignals(True)
        self._debug_slider.setRange(0, total)
        if self._timer.state == TimerState.IDLE:
            self._debug_slider.setValue(total)
        else:
            self._debug_slider.setValue(self._timer.remaining_sec)
        self._debug_slider.blockSignals(False)
    # ============================================================

    def _on_tick(self, remaining_sec, elapsed_sec):
        if self._timer.mode == TimerMode.COUNTDOWN:
            m, s = divmod(remaining_sec, 60)
        else:
            m, s = divmod(elapsed_sec, 60)
        self._time_label.setText(f"{m:02d}:{s:02d}")
        self._reminder.check(remaining_sec, elapsed_sec)
        self._update_progress()
        # DEBUG: 同步滑块位置（无信号避免循环）
        if hasattr(self, '_debug_slider') and self._debug_slider.isVisible():
            self._debug_slider.blockSignals(True)
            self._debug_slider.setValue(remaining_sec)
            self._debug_slider.blockSignals(False)
        # 剩余不足5分钟变色
        if self._theme == "dark":
            danger = DARK_DANGER
            warning = DARK_WARNING
        else:
            danger = LIGHT_DANGER
            warning = LIGHT_WARNING
        if remaining_sec <= 60 and self._timer.mode == TimerMode.COUNTDOWN:
            self._time_label.setStyleSheet(f"color: {danger}; background: transparent;")
        elif remaining_sec <= 300 and self._timer.mode == TimerMode.COUNTDOWN:
            self._time_label.setStyleSheet(f"color: {warning}; background: transparent;")
        else:
            text_color = DARK_TEXT if self._theme == "dark" else LIGHT_TEXT
            self._time_label.setStyleSheet(f"color: {text_color}; background: transparent;")

    def _on_state_changed(self, state):
        if state == TimerState.RUNNING:
            self._anti_ss.enable()
            self._start_btn.setText("暂停")
        elif state == TimerState.PAUSED:
            self._anti_ss.disable()
            self._start_btn.setText("继续")
        else:
            self._anti_ss.disable()
            self._start_btn.setText("开始")

    def _on_timeout(self):
        self._reminder.show_timeout_dialog(self)

    def _on_reminder(self, remaining_sec):
        if self._reminder.flash_enabled:
            self._flash_window()

    def _on_module_changed(self, name, duration_sec):
        self._module_label.setText(name)

    def _on_all_modules_done(self):
        self._timer.pause()
        self._save_record()
        QTimer.singleShot(200, lambda: self._reminder.show_timeout_dialog(self))

    def _flash_window(self):
        # 简单的透明度闪烁
        original = self.windowOpacity()
        for i in range(3):
            self.setWindowOpacity(0.5)
            QApplication.processEvents()
            QTimer.singleShot(150, lambda: None)
            self.setWindowOpacity(original)
            QApplication.processEvents()

    # ============ 计时控制 ============

    def start_pause(self):
        if self._timer.state == TimerState.IDLE:
            total = self._exam.total_duration_sec
            self._timer.set_countdown(total)
            self._timer.start()
            self._exam.start_module(0)
            self._reminder.reset()
        elif self._timer.state == TimerState.RUNNING:
            self._timer.pause()
        elif self._timer.state == TimerState.PAUSED:
            self._timer.resume()

    def reset(self):
        self._timer.reset()
        self._exam.reset_modules()
        self._reminder.reset()
        total = self._exam.total_duration_sec
        m = total // 60
        self._time_label.setText(f"{m:02d}:00")
        self._update_progress()
        text_color = DARK_TEXT if self._theme == "dark" else LIGHT_TEXT
        self._time_label.setStyleSheet(f"color: {text_color}; background: transparent;")
        self._update_debug_slider_range()

    def switch_next_module(self):
        """空格键触发：结束当前模块 + 下一模块"""
        if self._timer.state != TimerState.RUNNING:
            return
        record = self._exam.switch_next_module(self._timer.elapsed_sec)
        if self._exam.is_all_modules_done:
            return
        duration = self._exam.current_module_duration_sec
        self._exam.start_module(self._timer.elapsed_sec)
        self._module_label.setText(self._exam.current_module_name)

    def _save_record(self):
        from datetime import datetime
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mode": "行测" if self._exam.mode == ExamMode.XINGCE else "申论",
            "total_elapsed_sec": self._timer.elapsed_sec,
            "modules": self._exam.records,
        }
        if self._mini_timer:
            qi = self._mini_timer.elapsed_seconds()
            if qi > 0:
                record.setdefault("questions", []).append({"label": "单题", "elapsed_sec": int(qi)})
        self._data.add_record(record)

    # ============ 模式切换 ============

    def _toggle_mode(self):
        config = self._data.load_config()
        if self._exam.mode == ExamMode.XINGCE:
            modules = config.get("shenlun_modules") or [
                {"name": "小题作答", "duration_min": 90},
                {"name": "大作文", "duration_min": 60},
            ]
            duration = sum(m["duration_min"] for m in modules)
            self._exam.set_mode(ExamMode.SHENLUN, modules, duration)
            self._mode_label.setText("申论")
        else:
            modules = config.get("xingce_modules", [])
            duration = sum(m["duration_min"] for m in modules)
            self._exam.set_mode(ExamMode.XINGCE, modules, duration)
            self._mode_label.setText("行测")
        self._module_label.setText(self._exam.current_module_name)
        self.reset()

    # ============ 点击穿透 ============

    def _toggle_clickthrough(self):
        self._clickthrough = not self._clickthrough
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if self._clickthrough:
                ctypes.windll.user32.SetWindowLongW(
                    hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_LAYERED
                )
            else:
                ctypes.windll.user32.SetWindowLongW(
                    hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT
                )
        except Exception:
            # ctypes 不可用，回退到 Qt 方法
            if self._clickthrough:
                self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)
            else:
                self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
            self.show()

    # ============ 专注模式 ============

    def _toggle_focus(self):
        self._focus_mode = not self._focus_mode
        visible = not self._focus_mode
        self._mode_label.setVisible(visible)
        self._module_label.setVisible(visible)
        self._settings_btn.setVisible(visible)
        self._progress_label.setVisible(visible)
        self._start_btn.setVisible(visible)
        self._reset_btn.setVisible(visible)

    # ============ UI 弹窗 ============

    def _show_settings(self):
        from .settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._data, self)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            config = self._data.load_config()
            self._set_theme(config["appearance"]["theme"])
            self.setWindowOpacity(config["appearance"]["opacity"])
            cfg_reminder = config["reminder"]
            self._reminder.enabled = cfg_reminder["enabled"]
            self._reminder.sound_enabled = cfg_reminder["sound"]
            self._reminder.flash_enabled = cfg_reminder["flash"]
            # 重新注册快捷键
            self._hotkeys.unregister_all()
            for name, key_str in config["hotkeys"].items():
                self._hotkeys.register_hotkey(name, key_str, self)
            self._hotkeys.register_hotkey("next_module", "Space", self)

    def _show_history(self):
        from .history_dialog import HistoryDialog
        dlg = HistoryDialog(self._data, self)
        dlg.exec()

    def _export_data(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "刷题记录.xlsx", "Excel (*.xlsx);;CSV (*.csv)"
        )
        if path.endswith(".csv"):
            self._data.export_to_csv(path)
        elif path.endswith(".xlsx"):
            self._data.export_to_excel(path)

    def _show_mini_timer(self):
        from .mini_timer import MiniTimer
        if self._mini_timer is None:
            self._mini_timer = MiniTimer()
            self._mini_timer.closed.connect(lambda: setattr(self, '_mini_timer', None))
        self._mini_timer.show()
        self._mini_timer.reset()

    def _set_theme(self, theme):
        self._theme = theme
        self._apply_theme()

    def _quit_app(self):
        self._hotkeys.unregister_all()
        self._anti_ss.disable()
        QApplication.quit()

    # ============ 右键菜单 ============

    def _setup_context_menu(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("切换行测/申论").triggered.connect(self._toggle_mode)
        menu.addSeparator()

        click_action = menu.addAction("穿透模式")
        click_action.setCheckable(True)
        click_action.setChecked(self._clickthrough)
        click_action.triggered.connect(self._toggle_clickthrough)

        focus_action = menu.addAction("专注模式")
        focus_action.setCheckable(True)
        focus_action.setChecked(self._focus_mode)
        focus_action.triggered.connect(self._toggle_focus)

        menu.addSeparator()
        menu.addAction("单题计时器").triggered.connect(self._show_mini_timer)
        menu.addAction("历史记录").triggered.connect(self._show_history)
        menu.addAction("设置").triggered.connect(self._show_settings)
        menu.addSeparator()

        theme_label = "深色模式" if self._theme != "dark" else "浅色模式"
        menu.addAction(theme_label).triggered.connect(
            lambda: self._set_theme("dark" if self._theme != "dark" else "light")
        )
        menu.addAction("导出数据").triggered.connect(self._export_data)
        menu.addSeparator()
        menu.addAction("退出").triggered.connect(self._quit_app)
        menu.exec(self.mapToGlobal(pos))

    # ============ 窗口拖拽 ============

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and not self._clickthrough:
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ============ 全局热键 ============

    def nativeEvent(self, eventType, message):
        if self._hotkeys.handle_native_event(message):
            return True, 0
        return super().nativeEvent(eventType, message)
