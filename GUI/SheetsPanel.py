from PySide6.QtWidgets import (
    QGroupBox,QVBoxLayout, QHBoxLayout,QPushButton,
)
from CustomTable import CustomTable

COLUMNS = [
    ("სახელი",    "text"),
    ("სიგრძე",    "dim"),
    ("სიგანე",    "dim"),
    ("რაოდენობა", "qty"),
]

class SheetsPanel(QGroupBox):

    def __init__(self):
        super().__init__("მასალები")
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        self.table = CustomTable(COLUMNS)

        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.clear_btn  = QPushButton("გასუფთავება")
        self.save_btn   = QPushButton("შენახვა")
        self.cancel_btn = QPushButton("გაუქმება")
        self.cancel_btn.setEnabled(False)

        self.clear_btn.clicked.connect(self._on_clear)

        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)
        
    def _on_clear(self):
        self.table.clear_all()
    
    def set_unit(self, unit: str):
        self.table.set_unit(unit)

        