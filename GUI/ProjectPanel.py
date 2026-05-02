from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
)


class ProjectPanel(QGroupBox):

    def __init__(self):
        super().__init__("პროექტი")
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        job_row = QHBoxLayout()

        job_row.addWidget(QLabel("სახელი"))

        name_input = QLineEdit()
        name_input.setMinimumWidth(200)
        name_input.setMaximumWidth(250)

        job_row.addWidget(name_input)

        job_row.addSpacing(20)

        job_row.addWidget(QLabel("მასალა"))

        material_combo = QComboBox()
        material_combo.addItems(
            [
                "მდფ",
                "ლამინატი",
            ]
        )
        
        material_combo.setMinimumWidth(200)
        material_combo.setMaximumWidth(300)

        job_row.addWidget(material_combo)
        job_row.addSpacing(20)

        texture_button = QPushButton("ტექსტურის შეცვლა")
        texture_button.setObjectName("textureButton")
        
        job_row.addWidget(texture_button)
        
        job_row.addStretch()
        generate_button = QPushButton("ავტომატური განლაგება")
        generate_button.setObjectName("generateButton")
        
        job_row.addWidget(generate_button)      
        
        layout.addLayout(job_row)


        self.parts_table = QTableWidget(20, 5)

        self.parts_table.setHorizontalHeaderLabels(
            [
                "სახელი",
                "სიგრძე",
                "სიგანე",
                "რაოდენობა",
                "მობრუნება",
            ]
        )

        self.configure_table(self.parts_table)

        for row in range(20):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                Qt.ItemIsEnabled
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsSelectable
            )
            checkbox_item.setCheckState(Qt.Unchecked)

            self.parts_table.setItem(row, 4, checkbox_item)

        layout.addWidget(self.parts_table)

        right_buttons = QHBoxLayout()
        right_buttons.addStretch()

        right_buttons.addWidget(QPushButton("შენახვა"))
        right_buttons.addWidget(QPushButton("გაუქმება"))

        layout.addLayout(right_buttons)
    
    def configure_table(self, table):
        
        table.horizontalHeader().setStretchLastSection(True)

        header = table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        table.setColumnWidth(0, 60)