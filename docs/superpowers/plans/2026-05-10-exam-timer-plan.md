# 公考刷题计时器 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 Windows 桌面公考计时器，悬浮窗 + 行测/申论模式 + 全局快捷键 + 数据复盘

**Architecture:** PyQt6 悬浮窗 + JSON 本地存储 + Windows API 全局热键/防锁屏，分为数据层、计时引擎、考试管理、UI 四层

**Tech Stack:** Python 3.13, PyQt6, openpyxl, ctypes (Windows API), PyInstaller

---

### Task 1: 项目初始化与依赖安装

**Files:**
- Create: `d:/Desktop Clock/requirements.txt`
- Create: `d:/Desktop Clock/src/__init__.py`

- [ ] **Step 1: 创建项目目录结构**

```bash
mkdir -p "d:/Desktop Clock/src/ui" "d:/Desktop Clock/tests"
```

- [ ] **Step 2: 编写 requirements.txt**

```txt
PyQt6>=6.8.0
openpyxl>=3.1.0
pyinstaller>=6.0.0
```

- [ ] **Step 3: 安装依赖**

```bash
pip install -r "d:/Desktop Clock/requirements.txt"
```

- [ ] **Step 4: 验证安装**

```bash
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
python -c "import openpyxl; print('openpyxl OK')"
```

---

### Task 2: 数据管理器（data_manager.py）

**Files:**
- Create: `d:/Desktop Clock/src/data_manager.py`
- Create: `d:/Desktop Clock/tests/test_data_manager.py`

**接口设计：**
```python
class DataManager:
    def __init__(self, data_dir: str = None)  # 默认 %APPDATA%/ExamTimer
    def load_config(self) -> dict
    def save_config(self, config: dict)
    def load_history(self) -> list[dict]
    def save_history(self, history: list[dict])
    def add_record(self, record: dict)  # 追加一条刷题记录
    def clear_history()
    def export_to_excel(self, path: str)
    def export_to_csv(self, path: str)
```

- [ ] **Step 1: 编写测试 test_data_manager.py**

```python
import json
import tempfile
import os
from src.data_manager import DataManager

def test_init_creates_default_config():
    with tempfile.TemporaryDirectory() as tmp:
        dm = DataManager(data_dir=tmp)
        config = dm.load_config()
        assert config["xingce_modules"][0]["name"] == "常识"
        assert config["xingce_modules"][0]["duration_min"] == 10
        assert config["shenlun_duration"] == 150
        assert os.path.exists(os.path.join(tmp, "config.json"))

def test_save_and_load_config():
    with tempfile.TemporaryDirectory() as tmp:
        dm = DataManager(data_dir=tmp)
        config = dm.load_config()
        config["shenlun_duration"] = 180
        dm.save_config(config)
        dm2 = DataManager(data_dir=tmp)
        assert dm2.load_config()["shenlun_duration"] == 180

def test_add_and_load_history():
    with tempfile.TemporaryDirectory() as tmp:
        dm = DataManager(data_dir=tmp)
        record = {"date": "2026-05-10 14:30", "mode": "行测", "total_elapsed_sec": 7050}
        dm.add_record(record)
        history = dm.load_history()
        assert len(history) == 1
        assert history[0]["mode"] == "行测"

def test_clear_history():
    with tempfile.TemporaryDirectory() as tmp:
        dm = DataManager(data_dir=tmp)
        dm.add_record({"date": "test", "mode": "行测"})
        dm.clear_history()
        assert len(dm.load_history()) == 0

def test_export_to_csv():
    with tempfile.TemporaryDirectory() as tmp:
        dm = DataManager(data_dir=tmp)
        dm.add_record({"date": "2026-05-10 14:30", "mode": "行测",
                        "total_elapsed_sec": 7050, "modules": [
                            {"name": "常识", "planned_min": 10, "actual_sec": 580, "overtime": False}
                        ]})
        csv_path = os.path.join(tmp, "history.csv")
        dm.export_to_csv(csv_path)
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            assert "行测" in content
            assert "常识" in content

def test_export_to_excel():
    with tempfile.TemporaryDirectory() as tmp:
        dm = DataManager(data_dir=tmp)
        dm.add_record({"date": "2026-05-10 14:30", "mode": "申论",
                        "total_elapsed_sec": 9000, "modules": []})
        xlsx_path = os.path.join(tmp, "history.xlsx")
        dm.export_to_excel(xlsx_path)
        assert os.path.exists(xlsx_path)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd "d:/Desktop Clock" && python -m pytest tests/test_data_manager.py -v
```
预期：全部 FAIL（模块未实现）

- [ ] **Step 3: 实现 data_manager.py**

```python
"""数据持久化管理：JSON 配置与历史记录读写"""
import json
import os
import csv
from pathlib import Path

DEFAULT_CONFIG = {
    "hotkeys": {
        "start_pause": "Ctrl+Shift+Space",
        "reset": "Ctrl+Shift+R",
        "switch_mode": "Ctrl+Shift+M",
        "toggle_clickthrough": "Ctrl+Shift+T",
        "toggle_focus": "Ctrl+Shift+F",
    },
    "appearance": {"theme": "dark", "opacity": 0.9},
    "reminder": {"enabled": True, "sound": False, "flash": True},
    "xingce_modules": [
        {"name": "常识判断", "duration_min": 10},
        {"name": "言语理解", "duration_min": 35},
        {"name": "数量关系", "duration_min": 15},
        {"name": "判断推理", "duration_min": 35},
        {"name": "资料分析", "duration_min": 25},
    ],
    "shenlun_duration": 150,
}

def _default_data_dir():
    return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ExamTimer")

class DataManager:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or _default_data_dir()
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.config_path):
            self.save_config(DEFAULT_CONFIG)

    @property
    def config_path(self):
        return os.path.join(self.data_dir, "config.json")

    @property
    def history_path(self):
        return os.path.join(self.data_dir, "history.json")

    def load_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, config: dict):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def load_history(self) -> list[dict]:
        if not os.path.exists(self.history_path):
            return []
        with open(self.history_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_history(self, history: list[dict]):
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def add_record(self, record: dict):
        history = self.load_history()
        history.append(record)
        self.save_history(history)

    def clear_history(self):
        self.save_history([])

    def export_to_csv(self, path: str):
        history = self.load_history()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["日期", "模式", "整卷用时(秒)", "模块", "计划时长(分)", "实际用时(秒)", "超时"])
            for record in history:
                total_sec = record.get("total_elapsed_sec", 0)
                for mod in record.get("modules", []) or []:
                    writer.writerow([
                        record["date"], record["mode"], total_sec,
                        mod.get("name", ""), mod.get("planned_min", 0),
                        mod.get("actual_sec", 0),
                        "是" if mod.get("overtime") else "否"
                    ])
                if not record.get("modules"):
                    writer.writerow([record["date"], record["mode"], total_sec, "", "", "", ""])

    def export_to_excel(self, path: str):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "刷题记录"
        ws.append(["日期", "模式", "整卷用时(秒)", "模块", "计划时长(分)", "实际用时(秒)", "超时"])
        for record in self.load_history():
            total_sec = record.get("total_elapsed_sec", 0)
            for mod in (record.get("modules") or []):
                ws.append([
                    record["date"], record["mode"], total_sec,
                    mod.get("name", ""), mod.get("planned_min", 0),
                    mod.get("actual_sec", 0),
                    "是" if mod.get("overtime") else "否"
                ])
            if not record.get("modules"):
                ws.append([record["date"], record["mode"], total_sec, "", "", "", ""])
        wb.save(path)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd "d:/Desktop Clock" && python -m pytest tests/test_data_manager.py -v
```
预期：全部 PASS

