"""历史记录 / 数据复盘面板"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QFileDialog,
    QHeaderView, QMessageBox
)


def _format_time(seconds):
    if not seconds:
        return "0秒"
    m, s = divmod(int(seconds), 60)
    if m > 0:
        return f"{m}分{s}秒"
    return f"{s}秒"


class HistoryDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._data = data_manager
        self.setWindowTitle("历史记录")
        self.setMinimumSize(700, 450)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("font-size: 13px; margin: 4px;")
        layout.addWidget(self._summary_label)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["日期", "模式", "整卷用时", "模块", "计划时长", "实际用时", "超时"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        export_xlsx_btn = QPushButton("导出 Excel")
        export_xlsx_btn.clicked.connect(self._export_xlsx)
        btn_layout.addWidget(export_xlsx_btn)

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

        summary_parts = [f"共 {total_sessions} 次刷题记录"]
        if total_overtimes > 0:
            summary_parts.append(f"超时 {total_overtimes} 次")
        for name, stats in module_stats.items():
            avg_sec = stats["total_sec"] // stats["count"]
            summary_parts.append(f"「{name}」平均 {_format_time(avg_sec)}，超时 {stats['overtimes']} 次")
        self._summary_label.setText("  |  ".join(summary_parts))

    def _export_xlsx(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "刷题记录.xlsx", "Excel (*.xlsx)")
        if path:
            self._data.export_to_excel(path)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "刷题记录.csv", "CSV (*.csv)")
        if path:
            self._data.export_to_csv(path)

    def _clear_history(self):
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有历史记录吗？此操作不可恢复。")
        if reply == QMessageBox.StandardButton.Yes:
            self._data.clear_history()
            self._load_data()
