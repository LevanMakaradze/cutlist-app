from PySide6.QtCore import Qt, Signal, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QAbstractItemView,
    QLineEdit,
    QStyledItemDelegate,
)

INITIAL_ROWS = 25
ROW_GROW = 5


class TableDelegate(QStyledItemDelegate):
    def __init__(self, table_widget):
        super().__init__(table_widget)
        self.owner = table_widget

    def createEditor(self, parent,option, index):
        col_type = self.owner.columns[index.column()][1]

        if col_type == "check":
            return None

        editor = QLineEdit(parent)
        editor.setFrame(False)

        if col_type == "qty":
            rx = QRegularExpression(r"^\d{0,6}$")
            editor.setValidator(QRegularExpressionValidator(rx, editor))

        elif col_type == "dim":
            if self.owner._unit == "cm":
                rx = QRegularExpression(r"^\d{0,6}(\.\d?)?$")
            else:
                rx = QRegularExpression(r"^\d{0,7}$")

            editor.setValidator(QRegularExpressionValidator(rx, editor))

        return editor

    def setEditorData(self, editor, index):
        editor.setText(index.data() or "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())


class CustomTable(QWidget):
    modified = Signal()

    def __init__(self, columns):
        super().__init__()

        self.columns = columns
        self._unit = "mm"
        self.updating = False

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, len(columns) + 1)
        self.table.setHorizontalHeaderLabels(
            [name for name, _ in columns] + [""]
        )

        self.table.verticalHeader().setDefaultSectionSize(32)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.SelectedClicked
            | QAbstractItemView.AnyKeyPressed
        )

        header = self.table.horizontalHeader()

        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        header.setSectionResizeMode(
            len(columns),
            QHeaderView.Fixed,
        )

        self.table.setColumnWidth(len(columns), 36)

        self.table.setItemDelegate(
            TableDelegate(self)
        )

        layout.addWidget(self.table)

        self._refresh_headers()
        self.add_rows(INITIAL_ROWS)

        self.table.itemChanged.connect(
            self.on_item_changed
        )

    def add_rows(self, count):
        self.updating = True

        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._setup_row(row)

            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.setObjectName("rowClearButton")
            btn.clicked.connect(lambda checked=False, r=row: self.clear_row(r))
            self.table.setCellWidget(
                row,
                len(self.columns),
                btn,
            )

        self.updating = False

    def _setup_row(self, row):
        for col, (_, col_type) in enumerate(self.columns):
            if self.table.item(row, col) is not None:
                continue
            item = QTableWidgetItem()
            if col_type == "check":
                item.setFlags(
                    Qt.ItemIsEnabled
                    | Qt.ItemIsUserCheckable
                    | Qt.ItemIsSelectable
                )
                item.setCheckState(Qt.Unchecked)
                item.setTextAlignment(Qt.AlignCenter)
            else:
                item.setFlags(
                    Qt.ItemIsSelectable
                    | Qt.ItemIsEnabled
                    | Qt.ItemIsEditable
                )
            self.table.setItem(row, col, item)

    def row_has_data(self, row):
        for col, (_, col_type) in enumerate(self.columns):
            item = self.table.item(row, col)

            if not item:
                continue

            if col_type == "check":
                if item.checkState() == Qt.Checked:
                    return True
            else:
                if item.text().strip():
                    return True

        return False

    def on_item_changed(self, item):
        if self.updating:
            return

        self.modified.emit()

        last = self.table.rowCount() - 1

        if item.row() == last and self.row_has_data(last):
            self.add_rows(ROW_GROW)

    def clear_row(self, row):
        self.updating = True

        for col, (_, col_type) in enumerate(self.columns):
            item = self.table.item(row, col)

            if not item:
                continue

            if col_type == "check":
                item.setCheckState(Qt.Unchecked)
            else:
                item.setText("")

        self.updating = False
        self.modified.emit()
    
    def clear_all(self):
        """Clear all rows"""
        self.updating = True
        self.table.setRowCount(0)
        self.updating = False
        self.modified.emit()
        self.add_rows(INITIAL_ROWS)
   
    def set_unit(self, unit: str):
        """Switch display unit without changing the stored mm values."""
        if unit == self._unit:
            return
        old_unit = self._unit
        self._unit = unit
        self.updating = True
        for row in range(self.table.rowCount()):
            for col, (_, col_type) in enumerate(self.columns):
                if col_type != "dim":
                    continue
                item = self.table.item(row, col)
                if item is None or not item.text().strip():
                    continue
                try:
                    val_str = item.text().strip()
                    if old_unit == "mm":
                        mm_val = float(val_str)
                        new_str = f"{mm_val / 10:.1f}"
                    else:
                        cm_val = float(val_str)
                        new_str = str(int(round(cm_val * 10)))
                    item.setText(new_str)
                except ValueError:
                    pass
        self.updating = False
        self._refresh_headers()

    def _refresh_headers(self):
        headers = []
        for name, col_type in self.columns:
            if col_type == "dim":
                unit_label = "მმ" if self._unit == "mm" else "სმ"
                headers.append(f"{name} ({unit_label})")
            else:
                headers.append(name)
        headers.append("")
        self.table.setHorizontalHeaderLabels(headers)
    
    def get_data(self) -> list[dict]:
        """ returns data always in mm."""
        result = []
        for row in range(self.table.rowCount()):
            row_data = {}
            empty = True
            for col, (name, col_type) in enumerate(self.columns):
                item = self.table.item(row, col)
                if col_type == "check":
                    row_data[name] = bool(item and item.checkState() == Qt.Checked)
                elif col_type == "dim":
                    raw = item.text().strip() if item else ""
                    if raw:
                        empty = False
                        if self._unit == "cm":
                            try:
                                raw = str(int(round(float(raw) * 10)))
                            except ValueError:
                                pass
                    row_data[name] = raw
                else:
                    raw = item.text().strip() if item else ""
                    if raw:
                        empty = False
                    row_data[name] = raw
            if not empty:
                result.append(row_data)
        return result
    
    def set_data(self, data: list[dict]):
        """
        Load rows. Values for "dim" columns are expected in mm.(converted to cm if it is set)
        """
        self.updating = True
        self.table.setRowCount(0)
        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._setup_row(row)
            for col, (name, col_type) in enumerate(self.columns):
                if col_type == "check":
                    item = self.table.item(row, col)
                    if item is None:
                        item = QTableWidgetItem()
                        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)
                    item.setCheckState(Qt.Checked if row_data.get(name) else Qt.Unchecked)
                else:
                    raw = str(row_data.get(name, ""))
                    if col_type == "dim" and raw and self._unit == "cm":
                        try:
                            raw = f"{float(raw) / 10:.1f}"
                        except ValueError:
                            pass
                    item = QTableWidgetItem(raw)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    self.table.setItem(row, col, item)
            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.setObjectName("rowClearButton")
            btn.clicked.connect(lambda checked=False, r=row: self.clear_row(r))
            self.table.setCellWidget(row, len(self.columns), btn)
        # trailing empty rows
        for _ in range(max(5, INITIAL_ROWS - len(data))):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._setup_row(row)
            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.setObjectName("rowClearButton")
            btn.clicked.connect(lambda checked=False, r=row: self.clear_row(r))
            self.table.setCellWidget(row, len(self.columns), btn)
        self.updating = False