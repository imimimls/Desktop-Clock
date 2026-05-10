import json
import tempfile
import os
from src.data_manager import DataManager


def test_init_creates_default_config():
    with tempfile.TemporaryDirectory() as tmp:
        dm = DataManager(data_dir=tmp)
        config = dm.load_config()
        assert config["xingce_modules"][0]["name"] == "常识判断"
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