---

### Task 3: 计时引擎（timer_engine.py）

**Files:**
- Create: `d:/Desktop Clock/src/timer_engine.py`
- Create: `d:/Desktop Clock/tests/test_timer_engine.py`

- [ ] **Step 1: 编写测试**

```python
import time
from src.timer_engine import TimerEngine, TimerState, TimerMode

def test_initial_state():
    t = TimerEngine()
    assert t.state == TimerState.IDLE
    assert t.mode == TimerMode.COUNTDOWN
    assert t.remaining_sec == 0
    assert t.elapsed_sec == 0

def test_start_countdown():
    t = TimerEngine()
    t.set_countdown(60)  # 1分钟倒计时
    t.start()
    assert t.state == TimerState.RUNNING
    assert t.remaining_sec == 60

def test_pause_resume():
    t = TimerEngine()
    t.set_countdown(60)
    t.start()
    t.pause()
    assert t.state == TimerState.PAUSED
    t.resume()
    assert t.state == TimerState.RUNNING

def test_reset():
    t = TimerEngine()
    t.set_countdown(60)
    t.start()
    t.reset()
    assert t.state == TimerState.IDLE
    assert t.elapsed_sec == 0

def test_countup_mode():
    t = TimerEngine()
    t.set_countup()
    t.start()
    assert t.mode == TimerMode.COUNTUP
    assert t.elapsed_sec == 0

def test_countdown_finish():
    t = TimerEngine()
    t.set_countdown(1)
    t.start()
    # 模拟秒数走完
    t._remaining_sec = 0
    t._tick()
    if t.remaining_sec <= 0 and t.mode == TimerMode.COUNTDOWN:
        assert t.state == TimerState.FINISHED

def test_tick_signal():
    signals_received = []
    t = TimerEngine()
    t.tick.connect(lambda r, e: signals_received.append((r, e)))
    t.set_countdown(60)
    t.start()
    t._tick()
    assert len(signals_received) == 1
    assert signals_received[0][0] == 59  # remaining decreased
    assert signals_received[0][1] == 1   # elapsed increased
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd "d:/Desktop Clock" && python -m pytest tests/test_timer_engine.py -v
```

- [ ] **Step 3: 实现 timer_engine.py**

```python
"""计时引擎：倒计时/正计时状态机"""
from enum import Enum, auto
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class TimerState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()


class TimerMode(Enum):
    COUNTDOWN = auto()
    COUNTUP = auto()


class TimerEngine(QObject):
    tick = pyqtSignal(int, int)       # remaining_sec, elapsed_sec
    timeout = pyqtSignal()
    state_changed = pyqtSignal(TimerState)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = TimerState.IDLE
        self._mode = TimerMode.COUNTDOWN
        self._remaining_sec = 0
        self._elapsed_sec = 0
        self._total_sec = 0
        self._qtimer = QTimer(self)
        self._qtimer.timeout.connect(self._tick)

    @property
    def state(self):
        return self._state

    @property
    def mode(self):
        return self._mode

    @property
    def remaining_sec(self):
        return self._remaining_sec

    @property
    def elapsed_sec(self):
        return self._elapsed_sec

    @property
    def total_sec(self):
        return self._total_sec

    def set_countdown(self, total_seconds: int):
        self._mode = TimerMode.COUNTDOWN
        self._total_sec = total_seconds
        self._remaining_sec = total_seconds
        self._elapsed_sec = 0
        self._set_state(TimerState.IDLE)

    def set_countup(self):
        self._mode = TimerMode.COUNTUP
        self._total_sec = 0
        self._remaining_sec = 0
        self._elapsed_sec = 0
        self._set_state(TimerState.IDLE)

    def start(self):
        if self._state == TimerState.IDLE:
            self._qtimer.start(1000)
            self._set_state(TimerState.RUNNING)

    def pause(self):
        if self._state == TimerState.RUNNING:
            self._qtimer.stop()
            self._set_state(TimerState.PAUSED)

    def resume(self):
        if self._state == TimerState.PAUSED:
            self._qtimer.start(1000)
            self._set_state(TimerState.RUNNING)

    def reset(self):
        self._qtimer.stop()
        if self._mode == TimerMode.COUNTDOWN:
            self._remaining_sec = self._total_sec
        else:
            self._remaining_sec = 0
        self._elapsed_sec = 0
        self._set_state(TimerState.IDLE)

    def _tick(self):
        self._elapsed_sec += 1
        if self._mode == TimerMode.COUNTDOWN:
            self._remaining_sec -= 1
            if self._remaining_sec <= 0:
                self._remaining_sec = 0
                self._qtimer.stop()
                self._set_state(TimerState.FINISHED)
                self.timeout.emit()
        self.tick.emit(self._remaining_sec, self._elapsed_sec)

    def _set_state(self, state: TimerState):
        if self._state != state:
            self._state = state
            self.state_changed.emit(state)

    def set_remaining(self, seconds: int):
        """直接设置剩余秒数，用于模块切换时调整"""
        self._remaining_sec = max(0, seconds)
        self.tick.emit(self._remaining_sec, self._elapsed_sec)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd "d:/Desktop Clock" && python -m pytest tests/test_timer_engine.py -v
```

