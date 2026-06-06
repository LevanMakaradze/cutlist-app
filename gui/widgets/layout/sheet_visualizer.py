from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import QWidget


class SheetVisualizer(QWidget):
    def __init__(self, sheet_layout, unit="mm", parent=None):
        super().__init__(parent)
        self.sheet_layout = sheet_layout
        self.unit = unit
        self.setMinimumSize(360, 260)

    def _fmt(self, val: float) -> str:
        if self.unit == "cm":
            return f"{val / 10:.1f}"
        return f"{val:g}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        margin = 25
        rect = self.rect().adjusted(margin, margin, -margin, -margin)

        # Zero dimension safety check
        if sheet.width <= 0 or sheet.height <= 0:
            painter.setPen(QColor("#ef4444"))
            painter.drawText(rect, Qt.AlignCenter, "არასწორი ზომის ფილა")
            return
        
        sheet = self.sheet_layout.sheet
        scale_x = rect.width() / sheet.width
        scale_y = rect.height() / sheet.height
        scale = min(scale_x, scale_y)

        drawn_w = sheet.width * scale
        drawn_h = sheet.height * scale
        dx = rect.left() + (rect.width() - drawn_w) / 2
        dy = rect.top() + (rect.height() - drawn_h) / 2

        painter.setPen(QColor("#1e293b"))
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)

        title = f"{sheet.name} #{self.sheet_layout.sheet_number}"
        painter.drawText(int(dx), int(dy - 8), title)

        sheet_rect = QRectF(dx, dy, drawn_w, drawn_h)
        painter.setPen(QPen(QColor("#475569"), 1.5))
        painter.setBrush(QBrush(QColor("#f8fafc")))
        painter.drawRect(sheet_rect)

        remaining_brush = QBrush(QColor("#B6B6B6"))
        remaining_pen = QPen(QColor("#383838"), 1, Qt.DashLine)

        for idx, remaining in enumerate(
            self.sheet_layout.remaining_parts, start=1
        ):
            rx = dx + remaining.x * scale
            ry = dy + remaining.y * scale
            rw = remaining.width * scale
            rh = remaining.height * scale
            r_rect = QRectF(rx, ry, rw, rh)

            painter.setPen(remaining_pen)
            painter.setBrush(remaining_brush)
            painter.drawRect(r_rect)

            if rw >= 45 and rh >= 25:
                painter.setPen(QColor("#000000"))
                painter.setFont(QFont("Segoe UI", 7.5))
                label = f"R{idx}\n{self._fmt(remaining.width)}x{self._fmt(remaining.height)}"
                painter.drawText(r_rect, Qt.AlignCenter, label)

        part_brush = QBrush(QColor("#bae6fd"))
        part_pen = QPen(QColor("#0284c7"), 1)

        for placement in self.sheet_layout.placements:
            px = dx + placement.x * scale
            py = dy + placement.y * scale
            pw = placement.width * scale
            ph = placement.height * scale
            p_rect = QRectF(px, py, pw, ph)

            painter.setPen(part_pen)
            painter.setBrush(part_brush)
            painter.drawRect(p_rect)

            if pw >= 35 and ph >= 18:
                painter.setPen(QColor("#0f172a"))
                painter.setFont(QFont("Segoe UI", 8))
                label = placement.part.get_label()
                label += f"\n{self._fmt(placement.width)}x{self._fmt(placement.height)}"
                painter.drawText(p_rect, Qt.AlignCenter, label)