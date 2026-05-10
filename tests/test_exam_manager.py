from src.exam_manager import ExamManager, ExamMode


def test_init_xingce_mode():
    modules = [
        {"name": "常识", "duration_min": 10},
        {"name": "言语", "duration_min": 35},
    ]
    mgr = ExamManager()
    mgr.set_mode(ExamMode.XINGCE, modules, 120)
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
    mgr.start_module(0)
    result = mgr.switch_next_module(320)
    assert result["prev_module"] == "A"
    assert result["actual_sec"] == 320
    assert result["overtime"] == True
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


def test_records_accumulate():
    modules = [
        {"name": "M1", "duration_min": 5},
        {"name": "M2", "duration_min": 10},
    ]
    mgr = ExamManager()
    mgr.set_mode(ExamMode.XINGCE, modules)
    mgr.start_module(0)
    mgr.switch_next_module(300)
    mgr.start_module(300)
    mgr.switch_next_module(800)
    assert len(mgr.records) == 2
    assert mgr.records[0]["actual_sec"] == 300
    assert mgr.records[1]["actual_sec"] == 500
