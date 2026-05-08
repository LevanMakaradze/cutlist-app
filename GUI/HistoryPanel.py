from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QAbstractItemView, QWidget
)

from Storage import Storage

COLUMNS = ["სახელი", "დეტალების რაოდენობა", "მასალები", "შენახვის დრო", ""]
ACTION_COL = 4


class HistoryPanel(QGroupBox):
    """
    Lists every saved project file with basic info.
    """

    # emitted when user clicks load; payload = full project dict
    project_load_requested = Signal(dict)

    def __init__(self, settings_manager):
        super().__init__("შენახული პროექტები")
        self.settings = settings_manager
        self.storage = Storage(settings_manager)
        self._entries = []   # list of (Path, dict) tuples, parallel to rows
        self._create_ui()
        self.refresh()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        self.refresh_btn = QPushButton("განახლება")
        self.refresh_btn.clicked.connect(self.refresh)
        header_row.addStretch()
        header_row.addWidget(self.refresh_btn)
        layout.addLayout(header_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        hh.setDefaultAlignment(Qt.AlignCenter)

        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 300)
        self.table.setColumnWidth(3, 160)
        self.table.setColumnWidth(ACTION_COL, 200)

        table_width = sum(self.table.columnWidth(c) for c in range(len(COLUMNS))) + 20
        self.table.setFixedWidth(table_width)

        table_row = QHBoxLayout()
        table_row.addStretch()
        table_row.addWidget(self.table)
        table_row.addStretch()

        layout.addLayout(table_row)

    def refresh(self):
        """Reload the list of saved projects from storage."""
        self._entries = []
        files = self.storage.list_projects()

        self.table.setRowCount(0)
        for file_path in files:
            try:
                data = self.storage.load_project(file_path)
            except Exception:
                continue
            if not isinstance(data, dict):
                # skip malformed / unrelated json files in the projects folder
                continue
            self._entries.append((file_path, data))
            try:
                self._add_row(file_path, data)
            except Exception:
                # never let one bad entry break the whole history list
                continue

    def set_unit(self, unit: str):
        """Placeholder for consistency with other panels. HistoryPanel does not need unit changes."""
        pass

    def load_project(self, data: dict):
        """Load a project from history into the caller's panel (via signal)."""
        self.project_load_requested.emit(data)

    def _add_row(self, file_path: Path, data: dict):
        """Add a row to the history table for a single project."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 36)

        name = str(data.get("project_name") or "-")
        parts = data.get("parts", [])
        if not isinstance(parts, list):
            parts = []
        part_count = sum(1 for p in parts if isinstance(p, dict))

        sheets_used = data.get("sheets_used", [])
        if not isinstance(sheets_used, list):
            sheets_used = []

        material_names = []
        for s in sheets_used:
            if isinstance(s, dict):
                n = s.get("name", "").strip()
                if n and n not in material_names:
                    material_names.append(n)

        if material_names:
            max_visible = 3
            if len(material_names) > max_visible:
                display_text = ", ".join(material_names[:max_visible]) + f" +{len(material_names) - max_visible}"
            else:
                display_text = ", ".join(material_names)
            tooltip_text = ", ".join(material_names)
        else:
            display_text = "-"
            tooltip_text = "-"

        saved_at = data.get("saved_at") or ""
        display_time = saved_at.replace("T", "  ")[:20] if saved_at else "-"

        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.item(row, 0).setTextAlignment(Qt.AlignCenter)

        self.table.setItem(row, 1, QTableWidgetItem(str(part_count)))
        self.table.item(row, 1).setTextAlignment(Qt.AlignCenter)

        materials_item = QTableWidgetItem(display_text)
        materials_item.setToolTip(tooltip_text)
        materials_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, materials_item)

        self.table.setItem(row, 3, QTableWidgetItem(display_time))
        self.table.item(row, 3).setTextAlignment(Qt.AlignCenter)

        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 2, 4, 2)
        action_layout.setSpacing(6)

        load_btn = QPushButton("ჩატვირთვა")
        load_btn.setObjectName("historyLoadButton")
        load_btn.clicked.connect(lambda _, fp=file_path, d=data: self._on_load_clicked(fp, d))

        delete_btn = QPushButton("წაშლა")
        delete_btn.setObjectName("historyDeleteButton")
        delete_btn.clicked.connect(lambda _, fp=file_path: self._on_delete_clicked(fp))

        action_layout.addWidget(load_btn)
        action_layout.addWidget(delete_btn)
        self.table.setCellWidget(row, ACTION_COL, action_widget)

    def _on_load_clicked(self, file_path: Path, data: dict):
        """User clicked Load on a history row."""
        self.project_load_requested.emit(data)

    def _on_delete_clicked(self, file_path: Path):
        """User clicked Delete on a history row."""
        reply = QMessageBox.question(
            self,
            "წაშლის დადასტურება",
            "ნამდვილად გსურთ ამ პროექტის წაშლა? ეს მოქმედება შეუქცევადია.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.storage.delete_project(file_path)
            self.refresh()