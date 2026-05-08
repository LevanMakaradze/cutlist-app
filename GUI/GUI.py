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

from SheetsPanel import SheetsPanel
from ProjectPanel import ProjectPanel
from SettingsDialog import SettingsDialog
from SettingsManager import SettingsManager

class MainWindow(QMainWindow):
    def __init__(self, settings: SettingsManager):
        super().__init__()

        self.settings = settings
        self.create_menu()
        self.create_ui()
        self.sheets_panel.load_saved(warn_if_dirty=False)
        self._apply_unit(self.settings.get("units", "mm"))
        
        self.showMaximized()

    def create_menu(self):
        menu_bar = self.menuBar()
        menu_bar.addAction("პარამეტრები", self._open_settings)

    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        dlg.register_unit_callback(self._apply_unit)
        if dlg.exec():
            pass
        else:
            self._apply_unit(self.settings.get("units", "mm"))

    def _apply_unit(self, unit: str):
        self.sheets_panel.set_unit(unit)
        self.project_panel.set_unit(unit)

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
        
        self.sheets_panel = SheetsPanel(self.settings)
        self.sheets_panel.setFixedWidth(500)
        splitter.addWidget(self.sheets_panel)
        # wire project panel and material updates
        self.project_panel = ProjectPanel(self.settings)
        self.sheets_panel.sheets_changed.connect(self.project_panel.update_material_options)
        # seed initial material list (may be empty until load_saved runs)
        self.project_panel.update_material_options(self.sheets_panel.get_sheets())
        splitter.addWidget(self.project_panel)


def load_stylesheet(app):
    with open("style.qss", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_stylesheet(app)

    settings = SettingsManager()
    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec())