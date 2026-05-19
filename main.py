import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from services.settings_manager import SettingsManager


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
    from PySide6.QtCore import Qt

    main()