---

### Task 4: 考试管理器（exam_manager.py）

**Files:**
- Create: `d:/Desktop Clock/src/exam_manager.py`
- Create: `d:/Desktop Clock/tests/test_exam_manager.py`

- [ ] **Step 1: 编写测试**

```python
from src.exam_manager import ExamManager, ExamMode

def test_init_xingce_mode():
    modules = [
        {"name": "常识", "duration_min": 10},
        {"name": "言语", "duration_min": 35},
        {"name": "数量", "duration_min": 15},
        {"name": "判断", "duration_min": 35},
        {"name": "资料", "duration_min": 25},
    ]
    mgr = ExamManager()
    mgr.set_mode(ExamMode.XINGCE, modules)
    assert mgr.current_module_index == 0
    assert mgr.current_module_name == "常识"
    assert mgr.current_module_duration_sec == 600

def test_switch_next_module():
    modules = [
        {"name": "A", "duration_min": 5},
        {"name": "B", "duration_min": 10},
    ]
    mgr = ExamManager()
    mgr.set_mode(ExamMode.XINGCE, modules)
    result = mgr.switch_next_module()
    assert result["prev_module"] == "A"
    assert mgr.current_module_index == 1
    assert mgr.current_module_name == "B"

def test_switch_last_module_finishes():
    modules = [{"name": "Only", "duration_min": 5}]
    mgr = ExamManager()
    mgr.set_mode(ExamMode.XINGCE, modules)
    result = mgr.switch_next_module()
    assert result["prev_module"] == "Only"
    assert mgr.is_all_modules_done

def test_shenlun_mode():
    mgr = ExamManager()
    mgr.set_mode(ExamMode.SHENLUN, total_duration_min=150)
    assert mgr.mode == ExamMode.SHENLUN
    assert mgr.total_duration_sec == 9000

def test_module_record():
    modules = [{"name": "测试模块", "duration_min": 5}]
    mgr = ExamManager()
    mgr.set_mode(ExamMode.XINGCE, modules)
    mgr.start_module()  # 开始计时
    mgr._current_module_elapsed = 320  # 模拟经过了320秒
    record = mgr.switch_next_module()
    assert record["actual_sec"] == 320
    assert record["overtime"] == True  # 320 > 300
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd "d:/Desktop Clock" && python -m pytest tests/test_exam_manager.py -v
```

- [ ] **Step 3: 实现 exam_manager.py**

```python
"""考试模式管理：行测/申论模式、模块切换、用时记录"""
from enum import Enum, auto
from PyQt6.QtCore import QObject, pyqtSignal
from .timer_engine import TimerEngine, TimerMode


class ExamMode(Enum):
    XINGCE = auto()
    SHENLUN = auto()


class ExamManager(QObject):
    module_switched = pyqtSignal(dict)   # 模块切换信号，携带上一模块记录
    all_modules_done = pyqtSignal()
    module_changed = pyqtSignal(str, int)  # 模块名, 时长(秒)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = ExamMode.XINGCE
        self._modules = []
        self._current_index = 0
        self._total_duration_sec = 7200  # 默认120分钟
        self._records = []  # 各模块用时记录
        self._module_start_elapsed = 0  # 模块开始时整卷已用时间

    @property
    def mode(self):
        return self._mode

    @property
    def current_module_index(self):
        return self._current_index

    @property
    def current_module_name(self):
        if not self._modules or self._current_index >= len(self._modules):
            return ""
        return self._modules[self._current_index]["name"]

    @property
    def current_module_duration_sec(self):
        if not self._modules or self._current_index >= len(self._modules):
            return 0
        return self._modules[self._current_index]["duration_min"] * 60

    @property
    def total_duration_sec(self):
        return self._total_duration_sec

    @property
    def is_all_modules_done(self):
        return self._current_index >= len(self._modules)

    @property
    def module_count(self):
        return len(self._modules)

    @property
    def records(self):
        return list(self._records)

    def set_mode(self, mode: ExamMode, modules=None, total_duration_min=None):
        self._mode = mode
        if modules:
            self._modules = list(modules)
        elif mode == ExamMode.XINGCE:
            # 使用默认行测模块
            self._modules = []
        if total_duration_min:
            self._total_duration_sec = total_duration_min * 60
        elif mode == ExamMode.XINGCE:
            self._total_duration_sec = 7200  # 120分钟
        self._current_index = 0
        self._records = []
        if self._modules:
            self.module_changed.emit(self.current_module_name, self.current_module_duration_sec)

    def start_module(self, total_elapsed_sec: int = 0):
        """记录模块开始时的整卷用时"""
        self._module_start_elapsed = total_elapsed_sec

    def switch_next_module(self, current_elapsed_sec: int = 0) -> dict:
        """切换到下一模块，返回上一模块的记录"""
        if self.is_all_modules_done:
            return {}
        prev_name = self.current_module_name
        planned_sec = self.current_module_duration_sec
        actual_sec = current_elapsed_sec - self._module_start_elapsed
        record = {
            "name": prev_name,
            "planned_min": planned_sec // 60,
            "actual_sec": actual_sec,
            "overtime": actual_sec > planned_sec if planned_sec > 0 else False,
        }
        self._records.append(record)
        self._current_index += 1
        if self.is_all_modules_done:
            self.all_modules_done.emit()
        else:
            self.module_changed.emit(self.current_module_name, self.current_module_duration_sec)
        self.module_switched.emit(record)
        return record

    def reset_modules(self):
        """重置模块进度"""
        self._current_index = 0
        self._records = []
        if self._modules:
            self.module_changed.emit(self.current_module_name, self.current_module_duration_sec)

    def set_modules(self, modules: list[dict]):
        """动态设置模块列表（用于自定义配置）"""
        self._modules = list(modules)
        self.reset_modules()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd "d:/Desktop Clock" && python -m pytest tests/test_exam_manager.py -v
```

---

### Task 5: 防锁屏模块（anti_screensaver.py）

**Files:**
- Create: `d:/Desktop Clock/src/anti_screensaver.py`

- [ ] **Step 1: 实现 anti_screensaver.py**

