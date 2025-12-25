#!/usr/bin/env python3
"""
PyQt6 GUI for the YMS 4444 detector analysis.

This is the GUI/front-end layer. All heavy lifting (hitmaps, flux
computation, etc.) is in `data_processing.py`.
"""

from __future__ import annotations

import json
import os
import sys
import logging
from typing import List, Optional

import numpy as np

from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QPalette, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QDateEdit,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QGroupBox,
    QSizePolicy,
    QTabWidget,
    QCheckBox,
    QScrollArea,
    QGridLayout,
)

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure

from ncuhep.muography.classes import PlaneDetector, MuTxtFormat, AnalysisConfig
from ncuhep.muography.utils.tikhonov import tikhonov_smooth_neumann

from .data_processing import (
    filter_files,
    build_layer_geometry,
    compute_layer_pixel_mapping,
    compute_hitmaps_parallel,
    compute_flux_from_tracks,
)

logger = logging.getLogger("4444_gui")


class FocusAwareWheelMixin:
    """Allow scroll-wheel changes only when a widget is focused."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent wheel events from auto-focusing the widget; only clicks or tabbing
        # should provide focus so the wheel guard below remains effective.
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus | Qt.FocusPolicy.TabFocus)

    def wheelEvent(self, event):  # type: ignore[override]
        if not self.hasFocus():
            event.ignore()
            return
        super().wheelEvent(event)


class FocusSpinBox(FocusAwareWheelMixin, QSpinBox):
    pass


class FocusDoubleSpinBox(FocusAwareWheelMixin, QDoubleSpinBox):
    pass


class FocusDateEdit(FocusAwareWheelMixin, QDateEdit):
    pass


# ============================================================
#  QThread worker: hitmaps + raw flux
# ============================================================
class AnalysisWorker(QThread):
    finished = pyqtSignal(
        object, object, object, object, object, object, float, str, str
    )
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, int)  # percent, done, total

    def __init__(
            self,
            data_dir: str,
            config_dir: str,
            selected_mu_files: List[str],
            recon_path: str,
            fov_deg: float = 13.0,
            parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.data_dir = data_dir
        self.config_dir = config_dir
        self.selected_mu_files = selected_mu_files
        self.recon_path = recon_path
        self.fov_deg = fov_deg

    def _progress_cb(self, percent: int, done: int, total: int):
        self.progress.emit(percent, done, total)

    def run(self):
        logger.info(
            "AnalysisWorker.start: data_dir=%s config_dir=%s files=%d recon=%s",
            self.data_dir, self.config_dir, len(self.selected_mu_files), self.recon_path
        )
        try:
            (
                hits,
                events,
                tracks,
                det,
                summary_hits,
                _fails,
                tx_all,
                ty_all,
                live_time_total,
                total_tracks_global,
                total_rejected_global,
            ) = compute_hitmaps_parallel(
                self.data_dir,
                self.config_dir,
                self.selected_mu_files,
                max_workers=os.cpu_count() or 4,
                progress_callback=self._progress_cb,
            )

            flux_raw = None
            unc_raw = None
            unit_str = ""
            fov = self.fov_deg

            if tx_all is not None and tx_all.size > 0 and live_time_total > 0.0:
                logger.info(
                    "AnalysisWorker: computing flux from in-memory tracks "
                    "(N=%d, live_time=%.3fs)",
                    tx_all.size,
                    live_time_total,
                )
                flux_raw, unc_raw, fov, unit_str, summary_flux_core = compute_flux_from_tracks(
                    tx_all,
                    ty_all,
                    live_time_total,
                    self.recon_path,
                    fov_deg=self.fov_deg,
                )
                summary_flux = (
                    f"{summary_flux_core} | tracks_total={total_tracks_global}, "
                    f"rejected={total_rejected_global}"
                )
            else:
                summary_flux = "Flux: no tracks or zero live time for selected runs."
                logger.info("AnalysisWorker: %s", summary_flux)

            summary_all = summary_hits + " | " + summary_flux
            logger.info("AnalysisWorker finished summary: %s", summary_all)

            self.finished.emit(
                hits, events, tracks, det, flux_raw, unc_raw, fov, unit_str, summary_all
            )

        except Exception as e:
            logger.exception("AnalysisWorker.run exception")
            self.error.emit(f"{type(e).__name__}: {e}")


# ============================================================
#  PyQt GUI
# ============================================================
class HitMapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("HitMapWindow.__init__")
        self.setWindowTitle("Muon Detector Config + Analysis")
        self.resize(1400, 900)

        # Data holders
        self.counts_hits: Optional[List[np.ndarray]] = None
        self.counts_events: Optional[List[np.ndarray]] = None
        self.counts_tracks: Optional[List[np.ndarray]] = None
        self.det: Optional[PlaneDetector] = None

        self.flux_base_array: Optional[np.ndarray] = None
        self.unc_base_array: Optional[np.ndarray] = None
        self.flux_array: Optional[np.ndarray] = None
        self.uncertainty_array: Optional[np.ndarray] = None
        self.flux_fov_deg: float = 13.0
        self.flux_unit_str: str = ""

        self.reg_hx = 0.001
        self.reg_hy = 0.001

        self.default_config_path = os.path.join(
            os.path.expanduser("~"), ".ncuhep_muography_config.json"
        )
        self.current_theme: str = "dark"

        self.worker: Optional[AnalysisWorker] = None

        # Generate-config widget refs
        self.gen_config_dir_edit: QLineEdit
        self.mu_format_folder_edit: QLineEdit
        self.det_pix_fp_x: QDoubleSpinBox
        self.det_pix_fp_y: QDoubleSpinBox
        self.det_pix_fp_z: QDoubleSpinBox
        self.det_pix_act_x: QDoubleSpinBox
        self.det_pix_act_y: QDoubleSpinBox
        self.det_pix_act_z: QDoubleSpinBox
        self.layer_z_edit: QLineEdit
        self.event_thr_spin: QSpinBox
        self.hit_thr_spin: QSpinBox
        self.max_total_spin: QSpinBox
        self.max_per_layer_edit: QLineEdit
        self.flip_x_boxes: List[List[QCheckBox]] = []
        self.flip_y_boxes: List[List[QCheckBox]] = []
        self.layer_count_spin: QSpinBox
        self.ch_per_board_x_spin: QSpinBox
        self.ch_per_board_y_spin: QSpinBox
        self.boards_x_spins: List[QSpinBox] = []
        self.boards_y_spins: List[QSpinBox] = []
        self.boards_layer_layout = None
        self.flip_x_layout = None
        self.flip_y_layout = None
        self.layer_flip_layout = None
        self.layer_flip_x_checks: List[QCheckBox] = []
        self.layer_flip_y_checks: List[QCheckBox] = []

        # Matplotlib canvases (Processing)
        self.raw_hits_canvas: Optional[FigureCanvas] = None
        self.selected_hits_canvas: Optional[FigureCanvas] = None
        self.tracked_hits_canvas: Optional[FigureCanvas] = None
        self.flux_canvas: Optional[FigureCanvas] = None
        self.unc_canvas: Optional[FigureCanvas] = None

        # Mapping preview canvases (Generate Config)
        self.mapping_tabwidget: Optional[QTabWidget] = None
        self.mapping_canvases: List[FigureCanvas] = []
        self.latest_layer_maps: Optional[List[np.ndarray]] = None
        self.latest_layer_ids: Optional[np.ndarray] = None

        self._build_menu_bar()

        # Central widget with tabs
        central = QWidget()
        self.setCentralWidget(central)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.setSpacing(8)

        self.tabs = QTabWidget()
        central_layout.addWidget(self.tabs)

        # Generate Config tab
        self.config_scroll = QScrollArea()
        self.config_scroll.setWidgetResizable(True)
        self.config_page = QWidget()
        self.config_scroll.setWidget(self.config_page)
        self.tabs.addTab(self.config_scroll, "Generate Config")
        self._build_generate_config_tab()

        # Processing tab
        self.processing_tab = QWidget()
        self.tabs.addTab(self.processing_tab, "Processing")
        self._build_processing_tab()

        self.load_default_settings(initial=True)
        self._apply_minimal_style()

    # ========================================================
    #  Menu + configuration helpers
    # ========================================================
    def _apply_minimal_style(self):
        """Apply a clean, spacious style to the widgets."""

        self.setStyleSheet(
            """
            QWidget { font-size: 11.5pt; }
            QGroupBox {
                border: 1px solid #4c4c4c;
                border-radius: 8px;
                margin-top: 8px;
                padding: 10px 12px 12px 12px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }

            QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
                padding: 4px 6px;
                min-height: 25px;
            }

            QPushButton {
                padding: 8px 14px;
                border-radius: 7px;
                border: 1px solid palette(mid);
                background-color: palette(button);
                color: palette(button-text);
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
            QPushButton:disabled {
                color: palette(mid);
                background-color: palette(button);
                border: 1px solid palette(mid);
            }
            QTabWidget::pane { border: 0; }
            QLabel { font-size: 11pt; }
            """
        )

    def _build_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        save_cfg_action = QAction("Save Processing Config…", self)
        save_cfg_action.triggered.connect(self.save_processing_config)
        load_cfg_action = QAction("Load Processing Config…", self)
        load_cfg_action.triggered.connect(self.load_processing_config)
        file_menu.addAction(save_cfg_action)
        file_menu.addAction(load_cfg_action)

        settings_menu = menubar.addMenu("&Settings")
        save_default_action = QAction("Save as Default", self)
        save_default_action.triggered.connect(self.save_default_settings)
        load_default_action = QAction("Load Default", self)
        load_default_action.triggered.connect(self.load_default_settings)
        settings_menu.addAction(save_default_action)
        settings_menu.addAction(load_default_action)
        settings_menu.addSeparator()

        theme_menu = settings_menu.addMenu("Theme")
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)

        self.light_theme_action = QAction("Light", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(self.light_theme_action)
        self.theme_action_group.addAction(self.light_theme_action)

        self.dark_theme_action = QAction("Dark", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.setChecked(True)
        self.dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(self.dark_theme_action)
        self.theme_action_group.addAction(self.dark_theme_action)

    def _gather_processing_settings(self) -> dict:
        mode_index = self.filter_mode_combo.currentIndex()
        mode = "date" if mode_index == 0 else "run"
        settings = {
            "data_dir": self.data_dir_edit.text().strip(),
            "config_dir": self.config_dir_edit.text().strip(),
            "recon_path": self.recon_file_edit.text().strip(),
            "filter_mode": mode,
            "start_date": self.start_date_edit.date().toString(Qt.DateFormat.ISODate),
            "end_date": self.end_date_edit.date().toString(Qt.DateFormat.ISODate),
            "run_start": self.run_start_spin.value(),
            "run_end": self.run_end_spin.value(),
            "lambda": self.lambda_spin.value(),
            "theme": self.current_theme,
        }
        return settings

    def _apply_processing_settings(self, settings: dict):
        self.data_dir_edit.setText(settings.get("data_dir", ""))
        self.config_dir_edit.setText(settings.get("config_dir", ""))
        self.recon_file_edit.setText(settings.get("recon_path", ""))

        mode = settings.get("filter_mode", "date")
        if mode == "date":
            self.filter_mode_combo.setCurrentIndex(0)
        else:
            self.filter_mode_combo.setCurrentIndex(1)
        self.update_filter_mode()

        start_date_str = settings.get("start_date")
        end_date_str = settings.get("end_date")
        if start_date_str:
            self.start_date_edit.setDate(QDate.fromString(start_date_str, Qt.DateFormat.ISODate))
        if end_date_str:
            self.end_date_edit.setDate(QDate.fromString(end_date_str, Qt.DateFormat.ISODate))

        self.run_start_spin.setValue(int(settings.get("run_start", self.run_start_spin.value())))
        self.run_end_spin.setValue(int(settings.get("run_end", self.run_end_spin.value())))
        self.lambda_spin.setValue(float(settings.get("lambda", self.lambda_spin.value())))

        theme = settings.get("theme")
        if theme:
            self.set_theme(theme)

    def save_processing_config(self):
        settings = self._gather_processing_settings()
        fname, _ = QFileDialog.getSaveFileName(
            self,
            "Save processing configuration",
            "processing_config.json",
            "JSON files (*.json);;All files (*)",
        )
        if not fname:
            return

        try:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(self, "Saved", f"Saved processing settings to:\n{fname}")
        except Exception as exc:
            logger.exception("Failed to save processing config")
            QMessageBox.warning(self, "Save error", f"Could not save configuration:\n{exc}")

    def load_processing_config(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Load processing configuration",
            "processing_config.json",
            "JSON files (*.json);;All files (*)",
        )
        if not fname:
            return

        try:
            with open(fname, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self._apply_processing_settings(settings)
            QMessageBox.information(self, "Loaded", f"Loaded processing settings from:\n{fname}")
        except Exception as exc:
            logger.exception("Failed to load processing config")
            QMessageBox.warning(self, "Load error", f"Could not load configuration:\n{exc}")

    def save_default_settings(self):
        settings = self._gather_processing_settings()
        try:
            with open(self.default_config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(
                self,
                "Default saved",
                f"Saved default settings to:\n{self.default_config_path}",
            )
        except Exception as exc:
            logger.exception("Failed to save default settings")
            QMessageBox.warning(self, "Save error", f"Could not save default settings:\n{exc}")

    def load_default_settings(self, initial: bool = False):
        if not os.path.exists(self.default_config_path):
            if not initial:
                QMessageBox.information(
                    self,
                    "No default",
                    "No default settings found. Save one from Settings → Save as Default.",
                )
            return

        try:
            with open(self.default_config_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self._apply_processing_settings(settings)
            if not initial:
                QMessageBox.information(
                    self,
                    "Loaded default",
                    f"Loaded default settings from:\n{self.default_config_path}",
                )
        except Exception as exc:
            logger.exception("Failed to load default settings")
            if not initial:
                QMessageBox.warning(self, "Load error", f"Could not load default settings:\n{exc}")
            else:
                self.status_label.setText("Failed to load default settings")

    def set_theme(self, theme: str):
        theme = theme.lower()
        if theme not in ("light", "dark"):
            theme = "dark"

        app = QApplication.instance()
        if app is None:
            return

        if theme == self.current_theme:
            if theme == "dark":
                self.dark_theme_action.setChecked(True)
            else:
                self.light_theme_action.setChecked(True)
            return

        if theme == "dark":
            apply_dark_theme(app)
            self.dark_theme_action.setChecked(True)
        else:
            apply_light_theme(app)
            self.light_theme_action.setChecked(True)

        self.current_theme = theme
        self.refresh_plots_for_theme()

    def refresh_plots_for_theme(self):
        self._plot_layer_maps(self.raw_hits_canvas, self.counts_hits, "Raw Hits")
        self._plot_layer_maps(self.selected_hits_canvas, self.counts_events, "Selected Hits")
        self._plot_layer_maps(self.tracked_hits_canvas, self.counts_tracks, "Tracked Hits")
        self._plot_flux(self.flux_canvas, self.flux_array, "Flux", f"Flux ({self.flux_unit_str})")
        self._plot_flux(
            self.unc_canvas,
            self.uncertainty_array,
            "Flux Uncertainty",
            f"Uncertainty ({self.flux_unit_str})",
        )

        if self.latest_layer_maps is not None:
            self.update_mapping_layers(self.latest_layer_maps, self.latest_layer_ids)

    # ========================================================
    #  Plotting helpers (theme-aware)
    # ========================================================
    def _style_figure(self, fig: Figure):
        if self.current_theme == "dark":
            fig.patch.set_facecolor("#232323")
        else:
            fig.patch.set_facecolor("white")

    def _style_axes(self, ax):
        if self.current_theme == "dark":
            face = "#232323"
            fg = "white"
        else:
            face = "white"
            fg = "black"

        ax.set_facecolor(face)
        for spine in ax.spines.values():
            spine.set_color(fg)
        ax.tick_params(colors=fg)
        ax.title.set_color(fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)

    def _style_colorbar(self, cbar):
        if self.current_theme == "dark":
            face = "#232323"
            fg = "white"
        else:
            face = "white"
            fg = "black"

        cbar.ax.set_facecolor(face)
        cbar.ax.yaxis.label.set_color(fg)

        cbar.outline.set_edgecolor(fg)
        cbar.outline.set_linewidth(0.8)

        for t in cbar.ax.get_yticklabels():
            t.set_color(fg)

    # ========================================================
    #  Processing tab UI  (two-column layout)
    # ========================================================
    def _build_processing_tab(self):
        layout = QVBoxLayout(self.processing_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # --- Top area: two columns (left = controls, right = outputs) ---
        top_split = QHBoxLayout()
        top_split.setContentsMargins(0, 0, 0, 0)
        top_split.setSpacing(20)
        layout.addLayout(top_split)

        # LEFT COLUMN ----------------------------------------------------
        left_widget = QWidget()
        left_col = QVBoxLayout(left_widget)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(10)
        left_widget.setMaximumWidth(700)

        # Paths group
        path_group = QGroupBox("Paths")
        path_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        path_layout = QFormLayout(path_group)
        path_layout.setVerticalSpacing(8)
        path_layout.setHorizontalSpacing(10)

        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setPlaceholderText("Select data folder containing *_Mu.txt …")
        browse_data_btn = QPushButton("Browse…")
        browse_data_btn.clicked.connect(self.browse_data_dir)
        h_data = QHBoxLayout()
        h_data.setSpacing(8)
        h_data.addWidget(self.data_dir_edit)
        h_data.addWidget(browse_data_btn)

        self.config_dir_edit = QLineEdit("config4444-2")
        browse_cfg_btn = QPushButton("Browse…")
        browse_cfg_btn.clicked.connect(self.browse_config_dir)
        h_cfg = QHBoxLayout()
        h_cfg.setSpacing(8)
        h_cfg.addWidget(self.config_dir_edit)
        h_cfg.addWidget(browse_cfg_btn)

        self.recon_file_edit = QLineEdit("4444.npz")
        browse_recon_btn = QPushButton("Browse…")
        browse_recon_btn.clicked.connect(self.browse_recon_file)
        h_recon = QHBoxLayout()
        h_recon.setSpacing(8)
        h_recon.addWidget(self.recon_file_edit)
        h_recon.addWidget(browse_recon_btn)

        path_layout.addRow("Data folder:", h_data)
        path_layout.addRow("Config folder:", h_cfg)
        path_layout.addRow("Recon file:", h_recon)
        left_col.addWidget(path_group)

        # Filter group
        filter_group = QGroupBox("Filter")
        filter_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(8, 8, 8, 8)

        self.filter_mode_combo = QComboBox()
        self.filter_mode_combo.addItems(["Date range", "Run range"])
        self.filter_mode_combo.currentIndexChanged.connect(self.update_filter_mode)

        self.start_date_edit = FocusDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = FocusDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        today = QDate.currentDate()
        self.start_date_edit.setDate(today)
        self.end_date_edit.setDate(today)

        self.date_range_box = QWidget()
        date_layout = QHBoxLayout(self.date_range_box)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)
        date_layout.addWidget(QLabel("Start:"))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QLabel("End:"))
        date_layout.addWidget(self.end_date_edit)

        self.run_start_spin = FocusSpinBox()
        self.run_start_spin.setRange(0, 999999)
        self.run_start_spin.setValue(0)
        self.run_end_spin = FocusSpinBox()
        self.run_end_spin.setRange(0, 999999)
        self.run_end_spin.setValue(999999)

        self.run_range_box = QWidget()
        run_layout = QHBoxLayout(self.run_range_box)
        run_layout.setContentsMargins(0, 0, 0, 0)
        run_layout.setSpacing(8)
        run_layout.addWidget(QLabel("Run from:"))
        run_layout.addWidget(self.run_start_spin)
        run_layout.addWidget(QLabel("to"))
        run_layout.addWidget(self.run_end_spin)

        filter_layout.addWidget(QLabel("Mode:"))
        filter_layout.addWidget(self.filter_mode_combo)
        filter_layout.addStretch(1)
        filter_layout.addWidget(self.date_range_box)
        filter_layout.addWidget(self.run_range_box)
        left_col.addWidget(filter_group)
        self.update_filter_mode()

        # Controls row (λ, buttons)
        ctrl_group = QGroupBox("Analysis Control")
        ctrl_layout = QHBoxLayout(ctrl_group)
        ctrl_layout.setSpacing(12)
        ctrl_layout.setContentsMargins(8, 8, 8, 8)

        self.lambda_spin = FocusDoubleSpinBox()
        self.lambda_spin.setDecimals(4)
        self.lambda_spin.setRange(0, 1000.0)
        self.lambda_spin.setSingleStep(0.001)
        self.lambda_spin.setValue(0)

        self.lambda_btn = QPushButton("Apply λ")
        self.lambda_btn.clicked.connect(self.apply_lambda)

        self.run_btn = QPushButton("Run analysis")
        self.run_btn.clicked.connect(self.run_analysis)

        self.save_flux_btn = QPushButton("Save Flux Arrays…")
        self.save_flux_btn.clicked.connect(self.save_flux_arrays)

        ctrl_layout.addWidget(QLabel("Tikhonov λ:"))
        ctrl_layout.addWidget(self.lambda_spin)
        ctrl_layout.addWidget(self.lambda_btn)
        ctrl_layout.addStretch(1)
        ctrl_layout.addWidget(self.save_flux_btn)
        ctrl_layout.addWidget(self.run_btn)

        left_col.addWidget(ctrl_group)
        left_col.addStretch(1)

        # RIGHT COLUMN ---------------------------------------------------
        right_widget = QWidget()
        right_col = QVBoxLayout(right_widget)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(10)

        # Status label (single-line, at top)
        self.status_label = QLabel("")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        right_col.addWidget(self.status_label)

        # Info box with summary text
        info_box = QGroupBox("Data summary")
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(8, 8, 8, 8)
        self.info_label = QLabel(
            "Hitmaps and flux are kept in memory.\n"
            "Shapes and other debug info will appear here."
        )
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        right_col.addWidget(info_box)

        right_col.addStretch(1)

        # Add both columns to top_split
        top_split.addWidget(left_widget, stretch=3)
        top_split.addWidget(right_widget, stretch=2)

        # --- Plots (full width) ----------------------------------------
        self.plot_tabs = QTabWidget()
        self.plot_tabs.setTabPosition(QTabWidget.TabPosition.North)
        layout.addWidget(self.plot_tabs, stretch=1)

        self.raw_hits_canvas = self._add_plot_tab("Raw Hits")
        self.selected_hits_canvas = self._add_plot_tab("Selected Hits")
        self.tracked_hits_canvas = self._add_plot_tab("Tracked Hits")
        self.flux_canvas = self._add_plot_tab("Flux")
        self.unc_canvas = self._add_plot_tab("Flux Uncertainty")

    def _add_plot_tab(self, title: str) -> FigureCanvas:
        tab = QWidget()
        v = QVBoxLayout(tab)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(6)

        # Slightly larger than default but not so large that the grid overflows
        fig = Figure(figsize=(7.5, 7.5), dpi=110)
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        toolbar = NavigationToolbar(canvas, tab)
        v.addWidget(toolbar)
        v.addWidget(canvas)

        self.plot_tabs.addTab(tab, title)
        self._style_figure(fig)
        return canvas

    # ========================================================
    #  Generate Config tab UI
    # ========================================================
    def _build_generate_config_tab(self):
        layout = QVBoxLayout(self.config_page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(22)

        # Config Output
        cfg_group = QGroupBox("Config Output")
        cfg_layout = QFormLayout(cfg_group)
        cfg_layout.setVerticalSpacing(10)
        cfg_layout.setHorizontalSpacing(12)
        cfg_layout.setContentsMargins(12, 12, 12, 12)
        cfg_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.gen_config_dir_edit = QLineEdit("config4444-2")
        browse_cfg_btn = QPushButton("Browse…")
        browse_cfg_btn.clicked.connect(self.browse_gen_config_dir)
        h_cfg = QHBoxLayout()
        h_cfg.setSpacing(10)
        h_cfg.addWidget(self.gen_config_dir_edit)
        h_cfg.addWidget(browse_cfg_btn)

        # This is a *file* (CSV), not a folder
        self.mu_format_folder_edit = QLineEdit("mu_txt_format.csv")

        cfg_layout.addRow("Config folder:", h_cfg)
        cfg_layout.addRow("Mu txt format (CSV):", self.mu_format_folder_edit)
        layout.addWidget(cfg_group)

        # Two-column layout
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(26)
        layout.addLayout(cols_layout)

        left_col_widget = QWidget()
        right_col_widget = QWidget()
        left_col = QVBoxLayout(left_col_widget)
        right_col = QVBoxLayout(right_col_widget)
        left_col.setContentsMargins(0, 0, 0, 0)
        right_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(12)
        right_col.setSpacing(12)

        cols_layout.addWidget(left_col_widget, stretch=1)
        cols_layout.addWidget(right_col_widget, stretch=1)

        # LEFT: Detector Geometry
        det_group = QGroupBox("Detector Geometry (variable layers / boards)")
        det_layout = QFormLayout(det_group)
        det_layout.setVerticalSpacing(10)
        det_layout.setHorizontalSpacing(12)
        det_layout.setContentsMargins(12, 12, 12, 12)
        det_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.layer_count_spin = FocusSpinBox()
        self.layer_count_spin.setRange(1, 16)
        self.layer_count_spin.setValue(4)
        self.layer_count_spin.valueChanged.connect(self.on_layer_count_changed)

        self.ch_per_board_x_spin = FocusSpinBox()
        self.ch_per_board_y_spin = FocusSpinBox()
        for s in (self.ch_per_board_x_spin, self.ch_per_board_y_spin):
            s.setRange(1, 64)
            s.setValue(4)

        ch_row = QHBoxLayout()
        ch_row.setSpacing(10)
        ch_row.addWidget(QLabel("X"))
        ch_row.addWidget(self.ch_per_board_x_spin)
        ch_row.addWidget(QLabel("Y"))
        ch_row.addWidget(self.ch_per_board_y_spin)
        ch_row.addStretch(1)

        self.det_pix_fp_x = FocusDoubleSpinBox()
        self.det_pix_fp_y = FocusDoubleSpinBox()
        self.det_pix_fp_z = FocusDoubleSpinBox()
        for s in (self.det_pix_fp_x, self.det_pix_fp_y, self.det_pix_fp_z):
            s.setRange(0.1, 1000.0)
            s.setDecimals(2)
        self.det_pix_fp_x.setValue(50.0)
        self.det_pix_fp_y.setValue(50.0)
        self.det_pix_fp_z.setValue(12.0)

        fp_row = QHBoxLayout()
        fp_row.setSpacing(10)
        fp_row.addWidget(QLabel("X"))
        fp_row.addWidget(self.det_pix_fp_x)
        fp_row.addWidget(QLabel("Y"))
        fp_row.addWidget(self.det_pix_fp_y)
        fp_row.addWidget(QLabel("Z"))
        fp_row.addWidget(self.det_pix_fp_z)
        fp_row.addStretch(1)

        self.det_pix_act_x = FocusDoubleSpinBox()
        self.det_pix_act_y = FocusDoubleSpinBox()
        self.det_pix_act_z = FocusDoubleSpinBox()
        for s in (self.det_pix_act_x, self.det_pix_act_y, self.det_pix_act_z):
            s.setRange(0.1, 1000.0)
            s.setDecimals(2)
        self.det_pix_act_x.setValue(49.0)
        self.det_pix_act_y.setValue(49.0)
        self.det_pix_act_z.setValue(12.0)

        act_row = QHBoxLayout()
        act_row.setSpacing(10)
        act_row.addWidget(QLabel("X"))
        act_row.addWidget(self.det_pix_act_x)
        act_row.addWidget(QLabel("Y"))
        act_row.addWidget(self.det_pix_act_y)
        act_row.addWidget(QLabel("Z"))
        act_row.addWidget(self.det_pix_act_z)
        act_row.addStretch(1)

        self.layer_z_edit = QLineEdit("-750,-250,250,750")

        det_layout.addRow("Layer count:", self.layer_count_spin)
        det_layout.addRow("Channels per board:", ch_row)
        det_layout.addRow("Pixel footprint (mm):", fp_row)
        det_layout.addRow("Pixel actual (mm):", act_row)
        det_layout.addRow("Layer Z positions (mm):", self.layer_z_edit)
        left_col.addWidget(det_group)

        boards_group = QGroupBox("Boards per Layer")
        boards_group_layout = QVBoxLayout(boards_group)
        boards_group_layout.setSpacing(10)
        boards_group_layout.setContentsMargins(12, 12, 12, 12)

        self.boards_layer_layout = QVBoxLayout()
        self.boards_layer_layout.setSpacing(8)
        boards_group_layout.addLayout(self.boards_layer_layout)
        left_col.addWidget(boards_group)

        # Mapping group with per-layer tabs
        mapping_group = QGroupBox("Detector Mapping Preview (UNIQUEID)")
        mapping_layout = QVBoxLayout(mapping_group)
        mapping_layout.setContentsMargins(8, 8, 8, 8)

        self.mapping_tabwidget = QTabWidget()
        mapping_layout.addWidget(self.mapping_tabwidget)

        left_col.addWidget(mapping_group)
        left_col.addStretch(1)

        # RIGHT: flips + analysis
        layer_flips_group = QGroupBox("Layer Flips (per layer)")
        self.layer_flip_layout = QVBoxLayout(layer_flips_group)
        self.layer_flip_layout.setContentsMargins(12, 12, 12, 12)
        self.layer_flip_layout.setSpacing(8)
        right_col.addWidget(layer_flips_group)

        flips_group = QGroupBox("Board Flips (per board)")
        flips_group_layout = QHBoxLayout(flips_group)
        flips_group_layout.setSpacing(12)
        flips_group_layout.setContentsMargins(12, 12, 12, 12)

        group_x = QGroupBox("Board Flip X")
        self.flip_x_layout = QVBoxLayout(group_x)
        self.flip_x_layout.setSpacing(8)
        group_y = QGroupBox("Board Flip Y")
        self.flip_y_layout = QVBoxLayout(group_y)
        self.flip_y_layout.setSpacing(8)

        flips_group_layout.addWidget(group_x)
        flips_group_layout.addWidget(group_y)
        right_col.addWidget(flips_group)

        ana_group = QGroupBox("Analysis Settings")
        ana_layout = QFormLayout(ana_group)
        ana_layout.setVerticalSpacing(10)
        ana_layout.setHorizontalSpacing(12)
        ana_layout.setContentsMargins(12, 12, 12, 12)
        ana_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.event_thr_spin = FocusSpinBox()
        self.event_thr_spin.setRange(0, 10000)
        self.event_thr_spin.setValue(75)

        self.hit_thr_spin = FocusSpinBox()
        self.hit_thr_spin.setRange(0, 10000)
        self.hit_thr_spin.setValue(75)

        self.max_total_spin = FocusSpinBox()
        self.max_total_spin.setRange(1, 1000)
        self.max_total_spin.setValue(8)

        self.max_per_layer_edit = QLineEdit("3,3,3,2")

        ana_layout.addRow("Event threshold:", self.event_thr_spin)
        ana_layout.addRow("Hit threshold:", self.hit_thr_spin)
        ana_layout.addRow("Max total hits:", self.max_total_spin)
        ana_layout.addRow("Max per layer:", self.max_per_layer_edit)

        right_col.addWidget(ana_group)
        right_col.addStretch(1)

        # Buttons: Load + Generate
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.addStretch(1)

        load_btn = QPushButton("Load Config")
        load_btn.clicked.connect(self.load_config)
        btn_layout.addWidget(load_btn)

        gen_btn = QPushButton("Generate Config")
        gen_btn.clicked.connect(self.generate_config)
        btn_layout.addWidget(gen_btn)

        layout.addLayout(btn_layout)

        self.rebuild_boards_rows()
        self.rebuild_layer_flips()
        self.rebuild_flip_boxes()

    # ---------------- Dynamic boards / flips / layer flips ----------------
    def on_layer_count_changed(self, value: int):
        logger.debug("Layer count changed to %d", value)
        self.rebuild_boards_rows()
        self.rebuild_layer_flips()
        self.rebuild_flip_boxes()

    def rebuild_boards_rows(self):
        while self.boards_layer_layout.count():
            item = self.boards_layer_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self.boards_x_spins.clear()
        self.boards_y_spins.clear()

        n_layers = self.layer_count_spin.value()
        for i in range(n_layers):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            row_layout.addWidget(QLabel(f"Layer {i + 1}:"))
            bx_spin = FocusSpinBox()
            by_spin = FocusSpinBox()
            for s in (bx_spin, by_spin):
                s.setRange(1, 16)
                s.setValue(2)
                s.valueChanged.connect(self.rebuild_flip_boxes)

            row_layout.addWidget(QLabel("Bx"))
            row_layout.addWidget(bx_spin)
            row_layout.addWidget(QLabel("By"))
            row_layout.addWidget(by_spin)
            row_layout.addStretch(1)

            self.boards_layer_layout.addWidget(row_widget)
            self.boards_x_spins.append(bx_spin)
            self.boards_y_spins.append(by_spin)

    def rebuild_layer_flips(self):
        if self.layer_flip_layout is None:
            return

        while self.layer_flip_layout.count():
            item = self.layer_flip_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self.layer_flip_x_checks = []
        self.layer_flip_y_checks = []

        n_layers = self.layer_count_spin.value()
        for i in range(n_layers):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            lbl = QLabel(f"Layer {i + 1}:")
            cbx = QCheckBox("Flip X")
            cby = QCheckBox("Flip Y")

            cbx.setChecked(True)
            cby.setChecked(False)

            row_layout.addWidget(lbl)
            row_layout.addWidget(cbx)
            row_layout.addWidget(cby)
            row_layout.addStretch(1)

            self.layer_flip_layout.addWidget(row_widget)
            self.layer_flip_x_checks.append(cbx)
            self.layer_flip_y_checks.append(cby)

    def rebuild_flip_boxes(self):
        def clear_layout(lay: QVBoxLayout):
            while lay.count():
                item = lay.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        clear_layout(self.flip_x_layout)
        clear_layout(self.flip_y_layout)

        self.flip_x_boxes = []
        self.flip_y_boxes = []

        n_layers = self.layer_count_spin.value()

        for layer in range(n_layers):
            bx = self.boards_x_spins[layer].value()
            by = self.boards_y_spins[layer].value()
            nboards = bx * by

            group_x = QGroupBox(f"Layer {layer + 1}")
            grid_x = QGridLayout(group_x)
            grid_x.setContentsMargins(4, 4, 4, 4)
            grid_x.setHorizontalSpacing(4)
            grid_x.setVerticalSpacing(4)
            layer_boxes_x: List[QCheckBox] = []

            idx = 0
            for j in range(by):
                for i in range(bx):
                    cb = QCheckBox(f"{idx + 1}")
                    cb.setChecked(False)
                    grid_x.addWidget(cb, j, i)
                    layer_boxes_x.append(cb)
                    idx += 1

            self.flip_x_layout.addWidget(group_x)
            self.flip_x_boxes.append(layer_boxes_x)

            group_y = QGroupBox(f"Layer {layer + 1}")
            grid_y = QGridLayout(group_y)
            grid_y.setContentsMargins(4, 4, 4, 4)
            grid_y.setHorizontalSpacing(4)
            grid_y.setVerticalSpacing(4)
            layer_boxes_y: List[QCheckBox] = []

            idx = 0
            for j in range(by):
                for i in range(bx):
                    cb = QCheckBox(f"{idx + 1}")
                    cb.setChecked(False)
                    grid_y.addWidget(cb, j, i)
                    layer_boxes_y.append(cb)
                    idx += 1

            self.flip_y_layout.addWidget(group_y)
            self.flip_y_boxes.append(layer_boxes_y)

    # ========================================================
    #  UI helpers (both tabs)
    # ========================================================
    def browse_data_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select data folder",
            "",
        )
        if directory:
            logger.info("User selected data_dir=%s", directory)
            self.data_dir_edit.setText(directory)

    def browse_config_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select config folder",
            "",
        )
        if directory:
            logger.info("User selected config_dir=%s", directory)
            self.config_dir_edit.setText(directory)

    def browse_recon_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select recon .npz file",
            "",
            "NPZ files (*.npz);;All files (*)",
        )
        if filename:
            logger.info("User selected recon_file=%s", filename)
            self.recon_file_edit.setText(filename)

    def browse_gen_config_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select config output folder",
            "",
        )
        if directory:
            logger.info("User selected config output dir=%s", directory)
            self.gen_config_dir_edit.setText(directory)

    def update_filter_mode(self):
        mode_index = self.filter_mode_combo.currentIndex()
        logger.info("Filter mode changed to index=%d", mode_index)
        if mode_index == 0:
            self.date_range_box.show()
            self.run_range_box.hide()
        else:
            self.date_range_box.hide()
            self.run_range_box.show()

    # ========================================================
    #  Generate Config: LOAD
    # ========================================================
    def load_config(self):
        """
        Load existing detector_config.json and analysis_config.json
        from the folder in gen_config_dir_edit and populate the UI.
        """
        logger.info("Load Config clicked")
        cfg_dir = self.gen_config_dir_edit.text().strip()
        if not cfg_dir or not os.path.isdir(cfg_dir):
            cfg_dir_dialog = QFileDialog.getExistingDirectory(
                self, "Select existing config folder", "", )
            if not cfg_dir_dialog:
                return
            cfg_dir = cfg_dir_dialog
            self.gen_config_dir_edit.setText(cfg_dir)

        detector_config_path = os.path.join(cfg_dir, "detector_config.json")
        analysis_config_path = os.path.join(cfg_dir, "analysis_config.json")
        mutxt_config_path = os.path.join(cfg_dir, "mutxt_config.json")

        if not os.path.isfile(detector_config_path):
            QMessageBox.warning(
                self, "Load Config",
                f"detector_config.json not found in:\n{cfg_dir}"
            )
            return
        if not os.path.isfile(analysis_config_path):
            QMessageBox.warning(
                self, "Load Config",
                f"analysis_config.json not found in:\n{cfg_dir}"
            )
            return

        try:
            logger.info("Loading PlaneDetector from %s", detector_config_path)
            det = PlaneDetector()
            det._import(detector_config_path)

            logger.info("Loading AnalysisConfig from %s", analysis_config_path)
            ana = AnalysisConfig()
            ana._import(analysis_config_path)
        except Exception as e:
            logger.exception("Error loading config")
            QMessageBox.critical(
                self, "Load Config", f"Error loading config:\n{type(e).__name__}: {e}"
            )
            return

        # --- Populate detector settings ---
        try:
            layer_count = int(det.layer_count)
            self.layer_count_spin.blockSignals(True)
            self.layer_count_spin.setValue(layer_count)
            self.layer_count_spin.blockSignals(False)
            self.rebuild_boards_rows()
            self.rebuild_layer_flips()
            self.rebuild_flip_boxes()

            # Channels per board
            self.ch_per_board_x_spin.setValue(int(det.channels_per_board_x))
            self.ch_per_board_y_spin.setValue(int(det.channels_per_board_y))

            # Pixel footprint / actual (mm)
            self.det_pix_fp_x.setValue(float(det.pixel_footprint_length_x.mm))
            self.det_pix_fp_y.setValue(float(det.pixel_footprint_length_y.mm))
            self.det_pix_fp_z.setValue(float(det.pixel_footprint_length_z.mm))

            self.det_pix_act_x.setValue(float(det.pixel_actual_length_x.mm))
            self.det_pix_act_y.setValue(float(det.pixel_actual_length_y.mm))
            self.det_pix_act_z.setValue(float(det.pixel_actual_length_z.mm))

            # Layer Z positions
            z_vals = [str(float(z)) for z in det.layer_z.mm]
            self.layer_z_edit.setText(",".join(z_vals))

            # Boards per layer
            boards_per_layer_x = np.asarray(det.boards_per_layer_x, dtype=int)
            boards_per_layer_y = np.asarray(det.boards_per_layer_y, dtype=int)
            for i in range(layer_count):
                if i < len(self.boards_x_spins):
                    self.boards_x_spins[i].setValue(int(boards_per_layer_x[i]))
                if i < len(self.boards_y_spins):
                    self.boards_y_spins[i].setValue(int(boards_per_layer_y[i]))

            # Rebuild flip boxes so board counts match loaded geometry
            self.rebuild_flip_boxes()

            # Layer flips
            layer_flip_x = np.asarray(det.layer_flip_x, dtype=int)
            layer_flip_y = np.asarray(det.layer_flip_y, dtype=int)
            for i in range(layer_count):
                if i < len(self.layer_flip_x_checks):
                    self.layer_flip_x_checks[i].setChecked(bool(layer_flip_x[i] == 1))
                if i < len(self.layer_flip_y_checks):
                    self.layer_flip_y_checks[i].setChecked(bool(layer_flip_y[i] == 1))

            # Board flips
            board_flip_x = np.asarray(det.board_flip_x, dtype=int)
            board_flip_y = np.asarray(det.board_flip_y, dtype=int)
            boards_per_layer = np.asarray(det.boards_per_layer, dtype=int)
            val = 0
            for layer in range(layer_count):
                nboards = int(boards_per_layer[layer])
                for k in range(nboards):
                    if layer < len(self.flip_x_boxes) and k < len(self.flip_x_boxes[layer]):
                        self.flip_x_boxes[layer][k].setChecked(bool(board_flip_x[val] == 1))
                    if layer < len(self.flip_y_boxes) and k < len(self.flip_y_boxes[layer]):
                        self.flip_y_boxes[layer][k].setChecked(bool(board_flip_y[val] == 1))
                    val += 1

            # Optionally try to guess mu_txt CSV name from mutxt_config
            if os.path.isfile(mutxt_config_path):
                try:
                    logger.info("Loading MuTxtFormat from %s", mutxt_config_path)
                    mutxt = MuTxtFormat()
                    mutxt._import(mutxt_config_path)
                    csv_guess = getattr(mutxt, "path", None) or getattr(mutxt, "filename", None)
                    if csv_guess:
                        self.mu_format_folder_edit.setText(os.path.basename(csv_guess))
                except Exception:
                    logger.exception("Error reading mutxt_config; ignoring")

            # --- Populate analysis settings ---
            self.event_thr_spin.setValue(int(ana.event_threshold))
            self.hit_thr_spin.setValue(int(ana.hit_threshold))
            self.max_total_spin.setValue(int(ana.max_total))
            if hasattr(ana, "max_per_layer"):
                mpl = np.asarray(ana.max_per_layer, dtype=int)
                self.max_per_layer_edit.setText(",".join(str(int(x)) for x in mpl))

            # Update mapping preview
            try:
                layer_maps = compute_layer_pixel_mapping(det)
                self.update_mapping_layers(layer_maps, det.layer_id)
            except Exception:
                logger.exception("Error computing mapping preview in load_config")

            # Also set config folder in Processing tab
            self.config_dir_edit.setText(cfg_dir)

            QMessageBox.information(
                self,
                "Config loaded",
                f"Loaded config from:\n{cfg_dir}",
            )
        except Exception as e:
            logger.exception("Error populating GUI from loaded config")
            QMessageBox.critical(
                self,
                "Load Config",
                f"Config loaded, but GUI population failed:\n{type(e).__name__}: {e}",
            )

    # ========================================================
    #  Generate Config: GENERATE
    # ========================================================
    def generate_config(self):
        logger.info("Generate Config clicked")
        cfg_dir = self.gen_config_dir_edit.text().strip()
        if not cfg_dir:
            QMessageBox.warning(self, "Config", "Please specify a config folder.")
            return

        try:
            os.makedirs(cfg_dir, exist_ok=True)
            logger.debug("Ensured config folder exists: %s", cfg_dir)
        except Exception as e:
            logger.exception("Cannot create config folder %s", cfg_dir)
            QMessageBox.warning(self, "Config", f"Cannot create config folder:\n{e}")
            return

        layer_count = self.layer_count_spin.value()
        logger.debug("Generating config for layer_count=%d", layer_count)

        # --- layer Z ---
        try:
            layer_z_text = self.layer_z_edit.text().strip()
            z_vals = [float(x.strip()) for x in layer_z_text.split(",") if x.strip()]
            if len(z_vals) != layer_count:
                raise ValueError(f"Need exactly {layer_count} layer Z values.")
            layer_z = np.array(z_vals, dtype=np.float64)
            logger.debug("Parsed layer_z=%s", layer_z)
        except Exception as e:
            logger.exception("Error parsing layer Z positions")
            QMessageBox.warning(self, "Detector", f"Error parsing layer Z positions:\n{e}")
            return

        # --- boards per layer ---
        boards_per_layer_x_vals = [self.boards_x_spins[i].value() for i in range(layer_count)]
        boards_per_layer_y_vals = [self.boards_y_spins[i].value() for i in range(layer_count)]
        boards_per_layer_x = np.array(boards_per_layer_x_vals, dtype=np.int64)
        boards_per_layer_y = np.array(boards_per_layer_y_vals, dtype=np.int64)
        boards_per_layer = boards_per_layer_x * boards_per_layer_y
        logger.debug(
            "boards_per_layer_x=%s, boards_per_layer_y=%s, boards_per_layer=%s",
            boards_per_layer_x, boards_per_layer_y, boards_per_layer
        )

        # --- max_per_layer ---
        try:
            mpl_text = self.max_per_layer_edit.text().strip()
            mpl_vals = [int(x.strip()) for x in mpl_text.split(",") if x.strip()]
            if len(mpl_vals) != layer_count:
                raise ValueError(f"Max per layer must have exactly {layer_count} entries.")
            max_per_layer_arr = np.array(mpl_vals, dtype=np.int64)
            logger.debug("max_per_layer=%s", max_per_layer_arr)
        except Exception as e:
            logger.exception("Error parsing max per layer")
            QMessageBox.warning(self, "Analysis", f"Error parsing max per layer:\n{e}")
            return

        # --- layer flips ---
        if len(self.layer_flip_x_checks) != layer_count or len(self.layer_flip_y_checks) != layer_count:
            logger.error("Layer flip control size mismatch")
            QMessageBox.warning(
                self,
                "Layer flips",
                "Internal layer flip control size mismatch. Try changing layer count again.",
            )
            return

        layer_flip_x = np.array(
            [1 if cb.isChecked() else 0 for cb in self.layer_flip_x_checks],
            dtype=np.int64,
        )
        layer_flip_y = np.array(
            [1 if cb.isChecked() else 0 for cb in self.layer_flip_y_checks],
            dtype=np.int64,
        )
        logger.debug("layer_flip_x=%s, layer_flip_y=%s", layer_flip_x, layer_flip_y)

        # --- board flips ---
        board_flip_x: List[int] = []
        board_flip_y: List[int] = []
        for layer in range(layer_count):
            bx = boards_per_layer_x[layer]
            by = boards_per_layer_y[layer]
            nboards = bx * by

            if len(self.flip_x_boxes[layer]) != nboards or len(self.flip_y_boxes[layer]) != nboards:
                logger.error("Board flip matrix size mismatch at layer %d", layer + 1)
                QMessageBox.warning(
                    self,
                    "Flips",
                    f"Internal board flip matrix size mismatch at layer {layer + 1}. "
                    "Try adjusting boards per layer again.",
                )
                return

            for k in range(nboards):
                board_flip_x.append(1 if self.flip_x_boxes[layer][k].isChecked() else 0)
                board_flip_y.append(1 if self.flip_y_boxes[layer][k].isChecked() else 0)

        board_flip_x = np.array(board_flip_x, dtype=np.int64)
        board_flip_y = np.array(board_flip_y, dtype=np.int64)
        board_counts = int(boards_per_layer.sum())
        logger.debug(
            "board_flip_x len=%d, board_flip_y len=%d, board_counts=%d",
            len(board_flip_x), len(board_flip_y), board_counts
        )

        # --- PlaneDetector ---
        logger.info("Building PlaneDetector object")
        det = PlaneDetector()

        det.pixel_footprint_length_x.mm = self.det_pix_fp_x.value()
        det.pixel_footprint_length_y.mm = self.det_pix_fp_y.value()
        det.pixel_footprint_length_z.mm = self.det_pix_fp_z.value()

        det.pixel_actual_length_x.mm = self.det_pix_act_x.value()
        det.pixel_actual_length_y.mm = self.det_pix_act_y.value()
        det.pixel_actual_length_z.mm = self.det_pix_act_z.value()

        chx = self.ch_per_board_x_spin.value()
        chy = self.ch_per_board_y_spin.value()
        det.channels_per_board_x = chx
        det.channels_per_board_y = chy
        det.channels_per_board = chx * chy

        det.boards_per_layer_x = boards_per_layer_x
        det.boards_per_layer_y = boards_per_layer_y
        det.boards_per_layer = boards_per_layer

        det.layer_z.mm = layer_z
        det.layer_id = np.arange(1, layer_count + 1, dtype=np.int64)
        det.layer_count = layer_count

        det.board_flip_x = board_flip_x
        det.board_flip_y = board_flip_y
        det.board_flip_z = 0

        det.layer_flip_x = layer_flip_x
        det.layer_flip_y = layer_flip_y

        pixel_count_x = chx * boards_per_layer_x
        pixel_count_y = chy * boards_per_layer_y
        pixel_count = pixel_count_x * pixel_count_y

        det.pixel_count_per_layer_x = pixel_count_x.astype(np.int64)
        det.pixel_count_per_layer_y = pixel_count_y.astype(np.int64)
        det.pixel_count_per_layer = pixel_count.astype(np.int64)

        det.board_counts = board_counts

        det.detector_half_length_x.mm = np.ones(layer_count, dtype=np.float64) * 200.0
        det.detector_half_length_y.mm = np.ones(layer_count, dtype=np.float64) * 200.0

        detector_config_path = os.path.join(cfg_dir, "detector_config.json")
        logger.info("Calling det._export(%s)", detector_config_path)
        det._export(detector_config_path)
        logger.info("det._export finished")

        # --- AnalysisConfig ---
        ana = AnalysisConfig()
        ana.event_threshold = self.event_thr_spin.value()
        ana.hit_threshold = self.hit_thr_spin.value()
        ana.layer_id = det.layer_id.copy()
        ana.max_per_layer = max_per_layer_arr
        ana.max_total = self.max_total_spin.value()

        analysis_config_path = os.path.join(cfg_dir, "analysis_config.json")
        logger.info("Calling ana._export(%s)", analysis_config_path)
        ana._export(analysis_config_path)
        logger.info("ana._export finished")

        # --- MuTxtFormat as CSV FILE ---
        mutxt = MuTxtFormat()

        mu_format_path = self.mu_format_folder_edit.text().strip() or "mu_txt_format.csv"

        if not os.path.isabs(mu_format_path):
            mu_format_path = os.path.join(cfg_dir, mu_format_path)

        parent_dir = os.path.dirname(mu_format_path) or cfg_dir
        try:
            os.makedirs(parent_dir, exist_ok=True)
            logger.debug("Ensured parent dir for mu_txt_format: %s", parent_dir)
        except Exception as e:
            logger.exception("Cannot create parent dir for mu_txt_format %s", mu_format_path)
            QMessageBox.warning(self, "MuTxtFormat", f"Cannot create parent dir:\n{e}")
            return

        logger.info("Calling mutxt._generate(%s)", mu_format_path)
        mutxt._generate(mu_format_path)
        logger.info("mutxt._generate finished")

        mutxt_config_path = os.path.join(cfg_dir, "mutxt_config.json")
        logger.info("Calling mutxt._export(%s)", mutxt_config_path)
        mutxt._export(mutxt_config_path)
        logger.info("mutxt._export finished")

        # Mapping preview with UNIQUEID labels (per-layer tabs)
        try:
            layer_maps = compute_layer_pixel_mapping(det)
            self.update_mapping_layers(layer_maps, det.layer_id)
        except Exception:
            logger.exception("Error computing mapping preview")

        # Also point the Processing tab's config folder here
        self.config_dir_edit.setText(cfg_dir)

        QMessageBox.information(
            self,
            "Config generated",
            f"Generated:\n- {detector_config_path}\n- {analysis_config_path}\n"
            f"- {mutxt_config_path}\n- {mu_format_path}",
        )

    def update_mapping_layers(self, layer_maps: List[np.ndarray], layer_ids: np.ndarray):
        """
        Show one plot per layer, each in its own tab in the Generate Config pane.
        """
        self.latest_layer_maps = layer_maps
        self.latest_layer_ids = layer_ids

        if self.mapping_tabwidget is None:
            return

        self.mapping_tabwidget.clear()
        self.mapping_canvases.clear()

        if not layer_maps:
            tab = QWidget()
            v = QVBoxLayout(tab)
            v.setContentsMargins(6, 6, 6, 6)
            lbl = QLabel("No mapping to display. Generate or load a config first.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(lbl)
            self.mapping_tabwidget.addTab(tab, "Mapping")
            return

        vmin = min(float(np.min(m)) for m in layer_maps)
        vmax = max(float(np.max(m)) for m in layer_maps)
        if vmax == vmin:
            vmax = vmin + 1.0

        for idx, img in enumerate(layer_maps):
            lid = int(layer_ids[idx]) if layer_ids is not None and idx < len(layer_ids) else (idx + 1)

            tab = QWidget()
            v = QVBoxLayout(tab)
            v.setContentsMargins(4, 4, 4, 4)
            v.setSpacing(4)

            # Keep previews comfortably sized but allow narrower layouts to breathe
            fig = Figure(figsize=(5.6, 5.5), dpi=110)
            canvas = FigureCanvas(fig)
            self._style_figure(fig)
            canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            canvas.setMinimumSize(460, 460)
            canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

            toolbar = NavigationToolbar(canvas, tab)

            toolbar_box = QHBoxLayout()
            toolbar_box.setContentsMargins(0, 0, 0, 0)
            toolbar_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            toolbar_box.addWidget(toolbar)

            canvas_box = QHBoxLayout()
            canvas_box.setContentsMargins(0, 0, 0, 0)
            canvas_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            canvas_box.addWidget(canvas)

            v.addLayout(toolbar_box)
            v.addLayout(canvas_box)

            ax = fig.add_subplot(111)
            self._style_axes(ax)
            im = ax.imshow(
                img,
                cmap="coolwarm",
                vmin=vmin,
                vmax=vmax,
                aspect="equal",
                interpolation="nearest",
            )

            ny, nx = img.shape
            for y in range(ny):
                for x in range(nx):
                    text_color = "white" if self.current_theme == "dark" else "black"
                    ax.text(
                        x,
                        y,
                        str(int(img[y, x])),
                        ha="center",
                        va="center",
                        fontsize=7,
                        color=text_color,
                    )

            ax.set_title(
                f"Layer {lid}",
                fontsize=11,
                color="white" if self.current_theme == "dark" else "black",
            )
            ax.set_xticks([])
            ax.set_yticks([])

            fig.subplots_adjust(left=0.06, right=0.86, top=0.9, bottom=0.08)
            cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.06)
            self._style_colorbar(cbar)

            canvas.draw_idle()
            self.mapping_canvases.append(canvas)
            self.mapping_tabwidget.addTab(tab, f"Layer {lid}")

    # ========================================================
    #  Processing logic
    # ========================================================
    def run_analysis(self):
        logger.info("Run analysis clicked")
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Analysis running", "An analysis is already running.")
            return

        data_dir = self.data_dir_edit.text().strip()
        config_dir = self.config_dir_edit.text().strip()
        recon_path = self.recon_file_edit.text().strip()

        if not data_dir or not os.path.isdir(data_dir):
            logger.error("Invalid data folder: %s", data_dir)
            QMessageBox.warning(self, "Invalid data folder", "Please select a valid data folder.")
            return

        if not config_dir or not os.path.isdir(config_dir):
            logger.error("Invalid config folder: %s", config_dir)
            QMessageBox.warning(self, "Invalid config folder", "Please select a valid config folder.")
            return

        if not recon_path or not os.path.isfile(recon_path):
            logger.error("Invalid recon file: %s", recon_path)
            QMessageBox.warning(self, "Invalid recon file", "Please select a valid recon .npz file.")
            return

        all_files = [f for f in os.listdir(data_dir) if f.endswith("_Mu.txt")]
        all_files.sort()
        logger.info("Found %d *_Mu.txt files", len(all_files))
        if not all_files:
            QMessageBox.warning(self, "No files", "No *_Mu.txt files found in the selected data folder.")
            return

        mode_index = self.filter_mode_combo.currentIndex()
        if mode_index == 0:
            mode = "date"
            sd = self.start_date_edit.date().toPyDate()
            ed = self.end_date_edit.date().toPyDate()
            selected_files = filter_files(all_files, mode, start_date=sd, end_date=ed)
            filter_desc = f"Date {sd} → {ed}"
        else:
            mode = "run"
            rs = self.run_start_spin.value()
            re_ = self.run_end_spin.value()
            selected_files = filter_files(all_files, mode, run_start=rs, run_end=re_)
            filter_desc = f"Runs {rs} → {re_}"

        logger.info(
            "run_analysis: mode=%s, filter_desc=%s, selected_files=%d",
            mode, filter_desc, len(selected_files)
        )

        if not selected_files:
            QMessageBox.information(
                self,
                "No matching files",
                f"No files match the selected filter.\nFilter: {filter_desc}",
            )
            self.status_label.setText("No matching files")
            return

        self.status_label.setText(f"Queued {len(selected_files)} files | {filter_desc}")

        self.worker = AnalysisWorker(
            data_dir=data_dir,
            config_dir=config_dir,
            selected_mu_files=selected_files,
            recon_path=recon_path,
            fov_deg=13.0,
        )
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_analysis_progress)

        self.run_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        logger.info("Starting AnalysisWorker thread")
        self.worker.start()

    def on_analysis_progress(self, percent: int, done: int, total: int):
        self.status_label.setText(f"{done}/{total} files ({percent}%)")

    def on_analysis_finished(
            self,
            counts_hits,
            counts_events,
            counts_tracks,
            det,
            flux_raw,
            unc_raw,
            fov_deg,
            unit_str,
            summary: str,
    ):
        logger.info("on_analysis_finished called")
        QApplication.restoreOverrideCursor()
        self.run_btn.setEnabled(True)
        self.worker = None

        self.counts_hits = counts_hits
        self.counts_events = counts_events
        self.counts_tracks = counts_tracks
        self.det = det

        self.flux_base_array = flux_raw
        self.unc_base_array = unc_raw
        self.flux_fov_deg = fov_deg
        self.flux_unit_str = unit_str

        if self.flux_base_array is not None:
            lam = self.lambda_spin.value()
            logger.info("Applying initial λ=%f to flux arrays", lam)
            self.flux_array = tikhonov_smooth_neumann(
                self.flux_base_array.copy(), lam=lam, hx=self.reg_hx, hy=self.reg_hy
            )
            self.uncertainty_array = tikhonov_smooth_neumann(
                self.unc_base_array.copy(), lam=lam, hx=self.reg_hx, hy=self.reg_hy
            )
            summary = summary + f" | λ={lam:.3g}"
        else:
            self.flux_array = None
            self.uncertainty_array = None

        self.status_label.setText(summary)

        info_lines = []
        if counts_hits is not None:
            info_lines.append(f"Raw Hits layers: {len(counts_hits)}")
            for i, layer in enumerate(counts_hits):
                info_lines.append(f"  Layer {i}: {layer.shape}")
        if self.flux_array is not None:
            info_lines.append(f"Flux shape: {self.flux_array.shape}, unit={self.flux_unit_str}")
        else:
            info_lines.append("Flux: not computed (no tracks or error).")
        self.info_label.setText("\n".join(info_lines))

        self._plot_layer_maps(self.raw_hits_canvas, self.counts_hits, "Raw Hits")
        self._plot_layer_maps(self.selected_hits_canvas, self.counts_events, "Selected Hits")
        self._plot_layer_maps(self.tracked_hits_canvas, self.counts_tracks, "Tracked Hits")
        self._plot_flux(self.flux_canvas, self.flux_array, "Flux", f"Flux ({self.flux_unit_str})")
        self._plot_flux(
            self.unc_canvas,
            self.uncertainty_array,
            "Flux Uncertainty",
            f"Uncertainty ({self.flux_unit_str})",
        )

    def on_analysis_error(self, message: str):
        logger.error("on_analysis_error: %s", message)
        QApplication.restoreOverrideCursor()
        self.run_btn.setEnabled(True)
        self.worker = None
        QMessageBox.critical(self, "Analysis error", message)

    # ---------------- Plot helpers ----------------
    def _plot_layer_maps(self, canvas: FigureCanvas, layer_maps: Optional[List[np.ndarray]], title: str):
        fig = canvas.figure
        fig.clear()
        self._style_figure(fig)

        if not layer_maps:
            ax = fig.add_subplot(111)
            self._style_axes(ax)
            text_color = "white" if self.current_theme == "dark" else "black"
            ax.text(0.5, 0.5, f"No data for {title}", ha="center", va="center", color=text_color)
            ax.set_axis_off()
            canvas.draw_idle()
            return

        n_layers = len(layer_maps)
        n_show = min(n_layers, 4)
        nrows, ncols = 2, 2

        vmin = min(float(np.min(m)) for m in layer_maps[:n_show])
        vmax = max(float(np.max(m)) for m in layer_maps[:n_show])
        if vmax == vmin:
            vmax = vmin + 1.0

        fig.subplots_adjust(left=0.07, right=0.88, top=0.94, bottom=0.06,
                            hspace=0.4, wspace=0.3)
        last_im = None

        for idx in range(nrows * ncols):
            ax = fig.add_subplot(nrows, ncols, idx + 1)
            self._style_axes(ax)
            if idx < n_show:
                img = layer_maps[idx]
                last_im = ax.imshow(
                    img,
                    cmap="viridis",
                    vmin=vmin,
                    vmax=vmax,
                    aspect="equal",
                )
                text_color = "white" if self.current_theme == "dark" else "black"
                ax.set_title(f"Layer {idx + 1}", fontsize=11, color=text_color)
                ax.set_xticks([])
                ax.set_yticks([])
            else:
                ax.set_axis_off()

        if last_im is not None:
            cax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
            cbar = fig.colorbar(last_im, cax=cax, label="Counts")
            self._style_colorbar(cbar)

        title_color = "white" if self.current_theme == "dark" else "black"
        fig.suptitle(title, fontsize=13, color=title_color)
        canvas.draw_idle()

    def _plot_flux(self, canvas: FigureCanvas, Z: Optional[np.ndarray], title: str, label: str):
        fig = canvas.figure
        fig.clear()
        self._style_figure(fig)
        ax = fig.add_subplot(111)
        self._style_axes(ax)

        if Z is None:
            text_color = "white" if self.current_theme == "dark" else "black"
            ax.text(0.5, 0.5, f"{title} not computed", ha="center", va="center", color=text_color)
            ax.set_axis_off()
            canvas.draw_idle()
            return

        fov = self.flux_fov_deg
        im = ax.imshow(
            Z.T,
            extent=[-fov, fov, -fov, fov],
            origin="lower",
            cmap="viridis",
            aspect="equal",
        )
        ax.set_xlabel("Theta X (deg)")
        ax.set_ylabel("Theta Y (deg)")
        text_color = "white" if self.current_theme == "dark" else "black"
        ax.set_title(title, color=text_color)

        fig.subplots_adjust(left=0.07, right=0.88, top=0.94, bottom=0.08)
        cax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
        cbar = fig.colorbar(im, cax=cax, label=label)
        self._style_colorbar(cbar)

        canvas.draw_idle()

    # ---------------- Apply new λ ----------------
    def apply_lambda(self):
        logger.info("Apply λ clicked")
        if self.flux_base_array is None or self.unc_base_array is None:
            QMessageBox.information(self, "Flux", "Flux not computed yet.\nRun analysis first.")
            return

        lam = self.lambda_spin.value()
        try:
            logger.info("Recomputing flux with λ=%f", lam)
            self.flux_array = tikhonov_smooth_neumann(
                self.flux_base_array.copy(), lam=lam, hx=self.reg_hx, hy=self.reg_hy
            )
            self.uncertainty_array = tikhonov_smooth_neumann(
                self.unc_base_array.copy(), lam=lam, hx=self.reg_hx, hy=self.reg_hy
            )
        except Exception as e:
            logger.exception("Error in Tikhonov smoothing")
            QMessageBox.warning(self, "Regularization error", f"Error in Tikhonov smoothing:\n{e}")
            return

        self.status_label.setText(f"Flux regularized with λ={lam:.3g}")

        self._plot_flux(self.flux_canvas, self.flux_array, "Flux", f"Flux ({self.flux_unit_str})")
        self._plot_flux(
            self.unc_canvas,
            self.uncertainty_array,
            "Flux Uncertainty",
            f"Uncertainty ({self.flux_unit_str})",
        )

    # ---------------- Save flux arrays ----------------
    def save_flux_arrays(self):
        logger.info("Save Flux Arrays clicked")
        if self.flux_array is None or self.uncertainty_array is None:
            QMessageBox.information(self, "Flux", "No flux arrays to save.\nRun analysis first.")
            return

        fname, _ = QFileDialog.getSaveFileName(
            self,
            "Save flux array (.npy)",
            "flux.npy",
            "NumPy file (*.npy);;All files (*)",
        )
        if not fname:
            return

        try:
            logger.info("Saving flux array to %s", fname)
            np.save(fname, self.flux_array)
            base = os.path.splitext(fname)[0]
            unc_name = base + "_uncertainty.npy"
            logger.info("Saving uncertainty array to %s", unc_name)
            np.save(unc_name, self.uncertainty_array)
            QMessageBox.information(
                self,
                "Saved",
                f"Saved:\n- {fname}\n- {unc_name}",
            )
        except Exception as e:
            logger.exception("Error saving flux arrays")
            QMessageBox.warning(self, "Save error", f"Could not save flux arrays:\n{e}")


# ============================================================
#  Themes + main()
# ============================================================
def _apply_common_styles(app: QApplication):
    font = QFont(app.font())
    font.setPointSize(11)
    app.setFont(font)

    app.setStyleSheet("""
    QGroupBox {
        font-size: 11pt;
        font-weight: bold;
        margin-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 6px;
    }
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPushButton {
        font-size: 11pt;
    }
    """)


def apply_light_theme(app: QApplication):
    app.setStyle("Fusion")
    palette = app.style().standardPalette()
    app.setPalette(palette)
    _apply_common_styles(app)


def apply_dark_theme(app: QApplication):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    _apply_common_styles(app)


def main():
    logger.info("Application starting")
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    w = HitMapWindow()
    w.showMaximized()
    ret = app.exec()
    logger.info("Application exiting with code %d", ret)
    sys.exit(ret)


if __name__ == "__main__":
    import multiprocessing as mp

    mp.freeze_support()
    main()