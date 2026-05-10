"""快捷键管理器：优先使用 Windows 全局热键，ctypes 不可用时回退到 QShortcut"""
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt


VK_CODES = {
    "Space": 0x20, "Return": 0x0D, "Tab": 0x09, "Escape": 0x1B,
    "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28,
}
for i in range(26):
    VK_CODES[chr(ord("A") + i)] = 0x41 + i
for i in range(10):
    VK_CODES[str(i)] = 0x30 + i
for i in range(1, 13):
    VK_CODES[f"F{i}"] = 0x6F + i

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008


def _hotkey_str_to_qkeysequence(key_str: str) -> QKeySequence:
    """将 Ctrl+Shift+R 这样的字符串转为 QKeySequence"""
    return QKeySequence(key_str.strip())


class HotkeyManager(QObject):
    hotkey_triggered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shortcuts: list[QShortcut] = []
        self._global_hotkeys: dict[int, str] = {}
        self._next_id = 1
        self._use_global = False
        # 尝试加载 ctypes 以使用全局热键
        try:
            import ctypes
            from ctypes import wintypes
            self._ctypes = ctypes
            self._wintypes = wintypes
            self._use_global = True
        except ImportError:
            self._ctypes = None
            self._wintypes = None

    def register_hotkey(self, name: str, key_str: str, window=None) -> bool:
        # 先尝试全局热键
        if self._use_global and self._ctypes:
            try:
                parts = key_str.strip().split("+")
                mod = 0
                vk = 0
                for part in parts:
                    part = part.strip()
                    if part == "Ctrl":
                        mod |= MOD_CONTROL
                    elif part == "Shift":
                        mod |= MOD_SHIFT
                    elif part == "Alt":
                        mod |= MOD_ALT
                    elif part == "Win":
                        mod |= MOD_WIN
                    else:
                        vk = VK_CODES.get(part)
                        if vk is None and len(part) == 1:
                            vk = ord(part.upper())
                        if vk is None:
                            return False
                hotkey_id = self._next_id
                result = self._ctypes.windll.user32.RegisterHotKey(
                    self._wintypes.HWND(0), hotkey_id, mod, vk
                )
                if result:
                    self._global_hotkeys[hotkey_id] = name
                    self._next_id += 1
                    return True
            except Exception:
                pass

        # 回退到应用内快捷键
        if window:
            qkey = _hotkey_str_to_qkeysequence(key_str)
            shortcut = QShortcut(qkey, window)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(lambda n=name: self.hotkey_triggered.emit(n))
            self._shortcuts.append(shortcut)
            return True
        return False

    def unregister_all(self):
        if self._use_global and self._ctypes and self._global_hotkeys:
            for hotkey_id in list(self._global_hotkeys.keys()):
                try:
                    self._ctypes.windll.user32.UnregisterHotKey(
                        self._wintypes.HWND(0), hotkey_id
                    )
                except Exception:
                    pass
            self._global_hotkeys.clear()

        for s in self._shortcuts:
            s.setEnabled(False)
        self._shortcuts.clear()

    def handle_native_event(self, msg) -> bool:
        if not self._use_global:
            return False
        WM_HOTKEY = 0x0312
        if msg.message == WM_HOTKEY:
            hotkey_id = msg.wParam
            name = self._global_hotkeys.get(hotkey_id)
            if name:
                self.hotkey_triggered.emit(name)
                return True
        return False
