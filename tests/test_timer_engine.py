from src.timer_engine import TimerEngine, TimerState, TimerMode


def test_initial_state():
    t = TimerEngine()
    assert t.state == TimerState.IDLE
    assert t.mode == TimerMode.COUNTDOWN
    assert t.remaining_sec == 0
    assert t.elapsed_sec == 0


def test_start_countdown():
    t = TimerEngine()
    t.set_countdown(60)
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


def test_tick_signal():
    signals_received = []
    t = TimerEngine()
    t.tick.connect(lambda r, e: signals_received.append((r, e)))
    t.set_countdown(60)
    t.start()
    t._tick()
    assert len(signals_received) == 1
    assert signals_received[0][0] == 59
    assert signals_received[0][1] == 1


def test_countdown_finish():
    t = TimerEngine()
    t.set_countdown(1)
    t.start()
    t._tick()
    assert t.state == TimerState.FINISHED
    assert t.elapsed_sec == 1
    assert t.remaining_sec == 0
