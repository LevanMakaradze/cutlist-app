from PySide6.QtCore import Qt, Signal, QRegularExpression, QEvent
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


class ExcelTableWidget(QTableWidget):
    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        # Selection state: If Enter is pressed when NOT editing, switch directly into edit mode
        if key in (Qt.Key_Return, Qt.Key_Enter):
            curr = self.currentIndex()
            if curr.isValid() and curr.column() < len(self.owner.columns):
                col_type = self.owner.columns[curr.column()][1]
                if col_type != "check":
                    self.edit(curr)
                    event.accept()
                    return

        # Selection state: Tab key commits and moves focus to the adjacent cell on the right
        if key == Qt.Key_Tab:
            curr = self.currentIndex()
            if curr.isValid():
                next_col = curr.column() + 1
                if next_col < len(self.owner.columns):
                    self.setCurrentIndex(self.model().index(curr.row(), next_col))
                else:
                    if curr.row() + 1 < self.rowCount():
                        self.setCurrentIndex(self.model().index(curr.row() + 1, 0))
                event.accept()
                return

        # Direct writing: Pressing a text key directly on a cell opens the editor instantly
        if text and text.isprintable() and len(text) == 1:
            if not (event.modifiers() & (Qt.ControlModifier | Qt.AltModifier)):
                curr = self.currentIndex()
                if curr.isValid() and curr.column() < len(self.owner.columns):
                    col_type = self.owner.columns[curr.column()][1]
                    if col_type != "check":
                        self.edit(curr)
                        editor = self.findChild(QLineEdit)
                        if editor:
                            editor.setText(text)
                            editor.setCursorPosition(1)
                        event.accept()
                        return

        super().keyPressEvent(event)


class TableDelegate(QStyledItemDelegate):
    def __init__(self, table_widget):
        super().__init__(table_widget)
        self.owner = table_widget

    def createEditor(self, parent, option, index):
        col_type = self.owner.columns[index.column()][1]

        if col_type == "check":
            return None

        editor = QLineEdit(parent)
        editor.setFrame(False)
        editor.installEventFilter(self)

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

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            
            # Pressing Enter while editing commits changes and closes editor (remaining on current cell)
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self.commitData.emit(editor)
                self.closeEditor.emit(editor)
                
                table = self.owner.table
                table.setFocus()
                return True

            # Pressing Tab while editing commits changes and transitions right
            elif key == Qt.Key_Tab:
                self.commitData.emit(editor)
                self.closeEditor.emit(editor)
                
                table = self.owner.table
                curr = table.currentIndex()
                if curr.isValid():
                    next_col = curr.column() + 1
                    if next_col < len(self.owner.columns):
                        table.setCurrentIndex(table.model().index(curr.row(), next_col))
                    else:
                        if curr.row() + 1 < table.rowCount():
                            table.setCurrentIndex(table.model().index(curr.row() + 1, 0))
                    table.setFocus()
                return True

            elif key == Qt.Key_Escape:
                self.closeEditor.emit(editor)
                self.owner.table.setFocus()
                return True

        return super().eventFilter(editor, event)


class CustomTable(QWidget):
    modified = Signal()

    def __init__(self, columns):
        super().__init__()
        self.columns = columns
        self._unit = "mm"
        self.updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Initialize the custom arrow and focus-friendly Excel-smooth table widget
        self.table = ExcelTableWidget(self, 0, len(columns) + 1)
        self.table.setHorizontalHeaderLabels(
            [name for name, _ in columns] + [""]
        )
        self.table.verticalHeader().setDefaultSectionSize(32)
        
        # Enable cell-by-cell selection 
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.SelectedClicked
            | QAbstractItemView.AnyKeyPressed
        )

        # Set checkbox column size style to be small and contents-fitting
        header = self.table.horizontalHeader()
        for i in range(len(columns)):
            col_type = columns[i][1]
            if col_type == "check":
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            else:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
        header.setSectionResizeMode(len(columns), QHeaderView.Fixed)
        rows = self.table.verticalHeader()
        rows.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(len(columns), 36)

        self.table.setItemDelegate(TableDelegate(self))
        layout.addWidget(self.table)

        self._refresh_headers()
        self.add_rows(INITIAL_ROWS)
        self.table.itemChanged.connect(self.on_item_changed)

    def add_rows(self, count):
        self.updating = True
        for _ in range(count):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._setup_row(row)

            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.setObjectName("rowClearButton")
            btn.clicked.connect(self._on_clear_row_clicked)
            self.table.setCellWidget(row, len(self.columns), btn)
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

    def _on_clear_row_clicked(self):
        button = self.sender()
        if not button:
            return
        # Dynamically lookup widget row coordinate to ensure safety against shifts
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, len(self.columns)) == button:
                self.clear_row_at(r)
                break

    def clear_row_at(self, row):
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
        self.updating = True
        self.table.setRowCount(0)
        self.updating = False
        self.modified.emit()
        self.add_rows(INITIAL_ROWS)

    def set_unit(self, unit: str):
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
        result = []
        for row in range(self.table.rowCount()):
            row_data = {}
            empty = True
            for col, (name, col_type) in enumerate(self.columns):
                item = self.table.item(row, col)
                if col_type == "check":
                    row_data[name] = bool(
                        item and item.checkState() == Qt.Checked
                    )
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
                        item.setFlags(
                            Qt.ItemIsEnabled
                            | Qt.ItemIsUserCheckable
                            | Qt.ItemIsSelectable
                        )
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)
                    item.setCheckState(
                        Qt.Checked
                        if row_data.get(name)
                        else Qt.Unchecked
                    )
                else:
                    raw = str(row_data.get(name, ""))
                    if col_type == "dim" and raw and self._unit == "cm":
                        try:
                            raw = f"{float(raw) / 10:.1f}"
                        except ValueError:
                            pass
                    item = QTableWidgetItem(raw)
                    item.setFlags(
                        Qt.ItemIsSelectable
                        | Qt.ItemIsEnabled
                        | Qt.ItemIsEditable
                    )
                    self.table.setItem(row, col, item)
            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.setObjectName("rowClearButton")
            btn.clicked.connect(self._on_clear_row_clicked)
            self.table.setCellWidget(row, len(self.columns), btn)

        for _ in range(max(5, INITIAL_ROWS - len(data))):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._setup_row(row)
            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.setObjectName("rowClearButton")
            btn.clicked.connect(self._on_clear_row_clicked)
            self.table.setCellWidget(row, len(self.columns), btn)
        self.updating = False