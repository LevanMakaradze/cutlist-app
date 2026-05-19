"""
CheckableComboBox – a QComboBox where every item has a checkbox.
Usage:
    cb = CheckableComboBox()
    cb.addCheckItem("Sheet A")
    cb.addCheckItem("Sheet B", checked=True)
    checked = cb.checkedItems()   # list of display strings
    cb.setCheckedItems(["Sheet A"])
Signals:
    checkedItemsChanged(list[str])
"""
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui  import QStandardItem
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate


class _NoCloseDelegate(QStyledItemDelegate):
    """Prevent the popup closing on item click."""
    pass


class CheckableComboBox(QComboBox):
    checkedItemsChanged = Signal(list)   # emits list of checked strings

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(_NoCloseDelegate(self))
        self.view().pressed.connect(self._on_item_pressed)
        self._updating = False
        # placeholder text shown in the closed combo
        self._placeholder = "მასალა აირჩიეთ…"
        self._refresh_display()
        # block the built-in activated signal from closing popup
        self.view().viewport().installEventFilter(self)

    # ── event filter: keep popup open on click ────────────────────────────────

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            return True   # consume – we handle it via view.pressed
        return super().eventFilter(obj, event)

    # ── item management ───────────────────────────────────────────────────────

    def addCheckItem(self, text: str, checked: bool = False):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.model().appendRow(item)
        self._refresh_display()

    def clearItems(self):
        self.model().clear()
        self._refresh_display()

    def checkedItems(self) -> list[str]:
        result = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item and item.checkState() == Qt.Checked:
                result.append(item.text())
        return result

    def setCheckedItems(self, items: list[str]):
        self._updating = True
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item:
                item.setCheckState(
                    Qt.Checked if item.text() in items else Qt.Unchecked
                )
        self._updating = False
        self._refresh_display()

    def allItems(self) -> list[str]:
        return [
            self.model().item(i).text()
            for i in range(self.model().rowCount())
            if self.model().item(i)
        ]

    # ── internal ──────────────────────────────────────────────────────────────

    def _on_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item:
            new_state = (
                Qt.Unchecked
                if item.checkState() == Qt.Checked
                else Qt.Checked
            )
            item.setCheckState(new_state)
            self._refresh_display()
            if not self._updating:
                self.checkedItemsChanged.emit(self.checkedItems())

    def _refresh_display(self):
        checked = self.checkedItems()
        if checked:
            # show them joined; truncate if too long
            text = ", ".join(checked)
            if len(text) > 38:
                text = text[:35] + "…"
        else:
            text = self._placeholder
        # Block signals so we don't trigger currentIndexChanged noise
        self.blockSignals(True)
        # Use the line-edit approach: set custom text on closed combo
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setText(text)
        self.blockSignals(False)

    def setPlaceholder(self, text: str):
        self._placeholder = text
        self._refresh_display()