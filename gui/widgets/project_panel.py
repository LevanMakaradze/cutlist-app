from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from gui.widgets.custom_table import CustomTable
from gui.widgets.checkable_combo_box import CheckableComboBox
from services.storage import Storage

COLUMNS = [
    ("სახელი",    "text"),
    ("სიგრძე",    "dim"),
    ("სიგანე",    "dim"),
    ("რაოდენობა", "qty"),
    ("ბრუნვა", "check"),
]


class ProjectPanel(QGroupBox):
    modified = Signal()
    project_saved = Signal(str)

    def __init__(self, settings_manager=None):
        super().__init__("პროექტი")
        self.settings = settings_manager
        self.storage = Storage(settings_manager) if settings_manager else None
        self._saved_state = {}
        self._dirty = False
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("სახელი"))
        self.name_input = QLineEdit()
        self.name_input.setMinimumWidth(200)
        self.name_input.setMaximumWidth(250)
        header.addWidget(self.name_input)

        header.addSpacing(20)
        header.addWidget(QLabel("მასალა"))
        self.material_combo = CheckableComboBox()
        self.material_combo.setMinimumWidth(200)
        self.material_combo.setMaximumWidth(300)
        self.material_combo.checkedItemsChanged.connect(
            lambda _: self._mark_dirty()
        )
        header.addWidget(self.material_combo)

        header.addSpacing(20)
        self.texture_btn = QPushButton("ბრუნვის გადამრთველი")
        self.texture_btn.setObjectName("textureToggleButton")
        self.texture_btn.setFixedWidth(200)
        header.addWidget(self.texture_btn)

        header.addStretch()
        self.generate_btn = QPushButton("ავტომატური განლაგება")
        self.generate_btn.setObjectName("generateButton")
        header.addWidget(self.generate_btn)

        layout.addLayout(header)

        self.table = CustomTable(COLUMNS)
        self.table.modified.connect(self._mark_dirty)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.clear_btn = QPushButton("გასუფთავება")
        self.save_btn = QPushButton("შენახვა")

        self.clear_btn.clicked.connect(self._on_clear_all)
        self.save_btn.clicked.connect(self._on_save)

        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        buttons.addWidget(self.save_btn)
        layout.addLayout(buttons)

    def has_unsaved_changes(self) -> bool:
        return self._dirty

    def _on_clear_all(self):
        reply = QMessageBox.question(
            self,
            "გაფრთხილება",
            "ნამდვილად გსურთ პროექტის მონაცემების წაშლა? ეს მოქმედება შეუქცევადია თუ შენახული არ გაქვთ.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.table.clear_all()
            self.name_input.clear()
            self.material_combo.setCheckedItems([])

    def _mark_dirty(self):
        self._dirty = True

    def _on_save(self):
        self.save_current()

    def save_current(self) -> bool:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "შეცდომა", "პროექტს ესაჭიროება სახელი.")
            return False

        data = {
            "project_name": name,
            "sheets_used": [
                {
                    "name": s["name"],
                    "length": s["length"],
                    "width": s["width"],
                    "qty": s.get("qty", ""),
                }
                for s in self._get_selected_sheets()
            ],
            "parts": self.table.get_data(),
        }

        try:
            path = self.storage.save_project(data)
            QMessageBox.information(self, "შენახვა", "პროექტი შენახულია.")
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა", str(e))
            return False

        self._saved_state = data
        self._dirty = False
        if path:
            try:
                self.project_saved.emit(str(path))
            except Exception:
                pass
        return True

    def _get_selected_sheets(self) -> list:
        checked_names = self.material_combo.checkedItems()
        result = []
        for name in checked_names:
            for i in range(self.material_combo.model().rowCount()):
                item = self.material_combo.model().item(i)
                if item and item.text() == name:
                    data = item.data(Qt.UserRole)
                    if data:
                        result.append(data)
                    else:
                        result.append(
                            {"name": name, "length": "", "width": "", "qty": ""}
                        )
                    break
        return result

    def _restore(self, state: dict):
        self.name_input.blockSignals(True)
        self.name_input.setText(state.get("project_name", ""))
        self.name_input.blockSignals(False)

        names = [s.get("name", "") for s in state.get("sheets_used", [])]
        self.material_combo.setCheckedItems(names)
        self.table.set_data(state.get("parts", []))
        self._dirty = False

    def load_project(self, data: dict):
        self._restore(data)

    def get_project_data(self) -> dict:
        return {
            "project_name": self.name_input.text().strip(),
            "sheets_used": self._get_selected_sheets(),
            "parts": self.table.get_data(),
        }

    def set_unit(self, unit: str):
        self.table.set_unit(unit)

    def update_material_options(self, sheets: list[dict]):
        previously_checked = self.material_combo.checkedItems()
        self.material_combo.clearItems()
        for sheet in sheets:
            name = sheet.get("name", "").strip()
            if not name:
                continue
            item_was_checked = name in previously_checked
            self.material_combo.addCheckItem(name, checked=item_was_checked)
            idx = self.material_combo.model().rowCount() - 1
            model_item = self.material_combo.model().item(idx)
            if model_item:
                model_item.setData(sheet, Qt.UserRole)