```python
"""防屏幕锁屏：计时期间阻止系统自动锁屏/休眠"""
import ctypes


ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class AntiScreensaver:
    def __init__(self):
        self._active = False

    def enable(self):
        """阻止锁屏/休眠"""
        if not self._active:
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            self._active = True

    def disable(self):
        """恢复正常"""
        if self._active:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            self._active = False

    @property
    def is_active(self):
        return self._active
```

- [ ] **Step 2: 手动验证**

```bash
cd "d:/Desktop Clock" && python -c "from src.anti_screensaver import AntiScreensaver; a = AntiScreensaver(); a.enable(); print('防锁屏已开启，检查电源设置中显示器不会自动关闭'); import time; time.sleep(3); a.disable(); print('已关闭')"
```

---

### Task 6: 提醒模块（reminder.py）

**Files:**
- Create: `d:/Desktop Clock/src/reminder.py`

- [ ] **Step 1: 实现 reminder.py**

```python
"""提醒系统：倒计时阈值提醒 + 结束提醒"""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox


class Reminder(QObject):
    reminder_triggered = pyqtSignal(int)  # 剩余分钟数

    THRESHOLDS = [300, 180, 60]  # 5分钟、3分钟、1分钟（秒）
    _fired_thresholds: set[int]  # 已触发的阈值，避免重复

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = True
        self._sound_enabled = False
        self._flash_enabled = True
        self._fired_thresholds = set()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def sound_enabled(self):
        return self._sound_enabled

    @sound_enabled.setter
    def sound_enabled(self, value: bool):
        self._sound_enabled = value

    @property
    def flash_enabled(self):
        return self._flash_enabled

    @flash_enabled.setter
    def flash_enabled(self, value: bool):
        self._flash_enabled = value

    def reset(self):
        """重置已触发阈值，每次新计时开始时调用"""
        self._fired_thresholds.clear()

    def check(self, remaining_sec: int, elapsed_sec: int = 0):
        """每秒调用，检查是否触发提醒阈值"""
        if not self._enabled:
            return
        for threshold in self.THRESHOLDS:
            if remaining_sec == threshold and threshold not in self._fired_thresholds:
                self._fired_thresholds.add(threshold)
                self.reminder_triggered.emit(threshold)
                return

    def show_timeout_dialog(self, parent=None):
        """计时结束弹窗"""
        msg = QMessageBox(parent)
        msg.setWindowTitle("计时结束")
        msg.setText("本模块计时已结束！")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        # 播放系统提示音（可选）
        if self._sound_enabled:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except ImportError:
                pass
```

---

### Task 7: 快捷键管理器（hotkey_manager.py）

**Files:**
- Create: `d:/Desktop Clock/src/hotkey_manager.py`

- [ ] **Step 1: 实现 hotkey_manager.py**

```python
"""全局快捷键管理：Windows RegisterHotKey + WM_HOTKEY"""
import ctypes
from ctypes import wintypes
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QKeySequence


# Windows API 常量
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

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


def parse_hotkey(hotkey_str: str) -> tuple[int, int]:
    """解析快捷键字符串为 (modifiers, vk_code)"""
    parts = hotkey_str.strip().split("+")
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
            # 普通键
            vk = VK_CODES.get(part)
            if vk is None and len(part) == 1:
                vk = ord(part.upper())
            if vk is None:
                raise ValueError(f"未知按键: {part}")
    return mod, vk


class HotkeyManager(QObject):
    hotkey_triggered = pyqtSignal(str)  # 快捷键名称

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hotkeys: dict[int, str] = {}  # hotkey_id → name
        self._next_id = 1

    def register_hotkey(self, name: str, key_str: str) -> bool:
        try:
            mod, vk = parse_hotkey(key_str)
        except ValueError:
            return False
        hotkey_id = self._next_id
        result = ctypes.windll.user32.RegisterHotKey(
            wintypes.HWND(0), hotkey_id, mod, vk
        )
        if result:
            self._hotkeys[hotkey_id] = name
            self._next_id += 1
            return True
        return False

    def unregister_all(self):
        for hotkey_id in list(self._hotkeys.keys()):
            ctypes.windll.user32.UnregisterHotKey(wintypes.HWND(0), hotkey_id)
        self._hotkeys.clear()

    def handle_native_event(self, msg) -> bool:
        """在 QMainWindow.nativeEvent 中调用此方法"""
        WM_HOTKEY = 0x0312
        if msg.message == WM_HOTKEY:
            hotkey_id = msg.wParam
            name = self._hotkeys.get(hotkey_id)
            if name:
                self.hotkey_triggered.emit(name)
                return True
        return False
```

---

### Task 8: 导出模块（exporter.py）

已在 data_manager.py 的 `export_to_excel` 和 `export_to_csv` 方法中实现，无需独立文件。

---

### Task 9: 单题小计时器 UI（ui/mini_timer.py）

**Files:**
- Create: `d:/Desktop Clock/src/ui/__init__.py`
- Create: `d:/Desktop Clock/src/ui/mini_timer.py`

- [ ] **Step 1: 实现 mini_timer.py**

```python
"""单题小计时器：独立的微型计时窗口"""
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont


class MiniTimer(QWidget):
    closed = pyqtSignal()

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
```

---

### Task 10: 主悬浮窗 UI（ui/main_window.py）

**Files:**
- Create: `d:/Desktop Clock/src/ui/main_window.py`

这是最核心的 UI 组件。先实现基础框架，后续迭代功能。

- [ ] **Step 1: 实现 main_window.py（基础框架 + 布局 + 自适应缩放）**

