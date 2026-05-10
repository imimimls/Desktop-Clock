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

    def load_history(self) -> list:
        if not os.path.exists(self.history_path):
            return []
        with open(self.history_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_history(self, history: list):
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
                modules = record.get("modules") or []
                for mod in modules:
                    writer.writerow([
                        record["date"], record["mode"], total_sec,
                        mod.get("name", ""), mod.get("planned_min", 0),
                        mod.get("actual_sec", 0),
                        "是" if mod.get("overtime") else "否"
                    ])
                if not modules:
                    writer.writerow([record["date"], record["mode"], total_sec, "", "", "", ""])

    def export_to_excel(self, path: str):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "刷题记录"
        ws.append(["日期", "模式", "整卷用时(秒)", "模块", "计划时长(分)", "实际用时(秒)", "超时"])
        for record in self.load_history():
            total_sec = record.get("total_elapsed_sec", 0)
            modules = record.get("modules") or []
            for mod in modules:
                ws.append([
                    record["date"], record["mode"], total_sec,
                    mod.get("name", ""), mod.get("planned_min", 0),
                    mod.get("actual_sec", 0),
                    "是" if mod.get("overtime") else "否"
                ])
            if not modules:
                ws.append([record["date"], record["mode"], total_sec, "", "", "", ""])
        wb.save(path)
