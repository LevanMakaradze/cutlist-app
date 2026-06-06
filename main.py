import sys
import multiprocessing
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from gui.main_window import MainWindow
from services.settings_manager import SettingsManager

# Global exception handler to prevent silent exits
def global_exception_handler(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)
    error_msg = f"დაფიქსირდა მოულოდნელი შეცდომა:\n\n{value}"
    # Ensure there is a running application instance
    if QApplication.instance():
        QMessageBox.critical(None, "შეცდომა", error_msg)
    else:
        print(error_msg, file=sys.stderr)

def load_application_theme(app: QApplication, styles_dir: Path):
    """Aggregates and loads the modular QSS stylesheets."""
    ordered_sheets = [
        "base.qss",
        "inputs.qss",
        "tables.qss",
        "cards.qss",
        "details.qss",
    ]

    combined_css = []
    for sheet_name in ordered_sheets:
        path = styles_dir / sheet_name
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    combined_css.append(f.read())
            except IOError as e:
                print(f"Failed to read stylesheet {sheet_name}: {e}")

    if combined_css:
        app.setStyleSheet("\n".join(combined_css))


def main():
    # Call freeze_support immediately to fix recursive subprocess launches
    multiprocessing.freeze_support()

    # Set the global exception handler
    sys.excepthook = global_exception_handler

    app = QApplication(sys.argv)

    # Initialize settings and resolve resource paths
    settings = SettingsManager()
    styles_dir = Path(__file__).resolve().parent / "gui" / "styles"

    # Apply style sheets
    load_application_theme(app, styles_dir)

    # Launch GUI
    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()