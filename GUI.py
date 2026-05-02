import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.create_menu()
        self.create_ui()

        self.showMaximized()

    def create_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("ფაილი")
        file_menu.addAction("ახალი")
        file_menu.addAction("გახსნა")
        file_menu.addAction("შენახვა")

        settings_menu = menu_bar.addMenu("პარამეტრები")
        settings_menu.addAction("ერთეული")
        settings_menu.addAction("ხერხი")

    def create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)

        tabs = QTabWidget()
        root_layout.addWidget(tabs)

        input_tab = QWidget()
        tabs.addTab(input_tab, "ზომები")

        tabs.addTab(QWidget(), "განლაგება")
        tabs.addTab(QWidget(), "ისტორია")

        input_layout = QVBoxLayout(input_tab)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        input_layout.addWidget(splitter)

        # LEFT PANEL
        left_group = QGroupBox("მასალები")
        left_group.setFixedWidth(700)

        left_layout = QVBoxLayout(left_group)
        self.sheets_table = QTableWidget(20, 4)
        self.sheets_table.setHorizontalHeaderLabels(
            ["სახელი", "სიგრძე", "სიგანე", "რაოდენობა"]
        )

        self.configure_table(self.sheets_table)

        left_layout.addWidget(self.sheets_table)

        left_buttons = QHBoxLayout()
        left_buttons.addStretch()

        left_buttons.addWidget(QPushButton("შენახვა"))
        left_buttons.addWidget(QPushButton("გაუქმება"))

        left_layout.addLayout(left_buttons)

        splitter.addWidget(left_group)

        # RIGHT PANEL
        right_group = QGroupBox("პროექტი")
        right_group.setMinimumWidth(500)

        right_layout = QVBoxLayout(right_group)

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
        
        right_layout.addLayout(job_row)


        self.parts_table = QTableWidget(20, 5)

        self.parts_table.setHorizontalHeaderLabels(
            [
                "სიგრძე",
                "სიგანე",
                "რაოდენობა",
                "ტექსტურა",
                "სახელი",
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

        right_layout.addWidget(self.parts_table)

        right_buttons = QHBoxLayout()
        right_buttons.addStretch()

        right_buttons.addWidget(QPushButton("შენახვა"))
        right_buttons.addWidget(QPushButton("გაუქმება"))

        right_layout.addLayout(right_buttons)

        splitter.addWidget(right_group)
        
    def configure_table(self, table):
        
        table.horizontalHeader().setStretchLastSection(True)

        header = table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        table.setColumnWidth(0, 60)


def load_stylesheet(app):
    with open("style.qss", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # app.setStyle("Fusion")

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())