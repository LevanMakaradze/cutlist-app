from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox, QMessageBox,QVBoxLayout, QHBoxLayout,QPushButton,
)
from CustomTable import CustomTable
from Storage import Storage

COLUMNS = [
    ("სახელი",    "text"),
    ("სიგრძე",    "dim"),
    ("სიგანე",    "dim"),
    ("რაოდენობა", "qty"),
]

class SheetsPanel(QGroupBox):
    modified = Signal()
    # emitted whenever sheet list changes so ProjectPanel can refresh its combo
    sheets_changed = Signal(list)   # list of dicts with name/length/width
    
    def __init__(self, settings_manager):
        super().__init__("მასალები")
        self.settings = settings_manager
        self.storage = Storage(settings_manager)
        self._saved_data = []
        self._dirty = False
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        self.table = CustomTable(COLUMNS)
        self.table.modified.connect(self._on_modified)

        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.clear_btn = QPushButton("გასუფთავება")
        self.save_btn = QPushButton("შენახვა")
        self.load_saved_btn = QPushButton("შენახულის ჩატვირთვა")

        self.clear_btn.clicked.connect(self._on_clear)
        self.save_btn.clicked.connect(self._on_save)
        self.load_saved_btn.clicked.connect(self._on_load_saved)

        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.load_saved_btn)
        layout.addLayout(buttons)
        
    def _on_modified(self):
        self._dirty = True
        self.modified.emit()
        
    def _on_clear(self):
        reply = QMessageBox.question(
            self,
            "გაფრთხილება",
            "ნამდვილად გსურთ ყველა მასალის წაშლა? ეს მოქმედება შეუქცევადია თუ შენახული არ გაქვთ.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.table.clear_all()
        
    def load_saved(self, warn_if_dirty: bool = True):
        if warn_if_dirty and self._dirty:
            reply = QMessageBox.warning(
                self,
                "გაფრთხილება",
                "მიმდინარე მონაცემები დაიკარგება. ჩავტვირთოთ შენახული მასალები?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return False

        data = self.storage.load_sheets()
        if not data:
            if warn_if_dirty:
                QMessageBox.information(self, "ჩატვირთვა", "შენახული მასალები არ არის.")
            return False

        self.table.set_data(data)
        self._saved_data = data
        self._dirty = False
        # notify project panel of updated sheets
        try:
            self.sheets_changed.emit(self.get_sheets())
        except Exception:
            pass
        return True

    def _on_load_saved(self):
        self.load_saved(warn_if_dirty=True)

    def _on_save(self):
        data = self.table.get_data()   # values always in mm
        # validate non-empty rows: name, length and width must be present and length/width non-zero
        errors = []
        for i, r in enumerate(data, start=1):
            name = r.get("სახელი", "").strip()
            l = r.get("სიგრძე", "").strip()
            w = r.get("სიგანე", "").strip()
            # determine if row is non-empty (any field present)
            if not (name or l or w or r.get("რაოდენობა", "")):
                continue
            if not name:
                errors.append(f"#{i}: სახელი აუცილებელია")
            if not l:
                errors.append(f"#{i}: სიგრძე ცარიელია")
            else:
                try:
                    if float(l) == 0:
                        errors.append(f"#{i}: სიგრძე არ შეიძლება იყოს 0")
                except Exception:
                    errors.append(f"#{i}: სიგრძე არ არის ციფრი")
            if not w:
                errors.append(f"#{i}: სიგანე ცარიელია")
            else:
                try:
                    if float(w) == 0:
                        errors.append(f"#{i}: სიგანე არ შეიძლება იყოს 0")
                except Exception:
                    errors.append(f"#{i}: სიგანე არ არის ციფრი")
        if errors:
            QMessageBox.critical(self, "შენახვის შეცდომა", "\n".join(errors))
            return

        try:
            self.storage.save_sheets(data)
            QMessageBox.information(self,"შენახვა", "მასალები წარმატებით შენახულია.")
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა შენახვისას", str(e))
            return
        
        self._saved_data = data
        self._dirty = False
        # notify project panel of new materials
        try:
            self.sheets_changed.emit(self.get_sheets())
        except Exception:
            pass
    
    def set_unit(self, unit: str):
        self.table.set_unit(unit)

    def get_sheets(self) -> list[dict]:
        """Return only rows that have name AND at least one dimension, in mm."""
        rows = self.table.get_data()
        result = []
        for r in rows:
            name = r.get("სახელი", "").strip()
            l = r.get("სიგრძე", "").strip()
            w = r.get("სიგანე", "").strip()
            if name or l or w:
                result.append({"name": name, "length": l, "width": w, "qty": r.get("რაოდენობა", "")})
        return result

        