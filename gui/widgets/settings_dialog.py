from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QListWidget, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDoubleSpinBox, QLineEdit, QFileDialog, QFrame
)


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self._unit_change_callbacks: list = []
        self.setWindowTitle("პარამეტრები")
        self.setFixedSize(700, 450)
        self._create_ui()
        self._load()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setSpacing(0)
        body.setContentsMargins(0, 0, 0, 0)

        self.page_list = QListWidget()
        self.page_list.setObjectName("settingsSidebar")
        self.page_list.addItems(["ერთეული", "ხერხი", "შენახვის დირექტორია"])
        self.page_list.setFixedWidth(200)
        self.page_list.setFrameShape(QFrame.NoFrame)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_units())
        self.stack.addWidget(self._page_kerf())
        self.stack.addWidget(self._page_directory())

        self.page_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.page_list.setCurrentRow(0)

        body.addWidget(self.page_list)

        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setObjectName("settingsDivider")
        body.addWidget(div)

        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 10, 12, 0)
        btn_row.addStretch()
        self.save_btn = QPushButton("შენახვა")
        self.cancel_btn = QPushButton("გაუქმება")
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        root.addLayout(btn_row)

    def _page_units(self):
        page = QWidget()
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("გაზომვის ერთეული")
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)

        self.unit_combo = QComboBox()
        self.unit_combo.addItem("მილიმეტრი (მმ)", "mm")
        self.unit_combo.addItem("სანტიმეტრი (სმ)", "cm")
        self.unit_combo.setMaximumWidth(240)
        layout.addWidget(self.unit_combo)
        layout.addStretch()
        return page

    def _page_kerf(self):
        page = QWidget()
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("ხერხის სისქე")
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)

        layout.addWidget(QLabel("ყოველთვის მილიმეტრებში (მმ):"))

        self.kerf_spin = QDoubleSpinBox()
        self.kerf_spin.setMinimum(0.0)
        self.kerf_spin.setMaximum(50.0)
        self.kerf_spin.setDecimals(1)
        self.kerf_spin.setSingleStep(0.1)
        self.kerf_spin.setSuffix(" mm")
        self.kerf_spin.setMaximumWidth(100)
        layout.addWidget(self.kerf_spin)
        layout.addStretch()
        return page

    def _page_directory(self):
        page = QWidget()
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("პროექტების საქაღალდე")
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        self.dir_edit = QLineEdit()
        browse_btn = QPushButton("არჩევა…")
        browse_btn.setMaximumWidth(100)
        browse_btn.clicked.connect(self._browse)
        row.addWidget(self.dir_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)
        layout.addStretch()
        return page

    def _load(self):
        unit = self.settings.get("units", "mm")
        idx = self.unit_combo.findData(unit)
        self.unit_combo.blockSignals(True)
        self.unit_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.unit_combo.blockSignals(False)

        self.kerf_spin.setValue(float(self.settings.get("kerf", 4.4)))
        self.dir_edit.setText(str(self.settings.get("data_directory", "")))

    def _save(self):
        unit = self.unit_combo.currentData()
        self.settings.save(
            {
                "units": unit,
                "kerf": self.kerf_spin.value(),
                "data_directory": self.dir_edit.text(),
            }
        )
        for cb in self._unit_change_callbacks:
            cb(unit)
        self.accept()

    def register_unit_callback(self, callback):
        if callback not in self._unit_change_callbacks:
            self._unit_change_callbacks.append(callback)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(
            self, "არჩევა", self.dir_edit.text()
        )
        if path:
            self.dir_edit.setText(path)