```python
"""主悬浮窗：紧凑横条布局，置顶/拖拽/缩放/穿透"""
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QAction, QMouseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QMenu, QApplication, QSizePolicy
)


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

        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._connect_signals()
        self._setup_context_menu()

    def _setup_window(self):
        self.setWindowTitle("公考计时器")
        self.setMinimumSize(280, 60)
        self.resize(420, 80)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        # 启用拖拽移动
        self._drag_pos = None

    def _setup_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        self._root_layout = QVBoxLayout(central)
        self._root_layout.setContentsMargins(8, 4, 8, 4)
        self._root_layout.setSpacing(2)

        # --- 顶部行：模式 + 模块 + 时间 + 进度 ---
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

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

        # --- 底部行：进度条 ---
        self._progress_label = QLabel("")
        self._progress_label.setFixedHeight(4)
        self._progress_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._root_layout.addWidget(self._progress_label)

        # 初始进度条样式通过 setStyleSheet 设置

    def _apply_theme(self):
        if self._theme == "dark":
            bg, text, accent = DARK_BG, DARK_TEXT, DARK_ACCENT
            progress_bg, progress_fg = DARK_PROGRESS_BG, DARK_PROGRESS_FG
        else:
            bg, text, accent = LIGHT_BG, LIGHT_TEXT, LIGHT_ACCENT
            progress_bg, progress_fg = LIGHT_PROGRESS_BG, LIGHT_PROGRESS_FG

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {bg}; border-radius: 8px; }}
            QLabel {{ color: {text}; background: transparent; }}
            QPushButton {{ color: {text}; background: transparent; border: none; border-radius: 4px; }}
            QPushButton:hover {{ background: {progress_bg}; }}
        """)
        # 更新字体大小
        self._update_fonts()

    def _update_fonts(self):
        """根据窗口高度动态计算字体大小"""
        h = self.height()
        time_font_size = max(18, int(h * 0.5))
        label_font_size = max(10, int(h * 0.16))
        self._time_label.setFont(QFont("Consolas", time_font_size, QFont.Weight.Bold))
        self._mode_label.setFont(QFont("Microsoft YaHei", label_font_size))
        self._module_label.setFont(QFont("Microsoft YaHei", label_font_size))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_fonts()
        self._update_progress()

    def _update_progress(self):
        """更新进度条显示"""
        total = self._exam.total_duration_sec
        if total <= 0:
            return
        # 进度需要用 timer_engine 的 elapsed，这里暂用占位
        # 实际通过 connect 更新

    def _connect_signals(self):
        # 将在 Task 11-14 中完善
        pass

    def _setup_context_menu(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("切换行测/申论").triggered.connect(self._toggle_mode)
        menu.addSeparator()
        clickthrough_action = menu.addAction("穿透模式")
        clickthrough_action.setCheckable(True)
        clickthrough_action.setChecked(self._clickthrough)
        clickthrough_action.triggered.connect(self._toggle_clickthrough)
        focus_action = menu.addAction("专注模式")
        focus_action.setCheckable(True)
        focus_action.setChecked(self._focus_mode)
        focus_action.triggered.connect(self._toggle_focus)
        menu.addSeparator()
        menu.addAction("单题计时器").triggered.connect(self._show_mini_timer)
        menu.addAction("历史记录").triggered.connect(self._show_history)
        menu.addAction("设置").triggered.connect(self._show_settings)
        menu.addSeparator()
        dark_action = menu.addAction("深色模式")
        dark_action.setCheckable(True)
        dark_action.setChecked(self._theme == "dark")
        dark_action.triggered.connect(lambda: self._set_theme("dark" if self._theme != "dark" else "light"))
        menu.addAction("导出数据").triggered.connect(self._export_data)
        menu.addSeparator()
        menu.addAction("退出").triggered.connect(self._quit_app)
        menu.exec(self.mapToGlobal(pos))

    def _toggle_clickthrough(self):
        self._clickthrough = not self._clickthrough
        if self._clickthrough:
            # Windows: 设置 WS_EX_TRANSPARENT
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_LAYERED)
        else:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT)

    def _toggle_focus(self):
        self._focus_mode = not self._focus_mode
        self._mode_label.setVisible(not self._focus_mode)
        self._module_label.setVisible(not self._focus_mode)
        self._settings_btn.setVisible(not self._focus_mode)
        self._progress_label.setVisible(not self._focus_mode)

    def _toggle_mode(self):
        pass  # 在 Task 11 完善

    def _set_theme(self, theme):
        self._theme = theme
        self._apply_theme()

    def _show_mini_timer(self):
        from .mini_timer import MiniTimer
        if self._mini_timer is None:
            self._mini_timer = MiniTimer()
            self._mini_timer.closed.connect(lambda: setattr(self, '_mini_timer', None))
        self._mini_timer.show()
        self._mini_timer.reset()

    def _show_settings(self):
        pass  # Task 13

    def _show_history(self):
        pass  # Task 14

    def _export_data(self):
        pass  # Task 14

    def _quit_app(self):
        self._hotkeys.unregister_all()
        QApplication.quit()

    # --- 窗口拖拽 ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
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

    # --- 全局快捷键处理 ---
    def nativeEvent(self, eventType, message):
        if self._hotkeys.handle_native_event(message):
            return True, 0
        return super().nativeEvent(eventType, message)
```

- [ ] **Step 2: 验证窗口能启动并显示**

创建临时 `main_debug.py` 运行验证（手动检查窗口显示、拖拽、缩放、右键菜单）

---

### Task 11: 计时控制逻辑集成

**Files:**
- Modify: `d:/Desktop Clock/src/ui/main_window.py`

- [ ] **Step 1: 在 MainWindow 中添加计时控制方法**

