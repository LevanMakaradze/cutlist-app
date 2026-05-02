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
            if self.owner.unit == "cm":
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
        self.unit = "mm"
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

        self.add_rows(INITIAL_ROWS)

        self.table.itemChanged.connect(
            self.on_item_changed
        )

    def add_rows(self, count):
        self.updating = True

        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col, (_, col_type) in enumerate(self.columns):
                if col_type == "check":
                    item = QTableWidgetItem()
                    item.setFlags(
                        Qt.ItemIsEnabled
                        | Qt.ItemIsUserCheckable
                        | Qt.ItemIsSelectable
                    )
                    item.setCheckState(Qt.Unchecked)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)

            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.clicked.connect(lambda checked=False, r=row: self.clear_row(r))
            self.table.setCellWidget(
                row,
                len(self.columns),
                btn,
            )

        self.updating = False

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
        self._updating = True
        self.table.setRowCount(0)
        self._updating = False
        self.modified.emit()
        self.add_rows(INITIAL_ROWS)
   
    def set_unit(self, unit: str):
        """Switch display unit without changing the stored mm values."""
        if unit == self._unit:
            return
        old_unit  = self._unit
        self._unit = unit
        self._updating = True
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
        self._updating = False
        self._refresh_headers()