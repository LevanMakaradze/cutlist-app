import json
import os
from pathlib import Path

APP_NAME = "CutList"

class SettingsManager:
    DEFAULTS = {
        "units": "mm",
        "kerf": 4.4,
        "data_directory": None,
    }

    def __init__(self):
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        self.app_dir = Path(appdata) / APP_NAME
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.app_dir / "settings.json"
        self._settings = self._load()

    def _load(self) -> dict:
        default_projects = self.app_dir / "projects"
        default_projects.mkdir(parents=True, exist_ok=True)

        if not self.settings_file.exists():
            settings = self.DEFAULTS.copy()
            settings["data_directory"] = str(default_projects)
            self._write(settings)
            return settings

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
            merged = self.DEFAULTS.copy()
            merged.update(settings)
            if not merged["data_directory"]:
                merged["data_directory"] = str(default_projects)
            return merged
        except Exception:
            settings = self.DEFAULTS.copy()
            settings["data_directory"] = str(default_projects)
            self._write(settings)
            return settings

    @property
    def projects_dir(self) -> Path:
        path = Path(self._settings["data_directory"])
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(self, settings: dict):
        self._settings = settings
        self._write(settings)

    def _write(self, settings: dict):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self._write(self._settings)