from PySide6.QtCore import QThread, Signal
from engine.parallel_runner import run_all_parallel


class LayoutWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, parts, sheets, settings):
        super().__init__()
        self.parts = parts
        self.sheets = sheets
        self.settings = settings

    def run(self):
        try:
            collection = run_all_parallel(
                self.parts, self.sheets, self.settings
            )
            self.finished.emit(collection)
        except Exception as e:
            self.error.emit(str(e))