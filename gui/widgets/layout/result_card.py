from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QStyle, QStyleOption
)
from engine.models import LayoutResult


class ResultCard(QFrame):
    clicked = Signal(object)

    def __init__(self, result: LayoutResult, tier: str, parent=None):
        super().__init__(parent)
        self.result = result
        self.setObjectName("resultCard")
        self.setProperty("tier", tier)
        self.setAttribute(Qt.WA_StyledBackground, True)

        if tier == "green":
            tier_name = "საუკეთესო (რეკომენდირებული)"
        elif tier == "yellow":
            tier_name = "საშუალო"
        else:
            tier_name = "ცუდი"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        algo_label = QLabel(result.algorithm)
        algo_label.setObjectName("resultCardAlgo")
        algo_label.setProperty("tier", tier)
        algo_label.setWordWrap(True)
        header_layout.addWidget(algo_label, 1)

        badge = QLabel(tier_name)
        badge.setObjectName("resultCardBadge")
        badge.setProperty("tier", tier)
        header_layout.addWidget(badge, 0, Qt.AlignRight | Qt.AlignTop)
        layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("resultCardLine")
        line.setProperty("tier", tier)
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(6)

        def add_stat(row, label_text, val_text):
            lbl = QLabel(label_text)
            lbl.setObjectName("resultCardStatLabel")
            val = QLabel(val_text)
            val.setObjectName("resultCardStatValue")
            stats_layout.addWidget(lbl, row, 0, Qt.AlignLeft)
            stats_layout.addWidget(val, row, 1, Qt.AlignRight)

        difficulty = result.get_total_cut_difficulty()
        add_stat(
            0,
            "გამოყენებული ფილები:",
            f"{result.get_used_sheets()} / {result.get_total_sheets()}",
        )
        add_stat(1, "მასალის ათვისება:", f"{result.get_total_utilization():.1f}%")
        add_stat(
            2, "გაუნაწილებელი დეტალების რაოდენობა:", f"{len(result.unplaced)}"
        )
        add_stat(
            3,
            "გაჭრების რაოდენობა:",
            f"{difficulty.total_cuts} (მიმართულება: {difficulty.direction_changes})",
        )

        layout.addLayout(stats_layout)

        action_lbl = QLabel("დააკლიკეთ ნახაზის სანახავად")
        action_lbl.setObjectName("resultCardAction")
        action_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(action_lbl)

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.result)