```python
# 在 MainWindow.__init__ 中添加:
from ..timer_engine import TimerEngine, TimerMode, TimerState

self._timer = TimerEngine(self)

# 在 _connect_signals 中完善:
def _connect_signals(self):
    self._timer.tick.connect(self._on_tick)
    self._timer.state_changed.connect(self._on_state_changed)
    self._timer.timeout.connect(self._on_timeout)
    self._reminder.reminder_triggered.connect(self._on_reminder)

def _on_tick(self, remaining_sec, elapsed_sec):
    # 更新主时间显示
    if self._timer.mode == TimerMode.COUNTDOWN:
        mins, secs = divmod(remaining_sec, 60)
    else:
        mins, secs = divmod(elapsed_sec, 60)
    self._time_label.setText(f"{mins:02d}:{secs:02d}")
    # 检查提醒
    self._reminder.check(remaining_sec, elapsed_sec)
    # 更新进度条
    self._update_progress()
    # 剩余时间少时变色
    if remaining_sec <= 300 and self._timer.mode == TimerMode.COUNTDOWN:
        self._time_label.setStyleSheet(f"color: {DARK_DANGER if self._theme == 'dark' else LIGHT_DANGER};")

def _on_state_changed(self, state):
    if state == TimerState.RUNNING:
        self._anti_ss.enable()
    else:
        self._anti_ss.disable()

def _on_timeout(self):
    self._reminder.show_timeout_dialog(self)

def _on_reminder(self, remaining_sec):
    """剩余时间提醒：边框闪烁"""
    if self._reminder.flash_enabled:
        self._flash_window()

def _flash_window(self):
    """窗口边框闪烁 3 次"""
    import time
    original_style = self.styleSheet()
    flash_style = original_style + f" QMainWindow {{ border: 2px solid {DARK_WARNING}; }}"
    for _ in range(3):
        self.setStyleSheet(flash_style)
        QApplication.processEvents()
        QTimer.singleShot(200, lambda: None)
        self.setStyleSheet(original_style)
        QApplication.processEvents()
        QTimer.singleShot(200, lambda: None)

def _update_progress(self):
    total = self._exam.total_duration_sec
    if total <= 0:
        return
    elapsed = self._timer.elapsed_sec
    ratio = min(elapsed / total, 1.0)
    w = self._progress_label.width()
    # 用样式模拟进度条
    pct = int(ratio * 100)
    self._progress_label.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 {DARK_PROGRESS_FG if self._theme == 'dark' else LIGHT_PROGRESS_FG}, "
        f"stop:{ratio} {DARK_PROGRESS_FG if self._theme == 'dark' else LIGHT_PROGRESS_FG}, "
        f"stop:{ratio} {DARK_PROGRESS_BG if self._theme == 'dark' else LIGHT_PROGRESS_BG}, "
        f"stop:1 {DARK_PROGRESS_BG if self._theme == 'dark' else LIGHT_PROGRESS_BG}); "
        f"border-radius: 2px;"
    )

# 核心操作方法:
def start_pause(self):
    if self._timer.state == TimerState.IDLE:
        mode = self._exam.mode
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
    mins = total // 60
    self._time_label.setText(f"{mins:02d}:00")
    self._update_progress()
    self._time_label.setStyleSheet("")

def switch_next_module(self):
    """空格键触发：结束当前模块，切换到下一个"""
    if self._timer.state != TimerState.RUNNING:
        return
    record = self._exam.switch_next_module(self._timer.elapsed_sec)
    if record:
        # 记录上一模块数据
        pass
    if not self._exam.is_all_modules_done:
        # 切换模块计时器
        duration = self._exam.current_module_duration_sec
        self._timer.set_countdown(max(1, self._exam.total_duration_sec - self._timer.elapsed_sec))
        self._exam.start_module(self._timer.elapsed_sec)
        self._module_label.setText(self._exam.current_module_name)
    else:
        # 所有模块完成
        self._timer.pause()
        self._save_record()
```

---

### Task 12: 模式切换 + 模块管理逻辑

**Files:**
- Modify: `d:/Desktop Clock/src/ui/main_window.py`

- [ ] **Step 1: 完善 _toggle_mode 和模块显示更新**

```python
def _toggle_mode(self):
    if self._exam.mode == ExamMode.XINGCE:
        shenlun_duration = self._data.load_config().get("shenlun_duration", 150)
        modules = [
            {"name": "小题作答", "duration_min": shenlun_duration - 60},
            {"name": "大作文", "duration_min": 60},
        ]
        self._exam.set_mode(ExamMode.SHENLUN, modules, shenlun_duration)
        self._mode_label.setText("申论")
    else:
        modules = self._data.load_config().get("xingce_modules", [])
        self._exam.set_mode(ExamMode.XINGCE, modules, 120)
        self._mode_label.setText("行测")

    self._module_label.setText(self._exam.current_module_name)
    self.reset()

def _on_module_changed(self, name, duration_sec):
    self._module_label.setText(name)
```

---

### Task 13: 设置面板（ui/settings_dialog.py）

**Files:**
- Create: `d:/Desktop Clock/src/ui/settings_dialog.py`

- [ ] **Step 1: 实现设置面板**

```python
"""设置面板：快捷键、提醒、外观、模块配置"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QPushButton, QGroupBox,
    QFormLayout, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtGui import QKeySequence


class SettingsDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data = data_manager
        self._config = data_manager.load_config()
        self.setWindowTitle("设置")
        self.setMinimumSize(480, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._create_hotkey_tab(), "快捷键")
        tabs.addTab(self._create_module_tab(), "模块配置")
        tabs.addTab(self._create_appearance_tab(), "外观")
        tabs.addTab(self._create_reminder_tab(), "提醒")
        layout.addWidget(tabs)

        # 底部按钮
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
            editor.setPlaceholderText("例如: Ctrl+Shift+Space")
            editor.setReadOnly(True)
            editor.mousePressEvent = lambda e, ed=editor, k=key: self._capture_hotkey(ed, k)
            self._hk_editors[key] = editor
            layout.addRow(label_text, editor)

        # 说明
        note = QLabel("空格键固定为「结束模块+切下一模块」，不可更改")
        note.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow(note)
        return w

    def _capture_hotkey(self, editor: QLineEdit, key_name: str):
        editor.setText("按下快捷键...")
        editor.setFocus()
        # 简化版：打开一个临时输入框
        dlg = HotkeyCaptureDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            editor.setText(dlg.hotkey_string)

    def _create_module_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # 申论总时长
        shenlun_layout = QHBoxLayout()
        shenlun_layout.addWidget(QLabel("申论整卷时长（分钟）："))
        self._shenlun_spin = QSpinBox()
        self._shenlun_spin.setRange(60, 300)
        self._shenlun_spin.setValue(self._config.get("shenlun_duration", 150))
        shenlun_layout.addWidget(self._shenlun_spin)
        shenlun_layout.addStretch()
        layout.addLayout(shenlun_layout)

        # 行测模块列表
        layout.addWidget(QLabel("行测模块配置："))
        self._module_list = QListWidget()
        modules = self._config.get("xingce_modules", [])
        for i, mod in enumerate(modules):
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
        self._theme_combo.setCurrentText("深色" if appearance.get("theme") == "dark" else "浅色")
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

        # 快捷键
        for key, editor in self._hk_editors.items():
            config["hotkeys"][key] = editor.text()

        # 模块
        modules = []
        for i in range(self._module_list.count()):
            modules.append(self._module_list.item(i).data(Qt.ItemDataRole.UserRole))
        config["xingce_modules"] = modules
        config["shenlun_duration"] = self._shenlun_spin.value()

        # 外观
        config["appearance"]["theme"] = "dark" if self._theme_combo.currentText() == "深色" else "light"
        config["appearance"]["opacity"] = self._opacity_spin.value()

        # 提醒
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
        ok_btn.clicked.connect(lambda: self._validate_and_accept())
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(QPushButton("取消", clicked=self.reject))
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
        if key not in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            key_seq = QKeySequence(key).toString()
            if key_seq:
                parts.append(key_seq)
        self.hotkey_string = "+".join(parts)
        if self.hotkey_string:
            self.accept()
```

---

### Task 14: 历史记录面板（ui/history_dialog.py）

**Files:**
- Create: `d:/Desktop Clock/src/ui/history_dialog.py`

- [ ] **Step 1: 实现历史记录面板**

```python
"""历史记录 / 数据复盘面板"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QFileDialog,
    QHeaderView
)


def _format_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{mins}分{secs}秒"


class HistoryDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data = data_manager
        self.setWindowTitle("历史记录")
        self.setMinimumSize(700, 450)
        self.setup_ui()
        self._load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 统计摘要
        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("font-size: 13px; margin: 4px;")
        layout.addWidget(self._summary_label)

        # 表格
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["日期", "模式", "整卷用时", "模块", "计划时长", "实际用时", "超时"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        export_excel_btn = QPushButton("导出 Excel")
        export_excel_btn.clicked.connect(self._export_excel)
        btn_layout.addWidget(export_excel_btn)

        export_csv_btn = QPushButton("导出 CSV")
        export_csv_btn.clicked.connect(self._export_csv)
        btn_layout.addWidget(export_csv_btn)

        clear_btn = QPushButton("清空记录")
        clear_btn.setStyleSheet("color: red;")
        clear_btn.clicked.connect(self._clear_history)
        btn_layout.addWidget(clear_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        history = self._data.load_history()
        self._table.setRowCount(0)

        total_sessions = len(history)
        total_overtimes = 0
        module_stats = {}

        for record in history:
            modules = record.get("modules") or []
            for mod in modules:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(record.get("date", "")))
                self._table.setItem(row, 1, QTableWidgetItem(record.get("mode", "")))
                self._table.setItem(row, 2, QTableWidgetItem(_format_time(record.get("total_elapsed_sec", 0))))
                self._table.setItem(row, 3, QTableWidgetItem(mod.get("name", "")))
                self._table.setItem(row, 4, QTableWidgetItem(f"{mod.get('planned_min', 0)}分"))
                self._table.setItem(row, 5, QTableWidgetItem(_format_time(mod.get("actual_sec", 0))))
                overtime = "是" if mod.get("overtime") else "否"
                self._table.setItem(row, 6, QTableWidgetItem(overtime))
                if mod.get("overtime"):
                    total_overtimes += 1
                # 统计模块平均用时
                name = mod.get("name", "")
                if name not in module_stats:
                    module_stats[name] = {"total_sec": 0, "count": 0, "overtimes": 0}
                module_stats[name]["total_sec"] += mod.get("actual_sec", 0)
                module_stats[name]["count"] += 1
                if mod.get("overtime"):
                    module_stats[name]["overtimes"] += 1

            if not modules:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(record.get("date", "")))
                self._table.setItem(row, 1, QTableWidgetItem(record.get("mode", "")))
                self._table.setItem(row, 2, QTableWidgetItem(_format_time(record.get("total_elapsed_sec", 0))))

        # 摘要
        summary_parts = [f"共 {total_sessions} 次刷题记录"]
        if total_overtimes > 0:
            summary_parts.append(f"超时 {total_overtimes} 次")
        for name, stats in module_stats.items():
            avg_sec = stats["total_sec"] // stats["count"]
            summary_parts.append(f"「{name}」平均 {_format_time(avg_sec)}，超时 {stats['overtimes']} 次")
        self._summary_label.setText("  |  ".join(summary_parts))

    def _export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "刷题记录.xlsx", "Excel (*.xlsx)")
        if path:
            self._data.export_to_excel(path)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "刷题记录.csv", "CSV (*.csv)")
        if path:
            self._data.export_to_csv(path)

    def _clear_history(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有历史记录吗？此操作不可恢复。")
        if reply == QMessageBox.StandardButton.Yes:
            self._data.clear_history()
            self._load_data()
```

---

### Task 15: main.py 入口 + 系统托盘

**Files:**
- Create: `d:/Desktop Clock/src/main.py`

- [ ] **Step 1: 实现 main.py**

