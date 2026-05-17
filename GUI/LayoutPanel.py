# GUI/LayoutPanel.py
import sys
from pathlib import Path

# Add root folder to sys.path to allow imports from root directory under all execution contexts
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PySide6.QtCore import Qt, Signal, QThread, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QSplitter, QMessageBox,
    QGroupBox, QStackedWidget, QStyle, QStyleOption
)

from Models import PartSpec, SheetSpec, LayoutResult, LayoutResultCollection


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
            from App import run_all_parallel
            collection = run_all_parallel(self.parts, self.sheets, self.settings)
            self.finished.emit(collection)
        except Exception as e:
            self.error.emit(str(e))


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
        difficulty = self.sheet_layout.get_cut_difficulty()
        title = (
            f"{sheet.name} #{self.sheet_layout.sheet_number} | "
            f"cuts: {difficulty.total_cuts} | "
            f"turns: {difficulty.direction_changes} | "
            f"{self.sheet_layout.get_utilization():.1f}%"
        )
        painter.drawText(int(dx), int(dy - 8), title)

        sheet_rect = QRectF(dx, dy, drawn_w, drawn_h)
        painter.setPen(QPen(QColor("#475569"), 1.5))
        painter.setBrush(QBrush(QColor("#f8fafc")))
        painter.drawRect(sheet_rect)

        remaining_brush = QBrush(QColor("#B6B6B6"))
        remaining_pen = QPen(QColor("#383838"), 1, Qt.DashLine)

        for idx, remaining in enumerate(self.sheet_layout.remaining_parts, start=1):
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
                if placement.part.rotated:
                    label += " R"
                label += f"\n{self._fmt(placement.width)}x{self._fmt(placement.height)}"
                painter.drawText(p_rect, Qt.AlignCenter, label)


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

        # Header: Title + tier
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

        # Decorative line
        line = QFrame()
        line.setObjectName("resultCardLine")
        line.setProperty("tier", tier)
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

        # Stats info grid
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
        add_stat(0, "გამოყენებული ფილები:", f"{result.get_used_sheets()} / {result.get_total_sheets()}")
        add_stat(1, "მასალის ათვისება:", f"{result.get_total_utilization():.1f}%")
        add_stat(2, "გაუნაწილებელი დეტალების რაოდენობა:", f"{len(result.unplaced)}")
        add_stat(3, "გაჭრების რაოდენობა:", f"{difficulty.total_cuts} (მიმართულება: {difficulty.direction_changes})")

        layout.addLayout(stats_layout)

        # Hint at bottom
        action_lbl = QLabel("დააკლიკეთ ნახაზის სანახავად")
        action_lbl.setObjectName("resultCardAction")
        action_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(action_lbl)
        

    def paintEvent(self, event):
        """Ensures stylesheet backgrounds and borders paint correctly on custom QFrame subclasses."""
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.result)


