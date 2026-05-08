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
        return True

    def _on_load_saved(self):
        self.load_saved(warn_if_dirty=True)

    def _on_save(self):
        data = self.table.get_data()   # values always in mm
        try:
            self.storage.save_sheets(data)
            QMessageBox.information(self,"შენახვა", "მასალები წარმატებით შენახულია.")
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა შენახვისას", str(e))
            return
        
        self._saved_data = data
        self._dirty = False
    
    def set_unit(self, unit: str):
        self.table.set_unit(unit)

        