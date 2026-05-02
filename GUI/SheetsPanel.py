from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox, QHeaderView, QVBoxLayout, QHBoxLayout,
    QPushButton,QTableWidget
)

class SheetsPanel(QGroupBox):

    def __init__(self):
        super().__init__("მასალები")
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        self.sheets_table = QTableWidget(20, 4)
        self.sheets_table.setHorizontalHeaderLabels(
            ["სახელი", "სიგრძე", "სიგანე", "რაოდენობა"]
        )

        layout.addWidget(self.sheets_table)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(QPushButton("შენახვა"))
        buttons.addWidget(QPushButton("გაუქმება"))

        layout.addLayout(buttons)
        
    def configure_table(self, table):
        
        table.horizontalHeader().setStretchLastSection(True)

        header = table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        table.setColumnWidth(0, 80)