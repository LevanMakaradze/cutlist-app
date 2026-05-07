import json
import re
from datetime import datetime
from pathlib import Path


def _sanitize(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", name.strip())
    return name or "project"


class Storage:
    """
    Storage handles reading/writing projects and sheets to directory.
    
    Projects and sheets are saved as JSON in settings.data_directory.
    """
    def __init__(self, settings_manager):
        self.settings = settings_manager

    # sheets
    
    @property
    def _sheets_file(self) -> Path:
        return self.settings.data_directory / "sheets.json"

    def save_sheets(self, sheets: list):
        with open(self._sheets_file, "w", encoding="utf-8") as f:
            json.dump(sheets, f, indent=4, ensure_ascii=False)

    def load_sheets(self) -> list:
        if not self._sheets_file.exists():
            return []
        try:
            with open(self._sheets_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


    # projects

    def save_project(self, data: dict) -> Path:
        """
        data must contain: project_name, parts, sheets_used, created_at
        """
        name = data.get("project_name", "project")
        safe = _sanitize(name)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{safe}_{ts}.json"
        file_path = self.settings.projects_dir / filename
        data["saved_at"] = datetime.now().isoformat()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return file_path

    def load_project(self, file_path: Path) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete_project(self, file_path: Path):
        Path(file_path).unlink(missing_ok=True)

    def list_projects(self) -> list[Path]:
        files = list(self.settings.projects_dir.glob("*.json"))
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files