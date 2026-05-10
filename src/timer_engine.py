"""计时引擎：倒计时/正计时状态机"""
from enum import Enum, auto
from PySide6.QtCore import QObject, QTimer, Signal


class TimerState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()


class TimerMode(Enum):
    COUNTDOWN = auto()
    COUNTUP = auto()


class TimerEngine(QObject):
    tick = Signal(int, int)
    timeout = Signal()
    state_changed = Signal(TimerState)

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
    def state(self): return self._state

    @property
    def mode(self): return self._mode

    @property
    def remaining_sec(self): return self._remaining_sec

    @property
    def elapsed_sec(self): return self._elapsed_sec

    @property
    def total_sec(self): return self._total_sec

    def set_countdown(self, total_seconds: int):
        self._mode = TimerMode.COUNTDOWN
        self._total_sec = total_seconds
        self._remaining_sec = max(0, total_seconds)
        self._elapsed_sec = 0
        self._set_state(TimerState.IDLE)

    def set_countup(self):
        self._mode = TimerMode.COUNTUP
        self._total_sec = 0
        self._remaining_sec = 0
        self._elapsed_sec = 0
        self._set_state(TimerState.IDLE)

    def start(self):
        if self._state in (TimerState.IDLE,):
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
        self._remaining_sec = max(0, seconds)
        self.tick.emit(self._remaining_sec, self._elapsed_sec)
