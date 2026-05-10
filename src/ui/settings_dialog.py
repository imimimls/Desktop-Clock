"""设置面板：热键、模块配置、外观、提醒"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QPushButton, QFormLayout,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtGui import QKeySequence


class SettingsDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data = data_manager
        self._config = data_manager.load_config()
        self.setWindowTitle("设置")
        self.setMinimumSize(480, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._create_hotkey_tab(), "快捷键")
        tabs.addTab(self._create_module_tab(), "模块配置")
        tabs.addTab(self._create_appearance_tab(), "外观")
        tabs.addTab(self._create_reminder_tab(), "提醒")
        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _create_hotkey_tab(self):
        w = QWidget()
        layout = QFormLayout(w)
        self._hk_editors = {}
        hotkeys = self._config.get("hotkeys", {})
        labels = {
            "start_pause": "开始/暂停",
            "reset": "重置",
            "switch_mode": "切换模式",
            "toggle_clickthrough": "穿透模式",
            "toggle_focus": "专注模式",
        }
        for key, label_text in labels.items():
            editor = QLineEdit()
            editor.setText(hotkeys.get(key, ""))
            editor.setPlaceholderText("点击后按键捕获")
            # 双击进入捕获
            editor.mouseDoubleClickEvent = lambda e, ed=editor: self._capture_hotkey(ed)
            self._hk_editors[key] = editor
            layout.addRow(label_text, editor)

        note = QLabel("空格键固定为「结束模块+切下一模块」，不可更改")
        note.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow(note)
        return w

    def _capture_hotkey(self, editor: QLineEdit):
        dlg = HotkeyCaptureDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            editor.setText(dlg.hotkey_string)

    def _create_module_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        shenlun_layout = QHBoxLayout()
        shenlun_layout.addWidget(QLabel("申论整卷时长（分钟）："))
        self._shenlun_spin = QSpinBox()
        self._shenlun_spin.setRange(60, 300)
        self._shenlun_spin.setValue(self._config.get("shenlun_duration", 150))
        shenlun_layout.addWidget(self._shenlun_spin)
        shenlun_layout.addStretch()
        layout.addLayout(shenlun_layout)

        layout.addWidget(QLabel("行测模块配置（双击编辑）："))
        self._module_list = QListWidget()
        modules = self._config.get("xingce_modules", [])
        for mod in modules:
            item = QListWidgetItem(f"{mod['name']}  —  {mod['duration_min']} 分钟")
            item.setData(Qt.ItemDataRole.UserRole, mod)
            self._module_list.addItem(item)
        self._module_list.itemDoubleClicked.connect(self._edit_module)
        layout.addWidget(self._module_list)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加模块")
        add_btn.clicked.connect(self._add_module)
        btn_layout.addWidget(add_btn)
        edit_btn = QPushButton("编辑选中")
        edit_btn.clicked.connect(lambda: self._edit_module(self._module_list.currentItem()))
        btn_layout.addWidget(edit_btn)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._delete_module)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        return w

    def _add_module(self):
        dlg = ModuleEditDialog("新模块", 10, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QListWidgetItem(f"{dlg.name}  —  {dlg.duration} 分钟")
            item.setData(Qt.ItemDataRole.UserRole, {"name": dlg.name, "duration_min": dlg.duration})
            self._module_list.addItem(item)

    def _edit_module(self, item):
        if not item:
            return
        mod = item.data(Qt.ItemDataRole.UserRole)
        dlg = ModuleEditDialog(mod["name"], mod["duration_min"], self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item.setText(f"{dlg.name}  —  {dlg.duration} 分钟")
            item.setData(Qt.ItemDataRole.UserRole, {"name": dlg.name, "duration_min": dlg.duration})

    def _delete_module(self):
        row = self._module_list.currentRow()
        if row >= 0:
            self._module_list.takeItem(row)

    def _create_appearance_tab(self):
        w = QWidget()
        layout = QFormLayout(w)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["深色", "浅色"])
        appearance = self._config.get("appearance", {})
        current = "深色" if appearance.get("theme") == "dark" else "浅色"
        self._theme_combo.setCurrentText(current)
        layout.addRow("主题：", self._theme_combo)

        self._opacity_spin = QDoubleSpinBox()
        self._opacity_spin.setRange(0.3, 1.0)
        self._opacity_spin.setSingleStep(0.05)
        self._opacity_spin.setValue(appearance.get("opacity", 0.9))
        layout.addRow("窗口透明度：", self._opacity_spin)
        return w

    def _create_reminder_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        reminder = self._config.get("reminder", {})
        self._reminder_cb = QCheckBox("启用提醒（剩余5/3/1分钟）")
        self._reminder_cb.setChecked(reminder.get("enabled", True))
        layout.addWidget(self._reminder_cb)

        self._sound_cb = QCheckBox("计时结束声音提醒")
        self._sound_cb.setChecked(reminder.get("sound", False))
        layout.addWidget(self._sound_cb)

        self._flash_cb = QCheckBox("窗口闪烁提醒")
        self._flash_cb.setChecked(reminder.get("flash", True))
        layout.addWidget(self._flash_cb)

        layout.addStretch()
        return w

    def _save(self):
        config = self._data.load_config()
        for key, editor in self._hk_editors.items():
            config["hotkeys"][key] = editor.text()
        modules = []
        for i in range(self._module_list.count()):
            modules.append(self._module_list.item(i).data(Qt.ItemDataRole.UserRole))
        config["xingce_modules"] = modules
        config["shenlun_duration"] = self._shenlun_spin.value()
        config["appearance"]["theme"] = "dark" if self._theme_combo.currentText() == "深色" else "light"
        config["appearance"]["opacity"] = self._opacity_spin.value()
        config["reminder"]["enabled"] = self._reminder_cb.isChecked()
        config["reminder"]["sound"] = self._sound_cb.isChecked()
        config["reminder"]["flash"] = self._flash_cb.isChecked()
        self._data.save_config(config)
        self.accept()


class ModuleEditDialog(QDialog):
    def __init__(self, name="", duration=10, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑模块")
        layout = QFormLayout(self)
        self._name_edit = QLineEdit(name)
        layout.addRow("模块名称：", self._name_edit)
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 180)
        self._duration_spin.setValue(duration)
        layout.addRow("时长（分钟）：", self._duration_spin)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _validate_and_accept(self):
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "错误", "模块名称不能为空")
            return
        self.accept()

    @property
    def name(self):
        return self._name_edit.text().strip()

    @property
    def duration(self):
        return self._duration_spin.value()


class HotkeyCaptureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("按下快捷键")
        self.hotkey_string = ""
        layout = QVBoxLayout(self)
        self._label = QLabel("请按下组合键...")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(200, 60)
        layout.addWidget(self._label)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def keyPressEvent(self, event):
        mods = event.modifiers()
        key = event.key()
        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if mods & Qt.KeyboardModifier.MetaModifier:
            parts.append("Win")
        skip_keys = {
            Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
            Qt.Key.Key_Meta, Qt.Key.Key_Menu, Qt.Key.Key_unknown
        }
        if key not in skip_keys and key != 0:
            key_str = QKeySequence(key).toString()
            if key_str:
                parts.append(key_str)
        self.hotkey_string = "+".join(parts)
        if self.hotkey_string:
            self.accept()
