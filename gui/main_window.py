import sys
from pathlib import Path

# Add root folder to sys.path to allow imports from root directory under all execution contexts
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
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
from HistoryPanel import HistoryPanel
from SettingsDialog import SettingsDialog
from SettingsManager import SettingsManager
from LayoutPanel import LayoutPanel


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
        self.history_panel.set_unit(unit)
        if hasattr(self, "layout_panel"):
            self.layout_panel.set_unit(unit)

    def _on_project_load_requested(self, data: dict):
        """Handle loading a project from history."""
        if self.project_panel.has_unsaved_changes():
            box = QMessageBox(self)
            box.setWindowTitle("შეუნახავი ცვლილებები")
            box.setText("პროექტში არსებობს შეუნახავი ცვლილებები. გსურთ მათი შენახვა ჩატვირთვის წინ?")
            box.setIcon(QMessageBox.Warning)
            save_btn = box.addButton("შენახვა და ჩატვირთვა", QMessageBox.AcceptRole)
            discard_btn = box.addButton("იგნორირება და ჩატვირთვა", QMessageBox.DestructiveRole)
            cancel_btn = box.addButton("გაუქმება", QMessageBox.RejectRole)
            box.setDefaultButton(save_btn)
            box.exec()

            clicked = box.clickedButton()
            if clicked == cancel_btn:
                return
            if clicked == save_btn:
                if not self.project_panel.save_current():
                    return

        sheets_used = data.get("sheets_used", [])
        if not isinstance(sheets_used, list):
            sheets_used = []

        self.sheets_panel.merge_sheets(sheets_used)

        self.project_panel.load_project(data)
        self.tabs.setCurrentIndex(0)

    def _on_generate_layout_triggered(self):
        """Switches the view to the Layout tab and triggers calculations safely."""
        self.tabs.setCurrentIndex(1)
        self.layout_panel.run_calculation()

    def create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        input_tab = QWidget()
        self.tabs.addTab(input_tab, "ზომები")

        self.sheets_panel = SheetsPanel(self.settings)
        self.sheets_panel.setFixedWidth(500)
        
        self.project_panel = ProjectPanel(self.settings)
        
        self.layout_panel = LayoutPanel(self.settings, self.project_panel, self.sheets_panel, self)
        self.tabs.addTab(self.layout_panel, "განლაგება")
        
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_panel = HistoryPanel(self.settings)
        history_layout.addWidget(self.history_panel)
        self.tabs.addTab(history_tab, "ისტორია")

        input_layout = QVBoxLayout(input_tab)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        input_layout.addWidget(splitter)
        splitter.addWidget(self.sheets_panel)
        
        self.sheets_panel.sheets_changed.connect(self.project_panel.update_material_options)
        self.project_panel.update_material_options(self.sheets_panel.get_sheets())
        splitter.addWidget(self.project_panel)
        
        self.project_panel.generate_btn.clicked.connect(self._on_generate_layout_triggered)
        
        self.history_panel.project_load_requested.connect(self._on_project_load_requested)
        self.project_panel.project_saved.connect(lambda _: self.history_panel.refresh())


def load_stylesheet(app):
    dir_path = Path(__file__).resolve().parent
    style_path = dir_path / "style.qss"
    layout_style_path = dir_path / "style_layout.qss"

    stylesheet_content = ""
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as file:
            stylesheet_content += file.read() + "\n"
    if layout_style_path.exists():
        with open(layout_style_path, "r", encoding="utf-8") as file:
            stylesheet_content += file.read() + "\n"

    if stylesheet_content:
        app.setStyleSheet(stylesheet_content)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_stylesheet(app)

    settings = SettingsManager()
    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec())