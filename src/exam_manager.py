"""考试模式管理：行测/申论模式、模块切换、用时记录"""
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal


class ExamMode(Enum):
    XINGCE = auto()
    SHENLUN = auto()


class ExamManager(QObject):
    module_switched = Signal(dict)
    all_modules_done = Signal()
    module_changed = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = ExamMode.XINGCE
        self._modules = []
        self._current_index = 0
        self._total_duration_sec = 7200
        self._records = []
        self._module_start_elapsed = 0

    @property
    def mode(self): return self._mode

    @property
    def current_module_index(self): return self._current_index

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
    def total_duration_sec(self): return self._total_duration_sec

    @property
    def is_all_modules_done(self):
        return self._current_index >= len(self._modules)

    @property
    def module_count(self): return len(self._modules)

    @property
    def records(self): return list(self._records)

    def set_mode(self, mode: ExamMode, modules=None, total_duration_min=None):
        self._mode = mode
        if modules:
            self._modules = list(modules)
        if total_duration_min:
            self._total_duration_sec = total_duration_min * 60
        elif mode == ExamMode.XINGCE:
            self._total_duration_sec = 7200
        self._current_index = 0
        self._records = []
        if self._modules:
            self.module_changed.emit(self.current_module_name, self.current_module_duration_sec)

    def start_module(self, total_elapsed_sec: int = 0):
        self._module_start_elapsed = total_elapsed_sec

    def switch_next_module(self, current_elapsed_sec: int = 0) -> dict:
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
        self._current_index = 0
        self._records = []
        if self._modules:
            self.module_changed.emit(self.current_module_name, self.current_module_duration_sec)

    def set_modules(self, modules: list):
        self._modules = list(modules)
        self.reset_modules()