```python
"""公考计时器 - 主入口"""
import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from .data_manager import DataManager
from .timer_engine import TimerEngine
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

    # 注册默认快捷键
    hotkeys = config.get("hotkeys", {})
    for name, key_str in hotkeys.items():
        if name != "next_module":
            hotkey_mgr.register_hotkey(name, key_str)

    # 创建主窗口
    window = MainWindow(exam_mgr, data_mgr, reminder, hotkey_mgr, anti_ss)

    # 应用外观设置
    appearance = config.get("appearance", {})
    window._set_theme(appearance.get("theme", "dark"))
    window.setWindowOpacity(appearance.get("opacity", 0.9))

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
    tray.activated.connect(lambda reason: window.show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
    tray.show()

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

    hotkey_mgr.hotkey_triggered.connect(on_hotkey)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 启动脚本 run.py（项目根目录）**

```python
"""开发启动脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from src.main import main
main()
```

---

### Task 16: 空格键特殊处理

**Files:**
- Modify: `d:/Desktop Clock/src/main.py`

空格键在 `RegisterHotKey` 中单独注册为固定热键，不与用户自定义快捷键混在一起。

- [ ] **Step 1: 在 main.py 中添加空格键注册**

```python
# 在注册默认快捷键之后添加:
# 空格键固定为切换下一模块
hotkey_mgr.register_hotkey("next_module", "Space")

# 在 on_hotkey 处理中添加:
elif name == "next_module":
    window.switch_next_module()
```

- [ ] **Step 2: 在 hotkey_manager.py 中确保 VK_CODES 包含 Space**

已在 Task 7 的 VK_CODES 中定义 `"Space": 0x20`，无需修改。

---

### Task 17: 数据记录完善 + 整卷保存

**Files:**
- Modify: `d:/Desktop Clock/src/ui/main_window.py`

- [ ] **Step 1: 添加 _save_record 方法**

```python
def _save_record(self):
    """保存本次刷题记录到历史"""
    from datetime import datetime
    record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "mode": "行测" if self._exam.mode == ExamMode.XINGCE else "申论",
        "total_elapsed_sec": self._timer.elapsed_sec,
        "modules": self._exam.records,
    }
    # 如果有单题计时记录，也加入
    if self._mini_timer:
        qi = self._mini_timer.elapsed_seconds()
        if qi > 0:
            record.setdefault("questions", []).append({"label": "单题", "elapsed_sec": qi})
    self._data.add_record(record)
```

---

### Task 18: 使用说明文件

**Files:**
- Create: `d:/Desktop Clock/使用说明.txt`

- [ ] **Step 1: 编写使用说明**

```
公考计时器 - 使用说明
====================

【窗口操作】
- 拖拽标题区域移动窗口
- 拖拽窗口边缘/角落缩放窗口（字体自适应）
- 右键窗口弹出功能菜单

【计时操作】
- 窗口显示：模式 | 当前模块 | 剩余时间 | 进度条
- 右键菜单选「开始/暂停」或使用快捷键

【快捷键】（可在设置中自定义）
- 空格键         → 结束当前模块 + 切换下一模块（固定）
- Ctrl+Shift+Space → 开始/暂停
- Ctrl+Shift+R   → 重置
- Ctrl+Shift+M   → 切换行测/申论模式
- Ctrl+Shift+T   → 切换穿透模式（鼠标点击穿透到下层窗口）
- Ctrl+Shift+F   → 切换专注模式（只显示时间数字）

【模式说明】
- 行测模式：120分钟整卷，5个模块（常识/言语/数量/判断/资料）
  各模块时长可在设置中自定义
- 申论模式：150/180分钟可选，小题+大作文分段计时

【提醒】
- 倒计时剩余 5/3/1 分钟时窗口闪烁提醒
- 计时结束时弹窗提醒
- 提醒可在设置中开关

【数据】
- 所有数据保存在 %APPDATA%/ExamTimer/ 目录
- 右键菜单可查看历史记录和统计
- 支持导出 Excel (.xlsx) 和 CSV (.csv)

【防锁屏】
- 计时运行期间自动阻止屏幕锁屏/休眠
- 计时停止后恢复正常

【单题计时器】
- 右键菜单打开独立小计时器
- 用于单题计时，不影响整卷计时
```

---

### Task 19: 连接所有 UI 信号，最终整合

**Files:**
- Modify: `d:/Desktop Clock/src/ui/main_window.py`（完善 _connect_signals 和 _show_settings / _show_history）
- Modify: `d:/Desktop Clock/src/main.py`（确保所有模块正确初始化）

- [ ] **Step 1: 完善 MainWindow._show_settings 和 _show_history**

```python
def _show_settings(self):
    from .settings_dialog import SettingsDialog
    dlg = SettingsDialog(self._data, self)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        # 重新加载配置并应用
        config = self._data.load_config()
        self._set_theme(config["appearance"]["theme"])
        self.setWindowOpacity(config["appearance"]["opacity"])
        self._reminder.enabled = config["reminder"]["enabled"]
        self._reminder.sound_enabled = config["reminder"]["sound"]
        self._reminder.flash_enabled = config["reminder"]["flash"]
        # 重新注册快捷键
        self._hotkeys.unregister_all()
        hotkeys = config["hotkeys"]
        for name, key_str in hotkeys.items():
            self._hotkeys.register_hotkey(name, key_str)
        self._hotkeys.register_hotkey("next_module", "Space")

def _show_history(self):
    from .history_dialog import HistoryDialog
    dlg = HistoryDialog(self._data, self)
    dlg.exec()

def _export_data(self):
    from PyQt6.QtWidgets import QFileDialog
    path, _ = QFileDialog.getSaveFileName(self, "导出数据", "刷题记录.xlsx", "Excel (*.xlsx);;CSV (*.csv)")
    if path.endswith(".csv"):
        self._data.export_to_csv(path)
    elif path.endswith(".xlsx"):
        self._data.export_to_excel(path)
```

- [ ] **Step 2: 完善 exam_manager 信号连接**

```python
def _connect_signals(self):
    self._timer.tick.connect(self._on_tick)
    self._timer.state_changed.connect(self._on_state_changed)
    self._timer.timeout.connect(self._on_timeout)
    self._reminder.reminder_triggered.connect(self._on_reminder)
    self._exam.module_changed.connect(self._on_module_changed)
    self._exam.all_modules_done.connect(self._on_all_modules_done)

def _on_all_modules_done(self):
    self._timer.pause()
    self._save_record()
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.information(self, "全部完成", "所有模块已完成！记录已保存。")
```

---

### Task 20: PyInstaller 打包

**Files:**
- Create: `d:/Desktop Clock/build.spec`

- [ ] **Step 1: 创建 PyInstaller spec 文件**

```bash
cd "d:/Desktop Clock" && pyinstaller --onefile --windowed --name "公考计时器" --add-data "src;src" src/main.py
```

或使用以下精简 spec：

```python
# build.spec
# PyInstaller 打包配置

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['openpyxl', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='公考计时器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

- [ ] **Step 2: 执行打包**

```bash
cd "d:/Desktop Clock" && pyinstaller build.spec
```

---

### Task 21: 端到端测试

- [ ] **Step 1: 启动程序，验证所有功能**

手动测试清单：
1. 窗口置顶显示，拖拽移动正常
2. 字体随窗口缩放自适应
3. 右键菜单各项功能正常
4. 空格键切换模块正常
5. Ctrl+Shift+Space 开始/暂停正常
6. 计时结束提醒弹窗
7. 穿透模式切换正常（需要刷题软件验证）
8. 专注模式隐藏控件
9. 深色/浅色主题切换
10. 设置面板修改并保存
11. 历史记录查看和导出
12. 单题小计时器
13. 系统托盘图标和菜单
14. 防锁屏生效（查看电源设置）

---

## 验证方案

1. **单元测试**：`pytest tests/ -v` 验证 data_manager、timer_engine、exam_manager
2. **手动 UI 测试**：启动程序逐项验证上述清单
3. **打包验证**：运行生成的 exe，确认独立运行正常
4. **快捷键冲突**：在有其他软件的日常环境中测试快捷键是否冲突
