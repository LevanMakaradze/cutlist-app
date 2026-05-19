from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QSplitter, QMessageBox,
    QGroupBox, QStackedWidget
)
from engine.models import PartSpec, SheetSpec, LayoutResult
from gui.widgets.layout.layout_worker import LayoutWorker
from gui.widgets.layout.sheet_visualizer import SheetVisualizer
from gui.widgets.layout.result_card import ResultCard


class LayoutPanel(QWidget):
    def __init__(
        self, settings_manager, project_panel, sheets_panel, parent=None
    ):
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

        self.selection_page = QWidget()
        self._init_selection_page()
        self.stacked_widget.addWidget(self.selection_page)

        self.loading_page = QWidget()
        self._init_loading_page()
        self.stacked_widget.addWidget(self.loading_page)

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
        title.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #1e293b;"
        )
        subtitle = QLabel(
            "ალგორითმების შედეგები დალაგებულია ეფექტურობის მიხედვით"
        )
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

        for lbl in [
            self.stat_algo,
            self.stat_sheets,
            self.stat_util,
            self.stat_cuts,
            self.stat_turns,
        ]:
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
        self.unplaced_scroll_layout = QVBoxLayout(
            self.unplaced_scroll_container
        )
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
        lbl = QLabel(
            "განლაგება არ არის გამოთვლილი.\n\nდააჭირეთ 'გაშვება / განახლება' შედეგების მისაღებად."
        )
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

            parts.append(
                PartSpec(
                    name=name,
                    width=int(length),
                    height=int(width),
                    quantity=qty,
                    can_rotate=not locked,
                )
            )
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

            sheets.append(
                SheetSpec(
                    name=name,
                    width=int(length),
                    height=int(width),
                    quantity=qty,
                )
            )
        return sheets

    def run_calculation(self):
        if self.worker and self.worker.isRunning():
            return

        parts = self._get_parts_from_gui()
        sheets = self._get_sheets_from_gui()

        if not sheets:
            QMessageBox.warning(
                self, "გაფრთხილება", "გთხოვთ, ჯერ აირჩიოთ მასალა!"
            )
            return

        if not parts:
            QMessageBox.warning(
                self, "გაფრთხილება", "გთხოვთ, შეიყვანოთ დეტალების ზომები!"
            )
            return

        self.run_btn.setEnabled(False)
        self.project_panel.generate_btn.setEnabled(False)
        self.stacked_widget.setCurrentIndex(1)

        settings = {"kerf": float(self.settings.get("kerf", 4.4))}

        self.worker = LayoutWorker(parts, sheets, settings)
        self.worker.finished.connect(self._on_calculation_finished)
        self.worker.error.connect(self._on_calculation_error)
        self.worker.start()

    def _on_calculation_finished(self, collection):
        self.results_collection = collection
        self._populate_results(collection)
        self.stacked_widget.setCurrentIndex(0)

        self.run_btn.setEnabled(True)
        self.project_panel.generate_btn.setEnabled(True)

    def _on_calculation_error(self, err_msg):
        self.stacked_widget.setCurrentIndex(0)
        self._show_placeholder()

        self.run_btn.setEnabled(True)
        self.project_panel.generate_btn.setEnabled(True)

        QMessageBox.critical(
            self, "გამოთვლის შეცდომა", f"ვერ მოხერხდა გამოთვლა: {err_msg}"
        )

    def _get_result_tier(
        self, result: LayoutResult, results: list[LayoutResult]
    ) -> str:
        if not results:
            return "green"

        unplaced_min = min(len(r.unplaced) for r in results)
        if len(result.unplaced) > unplaced_min:
            return "red"

        best_unplaced_results = [
            r for r in results if len(r.unplaced) == unplaced_min
        ]
        sheets_min = min(r.get_used_sheets() for r in best_unplaced_results)

        if result.get_used_sheets() > sheets_min + 1:
            return "red"
        elif result.get_used_sheets() == sheets_min + 1:
            return "yellow"
        else:
            best_with_sheets_min = [
                r
                for r in best_unplaced_results
                if r.get_used_sheets() == sheets_min
            ]
            cuts_list = [
                r.get_total_cut_difficulty().total_cuts
                for r in best_with_sheets_min
            ]
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
        self.details_title.setText(
            f"განლაგების დეტალები: {result.algorithm.upper()}"
        )

        difficulty = result.get_total_cut_difficulty()
        self.stat_algo.setText(f"<b>ალგორითმი:</b> {result.algorithm}")
        self.stat_sheets.setText(
            f"<b>გამოყენებული ფილები:</b> {result.get_used_sheets()} / {result.get_total_sheets()}"
        )
        self.stat_util.setText(
            f"<b>ათვისების კოეფიციენტი:</b> {result.get_total_utilization():.1f}%"
        )
        self.stat_cuts.setText(
            f"<b>გაჭრების რაოდენობა:</b> {difficulty.total_cuts}"
        )
        self.stat_turns.setText(
            f"<b>მიმართულების ცვლილება:</b> {difficulty.direction_changes}"
        )

        self._clear_layout(self.unplaced_scroll_layout)
        if result.unplaced:
            self.unplaced_group.setStyleSheet(
                "QGroupBox::title { color: #ef4444; }"
            )
            for part in result.unplaced:
                part_lbl = QLabel(
                    f"{part.get_label()} ({self._fmt_dim(part.width)} x {self._fmt_dim(part.height)})"
                )
                part_lbl.setObjectName("unplacedPartLabel")
                self.unplaced_scroll_layout.addWidget(part_lbl)
        else:
            self.unplaced_group.setStyleSheet(
                "QGroupBox::title { color: #16a34a; }"
            )
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
        QMessageBox.information(self, "ექსპორტი", "მონაცემები ექსპორტირებულია.")

    def set_unit(self, unit: str):
        self.unit = unit
        if self.current_result:
            self._display_result_details(self.current_result)
        if self.results_collection:
            self._populate_results(self.results_collection)