class LayoutPanel(QWidget):
    def __init__(self, settings_manager, project_panel, sheets_panel, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.project_panel = project_panel
        self.sheets_panel = sheets_panel
        self.unit = self.settings.get("units", "mm")
        self.results_collection = None
        self.current_result = None
        self.worker = None

        self._create_ui()

    def _create_ui(self):
        self.stacked_widget = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_widget)

        # Page 0: Results Grid / Selection
        self.selection_page = QWidget()
        self._init_selection_page()
        self.stacked_widget.addWidget(self.selection_page)

        # Page 1: Loading Page
        self.loading_page = QWidget()
        self._init_loading_page()
        self.stacked_widget.addWidget(self.loading_page)

        # Page 2: Layout Details Page
        self.details_page = QWidget()
        self._init_details_page()
        self.stacked_widget.addWidget(self.details_page)

    def _init_selection_page(self):
        layout = QVBoxLayout(self.selection_page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("ავტომატური განლაგების ვარიანტები")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #1e293b;")
        subtitle = QLabel("ალგორითმების შედეგები დალაგებულია ეფექტურობის მიხედვით")
        subtitle.setStyleSheet("font-size: 10pt; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        top_bar.addLayout(title_layout)

        top_bar.addStretch()

        self.run_btn = QPushButton("გაშვება / განახლება")
        self.run_btn.setObjectName("generateButton")
        self.run_btn.clicked.connect(self.run_calculation)
        top_bar.addWidget(self.run_btn)
        layout.addLayout(top_bar)

        self.results_scroll = QScrollArea()
        self.results_scroll.setObjectName("resultsScrollArea")
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QFrame.NoFrame)

        self.results_container = QWidget()
        self.results_container.setObjectName("resultsContainer")
        self.results_grid = QGridLayout(self.results_container)
        self.results_grid.setSpacing(16)
        self.results_grid.setContentsMargins(8, 8, 8, 8)

        self.results_scroll.setWidget(self.results_container)
        layout.addWidget(self.results_scroll)

        self._show_placeholder()

    def _init_loading_page(self):
        layout = QVBoxLayout(self.loading_page)
        layout.setAlignment(Qt.AlignCenter)

        loading_frame = QFrame()
        loading_frame.setObjectName("loadingFrame")
        loading_frame.setAttribute(Qt.WA_StyledBackground, True)
        
        frame_layout = QVBoxLayout(loading_frame)
        frame_layout.setAlignment(Qt.AlignCenter)
        frame_layout.setSpacing(12)

        spinner_lbl = QLabel("⏳")
        spinner_lbl.setObjectName("loadingSpinner")
        spinner_lbl.setAlignment(Qt.AlignCenter)

        loading_title = QLabel("მიმდინარეობს ავტომატური განლაგება...")
        loading_title.setObjectName("loadingTitle")
        loading_title.setAlignment(Qt.AlignCenter)

        loading_desc = QLabel("გთხოვთ დაელოდოთ")
        loading_desc.setObjectName("loadingDesc")
        loading_desc.setAlignment(Qt.AlignCenter)

        frame_layout.addWidget(spinner_lbl)
        frame_layout.addWidget(loading_title)
        frame_layout.addWidget(loading_desc)

        layout.addWidget(loading_frame)

    def _init_details_page(self):
        layout = QVBoxLayout(self.details_page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        details_bar = QHBoxLayout()
        self.back_btn = QPushButton("ვარიანტებზე დაბრუნება")
        self.back_btn.setObjectName("backToSelectionButton")
        self.back_btn.clicked.connect(self._go_back_to_selection)
        details_bar.addWidget(self.back_btn)

        details_bar.addSpacing(16)

        self.details_title = QLabel("განლაგების დეტალური ნახაზი")
        self.details_title.setObjectName("detailsTitleLabel")
        details_bar.addWidget(self.details_title)

        details_bar.addStretch()
        layout.addLayout(details_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("sheetsScrollArea")
        scroll_area.setWidgetResizable(True)

        self.sheets_container = QWidget()
        self.sheets_grid = QGridLayout(self.sheets_container)
        self.sheets_grid.setSpacing(16)
        self.sheets_grid.setContentsMargins(12, 12, 12, 12)

        scroll_area.setWidget(self.sheets_container)
        left_layout.addWidget(scroll_area)
        splitter.addWidget(left_container)

        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(12)

        self.stats_group = QGroupBox("შედეგის პარამეტრები")
        stats_layout = QVBoxLayout(self.stats_group)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        stats_layout.setSpacing(8)

        self.stat_algo = QLabel()
        self.stat_sheets = QLabel()
        self.stat_util = QLabel()
        self.stat_cuts = QLabel()
        self.stat_turns = QLabel()

        for lbl in [self.stat_algo, self.stat_sheets, self.stat_util, self.stat_cuts, self.stat_turns]:
            lbl.setStyleSheet("font-size: 9.5pt; color: #1e293b;")
            stats_layout.addWidget(lbl)

        sidebar_layout.addWidget(self.stats_group)

        self.unplaced_group = QGroupBox("გაუნაწილებელი დეტალები")
        self.unplaced_layout = QVBoxLayout(self.unplaced_group)
        self.unplaced_layout.setContentsMargins(12, 12, 12, 12)
        self.unplaced_layout.setSpacing(6)

        self.unplaced_scroll = QScrollArea()
        self.unplaced_scroll.setWidgetResizable(True)
        self.unplaced_scroll.setFrameShape(QFrame.NoFrame)
        self.unplaced_scroll_container = QWidget()
        self.unplaced_scroll_layout = QVBoxLayout(self.unplaced_scroll_container)
        self.unplaced_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.unplaced_scroll_layout.setSpacing(4)
        self.unplaced_scroll.setWidget(self.unplaced_scroll_container)

        self.unplaced_layout.addWidget(self.unplaced_scroll)
        sidebar_layout.addWidget(self.unplaced_group)

        self.export_btn = QPushButton("მონაცემების ექსპორტი")
        self.export_btn.setObjectName("generateButton")
        self.export_btn.clicked.connect(self._on_export_clicked)
        sidebar_layout.addWidget(self.export_btn)

        sidebar_layout.addStretch()
        splitter.addWidget(self.sidebar)

    def _show_placeholder(self):
        self._clear_layout(self.results_grid)
        lbl = QLabel("განლაგება არ არის გამოთვლილი.\n\nდააჭირეთ 'გაშვება / განახლება' შედეგების მისაღებად.")
        lbl.setStyleSheet("font-size: 11pt; color: #64748b; font-weight: 500;")
        lbl.setAlignment(Qt.AlignCenter)
        self.results_grid.addWidget(lbl, 0, 0, Qt.AlignCenter)

    def _clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)

    def _get_parts_from_gui(self) -> list[PartSpec]:
        data = self.project_panel.table.get_data()
        parts = []
        for p in data:
            name = p.get("სახელი", "").strip()
            l_str = p.get("სიგრძე", "").strip()
            w_str = p.get("სიგანე", "").strip()
            q_str = p.get("რაოდენობა", "").strip()
            locked = p.get("ბრუნვა", False)

            if not name or not l_str or not w_str:
                continue
            try:
                length = float(l_str)
                width = float(w_str)
                qty = int(q_str) if q_str else 1
            except ValueError:
                continue

            parts.append(PartSpec(
                name=name,
                width=int(length),
                height=int(width),
                quantity=qty,
                can_rotate=not locked
            ))
        return parts

    def _get_sheets_from_gui(self) -> list[SheetSpec]:
        selected = self.project_panel._get_selected_sheets()
        sheets = []
        for s in selected:
            name = s.get("name", "").strip()
            l_str = s.get("length", "").strip()
            w_str = s.get("width", "").strip()
            q_str = s.get("qty", "").strip()

            if not name or not l_str or not w_str:
                continue
            try:
                length = float(l_str)
                width = float(w_str)
                qty = int(q_str) if q_str else 1
            except ValueError:
                continue

            sheets.append(SheetSpec(
                name=name,
                width=int(length),
                height=int(width),
                quantity=qty
            ))
        return sheets

    def run_calculation(self):
        # Prevent starting concurrent calculation threads
        if self.worker and self.worker.isRunning():
            return

        parts = self._get_parts_from_gui()
        sheets = self._get_sheets_from_gui()

        if not sheets:
            QMessageBox.warning(self, "გაფრთხილება", "გთხოვთ, ჯერ აირჩიოთ მასალა!")
            return

        if not parts:
            QMessageBox.warning(self, "გაფრთხილება", "გთხოვთ, შეიყვანოთ დეტალების ზომები!")
            return

        # Disable entry buttons during calculation to avoid collision and exit code 1
        self.run_btn.setEnabled(False)
        self.project_panel.generate_btn.setEnabled(False)

        self.stacked_widget.setCurrentIndex(1)

        settings = {
            "kerf": float(self.settings.get("kerf", 4.4))
        }

        self.worker = LayoutWorker(parts, sheets, settings)
        self.worker.finished.connect(self._on_calculation_finished)
        self.worker.error.connect(self._on_calculation_error)
        self.worker.start()

    def _on_calculation_finished(self, collection):
        self.results_collection = collection
        self._populate_results(collection)
        self.stacked_widget.setCurrentIndex(0)

        # Re-enable UI elements
        self.run_btn.setEnabled(True)
        self.project_panel.generate_btn.setEnabled(True)

    def _on_calculation_error(self, err_msg):
        self.stacked_widget.setCurrentIndex(0)
        self._show_placeholder()

        # Re-enable UI elements on failure
        self.run_btn.setEnabled(True)
        self.project_panel.generate_btn.setEnabled(True)

        QMessageBox.critical(self, "გამოთვლის შეცდომა", f"ვერ მოხერხდა გამოთვლა: {err_msg}")

    def _get_result_tier(self, result: LayoutResult, results: list[LayoutResult]) -> str:
        if not results:
            return "green"

        unplaced_min = min(len(r.unplaced) for r in results)
        if len(result.unplaced) > unplaced_min:
            return "red"

        best_unplaced_results = [r for r in results if len(r.unplaced) == unplaced_min]
        sheets_min = min(r.get_used_sheets() for r in best_unplaced_results)

        if result.get_used_sheets() > sheets_min + 1:
            return "red"
        elif result.get_used_sheets() == sheets_min + 1:
            return "yellow"
        else:
            best_with_sheets_min = [r for r in best_unplaced_results if r.get_used_sheets() == sheets_min]
            cuts_list = [r.get_total_cut_difficulty().total_cuts for r in best_with_sheets_min]
            if not cuts_list:
                return "green"
            cuts_min = min(cuts_list)
            cuts_max = max(cuts_list)

            my_cuts = result.get_total_cut_difficulty().total_cuts
            if cuts_max == cuts_min:
                return "green"

            threshold = cuts_min + 0.4 * (cuts_max - cuts_min)
            if my_cuts <= threshold:
                return "green"
            else:
                return "yellow"

    def _populate_results(self, collection):
        self._clear_layout(self.results_grid)

        if not collection or len(collection) == 0:
            self._show_placeholder()
            return

        results_list = list(collection)
        for idx, result in enumerate(results_list):
            tier = self._get_result_tier(result, results_list)
            card = ResultCard(result, tier, self)
            card.clicked.connect(self._on_result_card_clicked)

            row = idx // 3
            col = idx % 3
            self.results_grid.addWidget(card, row, col)

    def _on_result_card_clicked(self, result):
        self.current_result = result
        self._display_result_details(result)
        self.stacked_widget.setCurrentIndex(2)

    def _display_result_details(self, result: LayoutResult):
        self.details_title.setText(f"განლაგების დეტალები: {result.algorithm.upper()}")

        difficulty = result.get_total_cut_difficulty()
        self.stat_algo.setText(f"<b>ალგორითმი:</b> {result.algorithm}")
        self.stat_sheets.setText(f"<b>გამოყენებული ფილები:</b> {result.get_used_sheets()} / {result.get_total_sheets()}")
        self.stat_util.setText(f"<b>ათვისების კოეფიციენტი:</b> {result.get_total_utilization():.1f}%")
        self.stat_cuts.setText(f"<b>გაჭრების რაოდენობა:</b> {difficulty.total_cuts}")
        self.stat_turns.setText(f"<b>მიმართულების ცვლილება:</b> {difficulty.direction_changes}")

        self._clear_layout(self.unplaced_scroll_layout)
        if result.unplaced:
            self.unplaced_group.setStyleSheet("QGroupBox::title { color: #ef4444; }")
            for part in result.unplaced:
                part_lbl = QLabel(f"{part.get_label()} ({self._fmt_dim(part.width)} x {self._fmt_dim(part.height)})")
                part_lbl.setObjectName("unplacedPartLabel")
                self.unplaced_scroll_layout.addWidget(part_lbl)
        else:
            self.unplaced_group.setStyleSheet("QGroupBox::title { color: #16a34a; }")
            ok_lbl = QLabel("ყველა დეტალი წარმატებით განლაგდა!  ✅")
            ok_lbl.setObjectName("allPlacedLabel")
            self.unplaced_scroll_layout.addWidget(ok_lbl)

        self._clear_layout(self.sheets_grid)
        for idx, sheet_layout in enumerate(result.sheets):
            visualizer = SheetVisualizer(sheet_layout, unit=self.unit)
            row = idx // 2
            col = idx % 2
            self.sheets_grid.addWidget(visualizer, row, col)

    def _fmt_dim(self, mm_val: float) -> str:
        if self.unit == "cm":
            return f"{mm_val / 10:.1f} სმ"
        return f"{mm_val:g} მმ"

    def _go_back_to_selection(self):
        self.stacked_widget.setCurrentIndex(0)

    def _on_export_clicked(self):
        QMessageBox.information(self, "ექსპორტი", "")

    def set_unit(self, unit: str):
        self.unit = unit
        if self.current_result:
            self._display_result_details(self.current_result)
        if self.results_collection:
            self._populate_results(self.results_collection)