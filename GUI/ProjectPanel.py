from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
)
from CustomTable import CustomTable

COLUMNS = [
    ("სახელი",    "text"),
    ("სიგრძე",    "dim"),
    ("სიგანე",    "dim"),
    ("რაოდენობა", "qty"),
    ("ბრუნვა", "check"),
]

class ProjectPanel(QGroupBox):

    def __init__(self):
        super().__init__("პროექტი")
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        # header
        header = QHBoxLayout()
        
        header.addWidget(QLabel("სახელი"))
        self.name_input = QLineEdit()
        self.name_input.setMinimumWidth(200)
        self.name_input.setMaximumWidth(250)
        header.addWidget(self.name_input)
        
        header.addSpacing(20)
        
        header.addWidget(QLabel("მასალა"))
        self.material_combo = QComboBox()
        self.material_combo.addItems(
            [
                "მდფ",
                "ლამინატი",
            ]
        )
        self.material_combo.setMinimumWidth(200)
        self.material_combo.setMaximumWidth(300)
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

        # table
        self.table = CustomTable(COLUMNS)
        layout.addWidget(self.table)

        # footer buttons
        buttons = QHBoxLayout()
        self.clear_btn  = QPushButton("გასუფთავება")
        self.save_btn   = QPushButton("შენახვა")
        self.cancel_btn = QPushButton("გაუქმება")
        self.cancel_btn.setEnabled(False)

        self.clear_btn.clicked.connect(self._on_clear_all)
        # todo: save and cancel button connects
        
        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)

        layout.addLayout(buttons)
    
    def _on_clear_all(self):
        self.table.clear_all()
        self.name_input.clear()
        # todo: combobox
    
    def set_unit(self, unit: str):
        self.table.set_unit(unit)