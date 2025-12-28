#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import numpy as np

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QDoubleValidator, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QDockWidget, QFormLayout,
    QFileDialog, QMessageBox, QLineEdit, QPushButton, QCheckBox, QLabel, QHBoxLayout,
    QSlider, QDoubleSpinBox, QComboBox, QSizePolicy, QSpinBox, QGraphicsOpacityEffect
)

import pyqtgraph as pg
import pyqtgraph.opengl as gl
import matplotlib.tri as mtri

# ------------------------------------------------------------
# Settings dialog (separate file)
# ------------------------------------------------------------
from .settings_dialog import (
    SettingsDialog,
    default_settings,
    load_settings,
    save_settings,
    deep_update,
    rgba255_to_gl,
)
from .startup import StartupSplash
from .properties import PropertiesDialog, warmup_gl_widget
from .dem_utils import (
    _unit,
    _ceil_to_step,
    _extract_meta_dict,
    boresight_from_zen_az,
    build_density_interpolator,
    detector_frame_from_boresight,
    direction_from_detector_thetas,
    project_to_detector_thetas,
    sanitize_dem_points,
    triangle_plane_intersections,
    upscale_dem_bilinear_points,
)
from .resources import data_path, resolve_asset_path, default_dem_path, default_settings_store


def load_app_icon() -> QIcon | None:
    env_path = os.environ.get("MUOGRAPHY_ICON_PATH")
    candidates: list[Path | None] = [
        resolve_asset_path(env_path) if env_path else None,
        resolve_asset_path("muography_icon.png"),
    ]

    for path in candidates:
        if path is None:
            continue
        if path.exists():
            try:
                return QIcon(str(path))
            except Exception:
                continue
    return None


def apply_dark_qt(app: QApplication):
    app.setStyle("Fusion")
    pal = QPalette()
    bg = QColor(30, 30, 30)
    base = QColor(24, 24, 24)
    text = QColor(220, 220, 220)
    mid = QColor(45, 45, 45)
    highlight = QColor(90, 160, 255)
    pal.setColor(QPalette.ColorRole.Window, bg)
    pal.setColor(QPalette.ColorRole.WindowText, text)
    pal.setColor(QPalette.ColorRole.Base, base)
    pal.setColor(QPalette.ColorRole.AlternateBase, mid)
    pal.setColor(QPalette.ColorRole.Text, text)
    pal.setColor(QPalette.ColorRole.Button, mid)
    pal.setColor(QPalette.ColorRole.ButtonText, text)
    pal.setColor(QPalette.ColorRole.Highlight, highlight)
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(pal)


def apply_light_qt(app: QApplication):
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())


def apply_system_theme(app: QApplication):
    try:
        scheme = app.styleHints().colorScheme()
    except Exception:
        scheme = Qt.ColorScheme.Unknown

    if scheme == Qt.ColorScheme.Dark:
        apply_dark_qt(app)
    else:
        apply_light_qt(app)

# ============================================================
# Interpolator (θx, θy) -> value
# ============================================================

# ============================================================
# Viewer
# ============================================================

class DEMViewerPG(QMainWindow):
    def __init__(self, npz_path: str | os.PathLike | None = None, settings_path: str | os.PathLike | None = None):
        super().__init__()
        self.setWindowTitle("Muography 3D DEM Viewer")
        self._app_icon = load_app_icon()
        if self._app_icon is not None:
            try:
                self.setWindowIcon(self._app_icon)
            except Exception:
                pass

        # Slider uses int ticks. Value shown/used = tick / SCALE.
        self.SLICE_SCALE_Y = 10  # 10 ticks per degree => 0.1° resolution
        self.SLICE_SCALE_X = 10  # 0.1° resolution

        # Settings persistence
        self.settings_path = str(settings_path or default_settings_store())
        self.cfg = load_settings(self.settings_path, defaults=default_settings())
        self._last_perf_key = None  # to avoid rebuild if perf unchanged

        # Keep raw DEM (so perf setting changes can rebuild without reopening)
        self._dem_raw = None

        # --- DEM rebuild debounce ---
        # Changing the upscale factor can emit several UI signals in quick succession.
        # Rebuilding the mesh repeatedly can leave transient/incorrect face-colors on screen
        # until the next paint event. We debounce rebuilds and defer the redraw to the next
        # event-loop tick so GL gets a clean repaint.
        self._rebuilding_dem = False
        self._upscale_rebuild_timer = QTimer(self)
        self._upscale_rebuild_timer.setSingleShot(True)
        # small delay to coalesce rapid changes (spinbox clicks / key repeats)
        self._upscale_rebuild_timer.setInterval(0)
        self._upscale_rebuild_timer.timeout.connect(self._apply_upscale_rebuild)
        self._pending_upscale_rebuild = False
        self._pending_upscale_update_center = False

        # GL view
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor(tuple(int(x) for x in self.cfg["appearance"]["background"]))

        # --- create Properties menu ---
        menu_props = self.menuBar().addMenu("Properties")
        act_props = menu_props.addAction("OpenGL / System Info")
        act_props.triggered.connect(self.show_properties_dialog)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.addWidget(self.view)
        self.setCentralWidget(central)

        # Data
        self.pts_xyz = None
        self.triangles = None
        self.face_centroids = None
        self.default_z_at_0_0 = None
        self._height_min = None
        self._height_max = None

        self.mesh_data = None
        self.base_face_colors = None
        self.face_colors_work = None

        # Overlay maps (θx, θy) -> value
        self.maps_loaded = False
        self.maps_interps = {}
        self.maps_meta = {}
        self.maps_path = None
        self.maps_file_meta = None

        # LUT
        self._lut = self._make_lut_from_cfg()
        self._fov_lut = self._make_lut(self.cfg.get("overlay", {}).get("fov_colormap", "viridis"))

        # main mesh
        self.mesh_item = None

        # θy slice items
        self.slice_plane_y = None
        self.slice_border_y = None
        self.slice_lines_glow_y = None
        self.slice_lines_main_y = None

        # θx slice items
        self.slice_plane_x = None
        self.slice_border_x = None
        self.slice_lines_glow_x = None
        self.slice_lines_main_x = None

        # reference items
        self.base_grid_item = None
        self.z_axis_item = None
        self.z_ticks_item = None

        # colorbar objects
        self.cb_plot = None
        self.cb_view = None
        self.cb_axis = None
        self.cb_img = None
        self._cb_N = 256
        self._cb_data = None

        # UI polish helpers
        self._pulse_effects = {}
        self._pulse_anims = {}
        self._last_colorbar_range = None

        self._build_controls_dock()
        self._build_menu()

        # Apply settings to camera, etc (no refresh yet)
        self.apply_settings(self.cfg, refresh=False)

        dem_path = resolve_asset_path(str(npz_path)) if npz_path else default_dem_path()
        if dem_path and Path(dem_path).exists():
            try:
                self.load_dem(str(dem_path))
            except Exception:
                pass
            self.update_scene()

    def show_properties_dialog(self):
        dlg = PropertiesDialog(gl_widget=self.view, parent=self)
        dlg.exec()

    # ------------------------------------------------------------
    # LUT / colormap
    # ------------------------------------------------------------

    def _make_lut(self, cmap_name, n=256):
        n = int(n or 256)
        cmap_name = str(cmap_name or "viridis").strip() or "viridis"
        try:
            cmap = pg.colormap.get(cmap_name)
            try:
                lut = cmap.getLookupTable(0.0, 1.0, n, alpha=True)
            except TypeError:
                lut = cmap.getLookupTable(0.0, 1.0, n)

            lut = np.asarray(lut)
            if lut.ndim != 2:
                raise ValueError("Unexpected LUT shape")
            if lut.shape[1] == 3:
                a = np.full((lut.shape[0], 1), 255, dtype=lut.dtype)
                lut = np.concatenate([lut, a], axis=1)
            return lut.astype(np.uint8, copy=False)
        except Exception:
            x = np.linspace(0, 255, n).astype(np.uint8)
            return np.stack([x, x, x, np.full_like(x, 255)], axis=1)

    def _make_lut_from_cfg(self, n=256):
        cmap_name = self.cfg.get("appearance", {}).get("colormap", "viridis")
        return self._make_lut(cmap_name, n=n)

    def _map_values_to_rgba(self, values, lo, hi, lut):
        values = np.asarray(values, dtype=float)
        out = np.zeros((values.size, 4), dtype=np.float32)

        if lut is None or not isinstance(lut, np.ndarray) or lut.size == 0:
            return out, np.zeros(values.shape, dtype=bool)

        valid = np.isfinite(values)
        if not np.any(valid):
            return out, valid

        denom = (hi - lo) if (hi > lo) else 1.0
        t = (values[valid] - lo) / denom
        t = np.clip(t, 0.0, 1.0)

        idx = np.clip((t * (lut.shape[0] - 1)).astype(np.int32), 0, lut.shape[0] - 1)
        rgba_u8 = lut[idx]
        out[valid] = rgba_u8.astype(np.float32) / 255.0
        return out, valid

    def _map_rho_to_rgba(self, rho, lo, hi):
        return self._map_values_to_rgba(rho, lo, hi, self._lut)

    # ------------------------------------------------------------
    # Menu / settings integration
    # ------------------------------------------------------------

    def _build_menu(self):
        mb = self.menuBar()
        m = mb.addMenu("Settings")

        act_pref = m.addAction("Preferences…")
        act_pref.triggered.connect(self.open_preferences)

        m.addSeparator()

        act_load = m.addAction("Load settings…")
        act_load.triggered.connect(self.load_settings_from_disk)

        act_save = m.addAction("Save settings…")
        act_save.triggered.connect(self.save_settings_to_disk)

        act_reset = m.addAction("Reset settings (defaults)")
        act_reset.triggered.connect(self.reset_settings_defaults)

    def open_preferences(self):
        dlg = SettingsDialog(self.cfg, parent=self)
        dlg.settingsApplied.connect(self._on_settings_applied)
        dlg.exec()

    def _on_settings_applied(self, new_cfg: dict):
        base = default_settings()
        merged = load_settings(self.settings_path, defaults=base)  # start from defaults
        deep_update(merged, new_cfg)
        self.cfg = merged
        self.apply_settings(self.cfg, refresh=True)
        try:
            save_settings(self.settings_path, self.cfg)
        except Exception:
            pass

    def load_settings_from_disk(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load settings", "", "JSON (*.json);;All Files (*)")
        if not path:
            return
        self.cfg = load_settings(path, defaults=default_settings())
        self.apply_settings(self.cfg, refresh=True)
        try:
            save_settings(self.settings_path, self.cfg)
        except Exception:
            pass

    def save_settings_to_disk(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save settings", "", "JSON (*.json);;All Files (*)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        save_settings(path, self.cfg)

    def reset_settings_defaults(self):
        self.cfg = default_settings()
        self.apply_settings(self.cfg, refresh=True)
        try:
            save_settings(self.settings_path, self.cfg)
        except Exception:
            pass

    def apply_settings(self, cfg: dict, refresh: bool = True):
        # background
        bg = tuple(int(x) for x in cfg["appearance"]["background"])
        try:
            self.view.setBackgroundColor(bg)
        except Exception:
            pass

        # camera
        cam = cfg["camera"]
        try:
            self.view.setCameraPosition(
                distance=float(cam["distance"]),
                elevation=float(cam["elevation"]),
                azimuth=float(cam["azimuth"])
            )
        except Exception:
            try:
                self.view.opts["distance"] = float(cam["distance"])
                self.view.opts["elevation"] = float(cam["elevation"])
                self.view.opts["azimuth"] = float(cam["azimuth"])
            except Exception:
                pass

        try:
            self.view.opts["fov"] = float(cam.get("fov", 60.0))
        except Exception:
            pass

        try:
            if "perspective" in self.view.opts:
                self.view.opts["perspective"] = bool(cam.get("perspective", True))
        except Exception:
            pass

        # LUT / colormap
        n_lut = getattr(self, "_cb_N", 256)
        self._lut = self._make_lut_from_cfg(n=n_lut)
        self._fov_lut = self._make_lut(cfg.get("overlay", {}).get("fov_colormap", "viridis"), n=n_lut)
        if self.cb_img is not None:
            try:
                self.cb_img.setLookupTable(self._lut)
            except Exception:
                pass

        # grid color
        try:
            if self.base_grid_item is not None:
                self.base_grid_item.setColor(tuple(int(x) for x in cfg["grid"]["color"]))
        except Exception:
            pass

        # rebuild DEM only if performance settings changed
        perf = cfg.get("performance", default_settings()["performance"])
        perf_key = (
            int(perf.get("max_points", 250000)),
            int(perf.get("dedupe_round_decimals", 6)),
        )
        if refresh and (self._dem_raw is not None) and (perf_key != self._last_perf_key):
            self._last_perf_key = perf_key
            try:
                self._rebuild_dem_from_raw(update_center=False)
            except Exception:
                pass

        if refresh:
            self.update_scene()

    # ------------------------------------------------------------
    # UI: controls dock
    # ------------------------------------------------------------

    def _build_controls_dock(self):
        dock = QDockWidget("Controls", self)
        dock.setMinimumWidth(430)  # helps the "Maps" row have enough room

        w = QWidget()

        form = QFormLayout(w)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        v = QDoubleValidator()
        v.setNotation(QDoubleValidator.Notation.StandardNotation)

        self.edit_cx = QLineEdit("0.0")
        self.edit_cx.setValidator(v)
        self.edit_cy = QLineEdit("0.0")
        self.edit_cy.setValidator(v)
        self.edit_cz = QLineEdit("0.0")
        self.edit_cz.setValidator(v)
        form.addRow("Center X (m)", self.edit_cx)
        form.addRow("Center Y (m)", self.edit_cy)

        # Center Z row
        cz_row = QWidget()
        cz_lay = QHBoxLayout(cz_row)
        cz_lay.setContentsMargins(0, 0, 0, 0)
        cz_lay.setSpacing(8)
        cz_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.btn_reset_z = QPushButton("Reset Z")
        self.btn_reset_z.setToolTip("Reset Z = DEM@0,0")
        self.btn_reset_z.setFixedWidth(90)
        self.btn_reset_z.clicked.connect(self.reset_z_to_dem_0_0)

        h = max(self.edit_cz.sizeHint().height(), self.btn_reset_z.sizeHint().height())
        self.edit_cz.setFixedHeight(h)
        self.btn_reset_z.setFixedHeight(h)

        cz_lay.addWidget(self.edit_cz, 1)
        cz_lay.addWidget(self.btn_reset_z, 0)
        form.addRow("Center Z (m)", cz_row)

        self.edit_zen = QLineEdit("76.6")
        self.edit_zen.setValidator(v)
        self.edit_az = QLineEdit("90.0")
        self.edit_az.setValidator(v)
        form.addRow("Zenith (deg)", self.edit_zen)
        form.addRow("Azimuth (deg)", self.edit_az)

        self.edit_fovx = QLineEdit("13.0")
        self.edit_fovx.setValidator(v)
        self.edit_fovy = QLineEdit("13.0")
        self.edit_fovy.setValidator(v)
        form.addRow("FOV θx_max (deg)", self.edit_fovx)
        form.addRow("FOV θy_max (deg)", self.edit_fovy)

        self.chk_fov = QCheckBox("Show FOV mask")
        self.chk_fov.setChecked(True)
        self.chk_density = QCheckBox("Overlay map (inside FOV)")
        self.chk_density.setChecked(True)

        # slices (separate toggles)
        self.chk_slice_y = QCheckBox("Show θy slice")
        self.chk_slice_y.setChecked(True)
        self.chk_slice_x = QCheckBox("Show θx slice")
        self.chk_slice_x.setChecked(False)

        self.chk_base_grid = QCheckBox("Show base grid (z = DEM@0,0)")
        self.chk_base_grid.setChecked(False)
        self.chk_height_axis = QCheckBox("Show height axis + ticks")
        self.chk_height_axis.setChecked(False)

        form.addRow(self.chk_fov)
        form.addRow(self.chk_density)
        form.addRow(self.chk_slice_y)
        form.addRow(self.chk_slice_x)
        form.addRow(self.chk_base_grid)
        form.addRow(self.chk_height_axis)

        # =====================================================
        # DEM Upscale (bilinear, grid-only)
        # =====================================================
        self.chk_upscale_dem = QCheckBox("Upscale DEM (bilinear, grid-only)")
        self.chk_upscale_dem.setChecked(False)

        self.spin_upscale_factor = QSpinBox()
        self.spin_upscale_factor.setRange(1, 8)
        self.spin_upscale_factor.setValue(2)
        # Avoid expensive rebuilds on every keypress while typing.
        # (Step buttons still work normally.)
        try:
            self.spin_upscale_factor.setKeyboardTracking(False)
        except Exception:
            pass
        self.spin_upscale_factor.setEnabled(False)

        form.addRow(self.chk_upscale_dem)
        form.addRow("Upscale factor", self.spin_upscale_factor)

        # =====================================================
        # FLOAT θy slice control  (QDoubleSpinBox + scaled QSlider)
        # =====================================================
        row_y = QWidget()
        hl_y = QHBoxLayout(row_y)
        hl_y.setContentsMargins(0, 0, 0, 0)

        self.spin_slice_y = QDoubleSpinBox()
        self.spin_slice_y.setDecimals(1)
        self.spin_slice_y.setSingleStep(0.1)
        self.spin_slice_y.setRange(-13.0, 13.0)
        self.spin_slice_y.setValue(10.0)

        self.slider_slice_y = QSlider(Qt.Orientation.Horizontal)
        self.slider_slice_y.setTracking(True)
        self.slider_slice_y.setSingleStep(1)  # 1 tick = 0.1°
        self.slider_slice_y.setPageStep(5)    # 0.5°
        self.slider_slice_y.setRange(int(-13.0 * self.SLICE_SCALE_Y), int(13.0 * self.SLICE_SCALE_Y))
        self.slider_slice_y.setValue(int(round(10.0 * self.SLICE_SCALE_Y)))

        self.lbl_slice_y = QLabel("θy = 10.0°")
        self.lbl_slice_y.setStyleSheet("color: #dcdcdc;")

        hl_y.addWidget(self.spin_slice_y)
        hl_y.addWidget(self.slider_slice_y, 1)
        hl_y.addWidget(self.lbl_slice_y)
        form.addRow("Slice θy (deg)", row_y)

        # =====================================================
        # FLOAT θx slice control  (QDoubleSpinBox + scaled QSlider)
        # =====================================================
        row_x = QWidget()
        hl_x = QHBoxLayout(row_x)
        hl_x.setContentsMargins(0, 0, 0, 0)

        self.spin_slice_x = QDoubleSpinBox()
        self.spin_slice_x.setDecimals(1)
        self.spin_slice_x.setSingleStep(0.1)
        self.spin_slice_x.setRange(-13.0, 13.0)
        self.spin_slice_x.setValue(0.0)

        self.slider_slice_x = QSlider(Qt.Orientation.Horizontal)
        self.slider_slice_x.setTracking(True)
        self.slider_slice_x.setSingleStep(1)  # 0.1°
        self.slider_slice_x.setPageStep(5)    # 0.5°
        self.slider_slice_x.setRange(int(-13.0 * self.SLICE_SCALE_X), int(13.0 * self.SLICE_SCALE_X))
        self.slider_slice_x.setValue(int(round(0.0 * self.SLICE_SCALE_X)))

        self.lbl_slice_x = QLabel("θx = 0.0°")
        self.lbl_slice_x.setStyleSheet("color: #dcdcdc;")

        hl_x.addWidget(self.spin_slice_x)
        hl_x.addWidget(self.slider_slice_x, 1)
        hl_x.addWidget(self.lbl_slice_x)
        form.addRow("Slice θx (deg)", row_x)

        # =====================================================
        # Maps loader row (use a readonly QLineEdit so it doesn't elide)
        # =====================================================
        maps_row = QWidget()
        maps_hl = QHBoxLayout(maps_row)
        maps_hl.setContentsMargins(0, 0, 0, 0)

        self.maps_path_edit = QLineEdit()
        self.maps_path_edit.setReadOnly(True)
        self.maps_path_edit.setText("No maps loaded")
        self.maps_path_edit.setToolTip("Load maps: requires RADX, RADY and one of RHO/FLUX/THICK")
        self.maps_path_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.btn_den = QPushButton("Load maps .npz")
        self.btn_den.clicked.connect(self.open_maps)

        maps_hl.addWidget(self.maps_path_edit, 1)
        maps_hl.addWidget(self.btn_den, 0)
        form.addRow("Maps", maps_row)

        # overlay chooser
        self.combo_overlay = QComboBox()
        self.combo_overlay.addItem("None", userData=None)
        self.combo_overlay.setEnabled(False)
        form.addRow("Overlay field", self.combo_overlay)

        # scale chooser
        self.combo_scale = QComboBox()
        self.combo_scale.addItem("Linear", userData="linear")
        self.combo_scale.addItem("log10", userData="log10")
        form.addRow("Scale", self.combo_scale)

        # =====================================================
        # Colorbar (HORIZONTAL): ViewBox + bottom AxisItem
        # =====================================================
        self.cb_plot = pg.GraphicsLayoutWidget()
        self.cb_plot.setFixedHeight(120)
        self.cb_plot.setMinimumWidth(220)
        self.cb_plot.setBackground((30, 30, 30))

        self.cb_view = pg.ViewBox(enableMouse=False)
        self.cb_view.setMenuEnabled(False)
        self.cb_view.setMouseEnabled(x=False, y=False)
        self.cb_view.setDefaultPadding(0.0)

        self.cb_axis = pg.AxisItem(orientation="bottom")
        self.cb_axis.setPen(pg.mkPen((220, 220, 220)))
        self.cb_axis.setTextPen(pg.mkPen((220, 220, 220)))
        self.cb_axis.setLabel("Overlay", color="#dcdcdc")
        self.cb_axis.setStyle(autoExpandTextSpace=True, tickTextOffset=6)

        self.cb_plot.addItem(self.cb_view, row=0, col=0)
        self.cb_plot.addItem(self.cb_axis, row=1, col=0)
        self.cb_axis.linkToView(self.cb_view)

        def _cb_sync_axis(*args):
            xr = self.cb_view.viewRange()[0]
            self.cb_axis.setRange(xr[0], xr[1])

        self.cb_view.sigRangeChanged.connect(_cb_sync_axis)

        self.cb_img = pg.ImageItem()

        row_major_ok = False
        try:
            self.cb_img.setOpts(axisOrder="row-major")
            row_major_ok = True
        except Exception:
            row_major_ok = False

        self.cb_view.addItem(self.cb_img)

        self._cb_N = 256
        if row_major_ok:
            self._cb_data = np.linspace(0, 1, self._cb_N, dtype=np.float32).reshape(1, self._cb_N)
        else:
            self._cb_data = np.linspace(0, 1, self._cb_N, dtype=np.float32).reshape(self._cb_N, 1)

        self.cb_img.setImage(self._cb_data, autoLevels=False)
        self.cb_img.setLookupTable(self._lut)
        self.cb_img.setLevels([0.0, 1.0])

        self.cb_img.setRect(pg.QtCore.QRectF(0.0, 0.0, 1.0, 1.0))
        self.cb_view.setRange(xRange=(0.0, 1.0), yRange=(0.0, 1.0), padding=0.0)
        _cb_sync_axis()

        form.addRow("Colorbar", self.cb_plot)

        btn_open_dem = QPushButton("Open DEM .npz")
        btn_open_dem.clicked.connect(self.open_dem)
        form.addRow(btn_open_dem)

        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)
        form.addRow("Info", self.lbl_info)

        # ---------- wiring ----------
        def sync_spin_y():
            vdeg = float(self.spin_slice_y.value())
            self.slider_slice_y.blockSignals(True)
            self.slider_slice_y.setValue(int(round(vdeg * self.SLICE_SCALE_Y)))
            self.slider_slice_y.blockSignals(False)
            self.lbl_slice_y.setText(f"θy = {vdeg:.1f}°")
            self._pulse_widget(self.lbl_slice_y)
            self.update_scene()

        def sync_slider_y(val):
            vdeg = float(val) / float(self.SLICE_SCALE_Y)
            self.spin_slice_y.blockSignals(True)
            self.spin_slice_y.setValue(vdeg)
            self.spin_slice_y.blockSignals(False)
            self.lbl_slice_y.setText(f"θy = {vdeg:.1f}°")
            self._pulse_widget(self.lbl_slice_y)
            self.update_scene()

        def sync_spin_x():
            vdeg = float(self.spin_slice_x.value())
            self.slider_slice_x.blockSignals(True)
            self.slider_slice_x.setValue(int(round(vdeg * self.SLICE_SCALE_X)))
            self.slider_slice_x.blockSignals(False)
            self.lbl_slice_x.setText(f"θx = {vdeg:.1f}°")
            self._pulse_widget(self.lbl_slice_x)
            self.update_scene()

        def sync_slider_x(val):
            vdeg = float(val) / float(self.SLICE_SCALE_X)
            self.spin_slice_x.blockSignals(True)
            self.spin_slice_x.setValue(vdeg)
            self.spin_slice_x.blockSignals(False)
            self.lbl_slice_x.setText(f"θx = {vdeg:.1f}°")
            self._pulse_widget(self.lbl_slice_x)
            self.update_scene()

        self.spin_slice_y.valueChanged.connect(sync_spin_y)
        self.slider_slice_y.valueChanged.connect(sync_slider_y)
        self.spin_slice_x.valueChanged.connect(sync_spin_x)
        self.slider_slice_x.valueChanged.connect(sync_slider_x)

        def _connect_toggle_with_pulse(box, handler):
            def _wrap(*_):
                self._pulse_widget(box)
                handler()
            box.stateChanged.connect(_wrap)

        _connect_toggle_with_pulse(self.chk_slice_y, self.update_scene)
        _connect_toggle_with_pulse(self.chk_slice_x, self.update_scene)
        _connect_toggle_with_pulse(self.chk_fov, self.update_scene)
        _connect_toggle_with_pulse(self.chk_density, self.update_scene)
        _connect_toggle_with_pulse(self.chk_base_grid, self.update_scene)
        _connect_toggle_with_pulse(self.chk_height_axis, self.update_scene)

        def _on_overlay_or_scale_changed(*args):
            self._update_colorbar_label_from_ui()
            self.update_scene()

        self.combo_overlay.currentIndexChanged.connect(_on_overlay_or_scale_changed)
        self.combo_scale.currentIndexChanged.connect(_on_overlay_or_scale_changed)

        for le in (self.edit_cx, self.edit_cy, self.edit_cz, self.edit_zen, self.edit_az):
            le.editingFinished.connect(self.update_scene)

        # When FOV changes, update slice ranges FIRST, then redraw
        self.edit_fovy.editingFinished.connect(lambda: self._update_slice_range_from_fovy(call_update=True))
        self.edit_fovx.editingFinished.connect(lambda: self._update_slice_range_from_fovx(call_update=True))

        # initialize slice ranges from current fov
        self._update_slice_range_from_fovy(call_update=False)
        self._update_slice_range_from_fovx(call_update=False)

        # DEM upscaling changes => rebuild from raw, then update
        def _on_upscale_changed(*args):
            self.spin_upscale_factor.setEnabled(self.chk_upscale_dem.isChecked())
            self._pulse_widget(self.chk_upscale_dem)
            if self._dem_raw is None:
                return
            # Debounce; repeated changes coalesce into one rebuild.
            self._schedule_upscale_rebuild(update_center=False)

        self.chk_upscale_dem.stateChanged.connect(_on_upscale_changed)
        self.spin_upscale_factor.valueChanged.connect(_on_upscale_changed)

        self._setup_feedback_animations()
        dock.setWidget(w)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _setup_feedback_animations(self):
        targets = (
            self.chk_fov,
            self.chk_density,
            self.chk_slice_y,
            self.chk_slice_x,
            self.chk_base_grid,
            self.chk_height_axis,
            self.chk_upscale_dem,
            self.cb_plot,
            self.lbl_info,
            self.lbl_slice_y,
            self.lbl_slice_x,
            self.maps_path_edit,
        )
        for w in targets:
            self._attach_opacity_pulse(w)

    def _attach_opacity_pulse(self, widget, start_opacity=0.45, duration_ms=320):
        if widget is None:
            return
        eff = QGraphicsOpacityEffect(widget)
        eff.setOpacity(1.0)
        widget.setGraphicsEffect(eff)

        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(int(duration_ms))
        anim.setStartValue(float(start_opacity))
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.finished.connect(lambda eff=eff: eff.setOpacity(1.0))

        self._pulse_effects[widget] = eff
        self._pulse_anims[widget] = anim

    def _pulse_widget(self, widget):
        anim = self._pulse_anims.get(widget, None)
        eff = self._pulse_effects.get(widget, None)
        if anim is None or eff is None:
            return
        try:
            anim.stop()
            eff.setOpacity(float(anim.startValue()))
            anim.start()
        except Exception:
            pass

    # ------------------------------------------------------------
    # dialogs
    # ------------------------------------------------------------

    def open_dem(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open DEM .npz", "", "NumPy NPZ (*.npz);;All Files (*)")
        if path:
            try:
                self.load_dem(path)
                self.update_scene()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def open_maps(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open maps .npz (RADX/RADY + RHO/FLUX/THICK)",
            "",
            "NumPy NPZ (*.npz);;All Files (*)"
        )
        if path:
            try:
                self.load_maps(path)
                self.update_scene()
            except Exception as e:
                QMessageBox.critical(self, "Map load error", str(e))

    # Backward-compatible name
    def open_density(self):
        self.open_maps()

    # ------------------------------------------------------------
    # maps
    # ------------------------------------------------------------

    @staticmethod
    def _field_display_name(key: str) -> str:
        return {
            "RHO": "Density ρ",
            "FLUX": "Flux",
            "THICK": "Thickness",
        }.get(str(key).upper(), str(key))

    def _refresh_overlay_controls(self, keep_current: bool = True):
        cur = None
        if keep_current:
            try:
                cur = self.combo_overlay.currentData()
            except Exception:
                cur = None

        keys = [k for k in ("RHO", "FLUX", "THICK") if k in self.maps_interps]

        self.combo_overlay.blockSignals(True)
        try:
            self.combo_overlay.clear()
            self.combo_overlay.addItem("None", userData=None)
            for k in keys:
                self.combo_overlay.addItem(f"{self._field_display_name(k)} ({k})", userData=k)
        finally:
            self.combo_overlay.blockSignals(False)

        chosen = None
        if cur in keys:
            chosen = cur
        elif "RHO" in keys:
            chosen = "RHO"
        elif keys:
            chosen = keys[0]

        if chosen is None:
            self.combo_overlay.setCurrentIndex(0)
        else:
            for i in range(self.combo_overlay.count()):
                if self.combo_overlay.itemData(i) == chosen:
                    self.combo_overlay.setCurrentIndex(i)
                    break

        self.combo_overlay.setEnabled(bool(keys))
        self._update_colorbar_label_from_ui()

    def _update_colorbar_label_from_ui(self):
        if self.cb_axis is None:
            return
        try:
            key = self.combo_overlay.currentData()
        except Exception:
            key = None

        try:
            scale = self.combo_scale.currentData() or "linear"
        except Exception:
            scale = "linear"

        if key is None:
            self.cb_axis.setLabel("Overlay", color="#dcdcdc")
            return

        base = self._field_display_name(key)
        if str(scale).lower() == "log10":
            self.cb_axis.setLabel(f"log10({base})", color="#dcdcdc")
        else:
            self.cb_axis.setLabel(base, color="#dcdcdc")

    def _apply_map_meta(self, meta: dict):
        """
        Apply map-provided metadata (e.g., zenith/azimuth/FOV/center) to the UI.
        Values in the meta dict override current user inputs at load time only.
        """
        if not isinstance(meta, dict):
            return

        meta_norm = {str(k).lower(): v for k, v in meta.items()}
        changed_fovx = False
        changed_fovy = False

        def _set_line_edit(le, keys):
            for k in keys:
                if k in meta_norm:
                    try:
                        le.setText(f"{float(meta_norm[k]):.6g}")
                        return True
                    except Exception:
                        continue
            return False

        _set_line_edit(self.edit_cx, ("cx", "center_x", "centerx", "x0", "x", "center-x"))
        _set_line_edit(self.edit_cy, ("cy", "center_y", "centery", "y0", "y", "center-y"))
        _set_line_edit(self.edit_cz, ("cz", "center_z", "centerz", "z0", "z", "center-z"))
        _set_line_edit(self.edit_zen, ("zenith", "zenith_deg", "zen", "zen_deg"))
        _set_line_edit(self.edit_az, ("azimuth", "azimuth_deg", "az", "az_deg"))

        changed_fovx = _set_line_edit(self.edit_fovx, ("fovx", "fov_x", "fovx_deg", "fov_x_deg")) or changed_fovx
        changed_fovy = _set_line_edit(self.edit_fovy, ("fovy", "fov_y", "fovy_deg", "fov_y_deg")) or changed_fovy

        if changed_fovx:
            self._update_slice_range_from_fovx(call_update=False)
        if changed_fovy:
            self._update_slice_range_from_fovy(call_update=False)

    def load_maps(self, npz_path: str):
        path = resolve_asset_path(npz_path)
        if path is None or not path.exists():
            raise ValueError(f"Maps NPZ not found: {npz_path}")

        d = np.load(path, allow_pickle=True)
        for k in ("RADX", "RADY"):
            if k not in d.files:
                raise ValueError(f"{npz_path} missing key '{k}' (expected at least RADX and RADY)")

        file_meta = None
        for meta_key in ("meta", "META", "Meta"):
            if meta_key in d.files:
                file_meta = _extract_meta_dict(d[meta_key])
                if file_meta is not None:
                    break

        RADX = d["RADX"]
        RADY = d["RADY"]

        present = [k for k in ("RHO", "FLUX", "THICK") if k in d.files]
        if not present:
            raise ValueError(f"{npz_path} has no data fields. Expected at least one of: RHO, FLUX, THICK")

        self.maps_interps = {}
        self.maps_meta = {}
        for k in present:
            interp, meta = build_density_interpolator(RADX, RADY, d[k])
            self.maps_interps[k] = interp
            self.maps_meta[k] = meta

        self.maps_file_meta = file_meta
        if self.maps_file_meta:
            self._apply_map_meta(self.maps_file_meta)

        self.maps_loaded = True
        self.maps_path = str(path)

        nice = ", ".join(present)
        shown = f"{path.name} ({nice})"
        self.maps_path_edit.setText(shown)
        self.maps_path_edit.setToolTip(str(path))
        self.maps_path_edit.setCursorPosition(0)
        self._pulse_widget(self.maps_path_edit)

        self._refresh_overlay_controls(keep_current=True)

    # Backward-compatible name
    def load_density(self, npz_path: str):
        self.load_maps(npz_path)

    # ------------------------------------------------------------
    # DEM load + mesh build
    # ------------------------------------------------------------

    def _rebuild_dem_from_raw(self, update_center: bool = False):
        if self._dem_raw is None:
            return

        perf = self.cfg.get("performance", default_settings()["performance"])
        round_dec = int(perf.get("dedupe_round_decimals", 6))
        max_points = int(perf.get("max_points", 250000))

        dem_work = self._dem_raw

        # optional upscaling
        if hasattr(self, "chk_upscale_dem") and self.chk_upscale_dem.isChecked():
            factor = int(self.spin_upscale_factor.value()) if hasattr(self, "spin_upscale_factor") else 2
            dem_up, meta = upscale_dem_bilinear_points(dem_work, factor=factor, round_decimals=round_dec)
            dem_work = dem_up

            # prevent memory blow-up; also avoid losing the upscaling immediately
            max_points = min(int(max_points * (factor ** 2)), 2_000_000)

            if meta.get("used") is False:
                self.lbl_info.setText(f"DEM upscale skipped: {meta.get('reason', 'unknown')}")
            else:
                self.lbl_info.setText(
                    f"DEM upscaled x{meta.get('factor')}  ({meta.get('nx0')}x{meta.get('ny0')} -> {meta.get('nx1')}x{meta.get('ny1')})"
                )

        DEM = sanitize_dem_points(
            dem_work,
            dedupe_round_decimals=round_dec,
            max_points=max_points,
        )

        self.pts_xyz = DEM.astype(np.float32)

        x = self.pts_xyz[:, 0].astype(np.float64)
        y = self.pts_xyz[:, 1].astype(np.float64)
        z = self.pts_xyz[:, 2].astype(np.float64)

        idx0 = int(np.argmin((x - 0.0) ** 2 + (y - 0.0) ** 2))
        self.default_z_at_0_0 = float(z[idx0])

        if update_center:
            self.edit_cx.setText("0.0")
            self.edit_cy.setText("0.0")
            self.edit_cz.setText(f"{self.default_z_at_0_0:.6f}")

        tri = mtri.Triangulation(x, y)
        self.triangles = tri.triangles.astype(np.int32)

        P = self.pts_xyz.astype(np.float64)
        t = self.triangles
        self.face_centroids = (P[t[:, 0]] + P[t[:, 1]] + P[t[:, 2]]) / 3.0

        self._rebuild_mesh()
        self._ensure_reference_items()
        self._update_reference_geometry(
            grid_spacing=float(self.cfg.get("grid", {}).get("spacing", 100.0)),
            tick_step=float(self.cfg.get("height_axis", {}).get("tick_step", 100.0)),
        )
    def _freeze_gl_updates(self, freeze: bool):
        """
        Prevent transient OpenGL artifacts during heavy mesh rebuilds.

        When changing the DEM upscale factor, we rebuild triangulation + mesh.
        GLViewWidget may repaint between "remove old items" and "new VBO ready",
        which can show a brief frame with wrong / "smeared" colors.

        Strategy:
          - disable QWidget updates (stops paintGL)
          - hide current GL items
          - after rebuild, re-enable and let update_scene redraw normally
        """
        if not hasattr(self, "_gl_updates_frozen"):
            self._gl_updates_frozen = False

        if freeze and not self._gl_updates_frozen:
            self._gl_updates_frozen = True
            try:
                self.view.setUpdatesEnabled(False)
            except Exception:
                pass
            for it in (
                self.mesh_item,
                self.slice_plane_y, self.slice_border_y, self.slice_lines_glow_y, self.slice_lines_main_y,
                self.slice_plane_x, self.slice_border_x, self.slice_lines_glow_x, self.slice_lines_main_x,
                self.base_grid_item, self.z_axis_item, self.z_ticks_item,
            ):
                try:
                    if it is not None:
                        it.setVisible(False)
                except Exception:
                    pass

        elif (not freeze) and self._gl_updates_frozen:
            self._gl_updates_frozen = False
            try:
                self.view.setUpdatesEnabled(True)
            except Exception:
                pass
            # Terrain should be visible again; slice vis is handled by update_scene.
            try:
                if self.mesh_item is not None:
                    self.mesh_item.setVisible(True)
            except Exception:
                pass
            try:
                self.view.update()
            except Exception:
                pass
    def _schedule_upscale_rebuild(self, update_center: bool = False):
        """Debounced DEM+mesh rebuild (used when changing upscale options)."""
        if self._dem_raw is None:
            return

        # If we are not already pending, freeze GL updates immediately so the
        # user will NOT see any intermediate frame (this is the key fix).
        if not getattr(self, "_pending_upscale_rebuild", False):
            self._freeze_gl_updates(True)

        self._pending_upscale_rebuild = True
        self._pending_upscale_update_center = bool(update_center)

        # restart timer to coalesce rapid changes
        try:
            self._upscale_rebuild_timer.stop()
        except Exception:
            pass
        self._upscale_rebuild_timer.start()

    def _apply_upscale_rebuild(self):
        """Timer callback: rebuild DEM/triangulation/mesh safely, then redraw."""
        if (not getattr(self, "_pending_upscale_rebuild", False)) or (self._dem_raw is None):
            # If we were frozen but no rebuild is needed, unfreeze.
            self._freeze_gl_updates(False)
            return

        self._pending_upscale_rebuild = False

        self._rebuilding_dem = True
        try:
            self._rebuild_dem_from_raw(update_center=bool(getattr(self, "_pending_upscale_update_center", False)))
        finally:
            self._rebuilding_dem = False
            # IMPORTANT: re-enable painting only after the mesh is fully rebuilt.
            self._freeze_gl_updates(False)

        # redraw after the event loop has had a chance to process GL state changes
        QTimer.singleShot(0, self.update_scene)

    def load_dem(self, npz_path: str):
        path = resolve_asset_path(npz_path)
        if path is None or not path.exists():
            raise ValueError(f"DEM file not found: {npz_path}")

        d = np.load(path, allow_pickle=True)
        if "DEM" not in d.files:
            raise ValueError("NPZ missing key 'DEM'")

        self._dem_raw = d["DEM"]

        perf = self.cfg.get("performance", default_settings()["performance"])
        self._last_perf_key = (int(perf.get("max_points", 250000)), int(perf.get("dedupe_round_decimals", 6)))

        self._rebuild_dem_from_raw(update_center=True)

    def reset_z_to_dem_0_0(self):
        if self.default_z_at_0_0 is None:
            return
        self.edit_cz.setText(f"{self.default_z_at_0_0:.6f}")
        self.update_scene()

    def _remove_item(self, it):
        if it is None:
            return
        try:
            self.view.removeItem(it)
        except Exception:
            pass

    def _rebuild_mesh(self):
        for it in (
            self.mesh_item,
            self.slice_plane_y, self.slice_border_y, self.slice_lines_glow_y, self.slice_lines_main_y,
            self.slice_plane_x, self.slice_border_x, self.slice_lines_glow_x, self.slice_lines_main_x,
        ):
            self._remove_item(it)

        self.mesh_data = gl.MeshData(vertexes=self.pts_xyz, faces=self.triangles)

        # base shading by height
        cz = self.face_centroids[:, 2].astype(np.float64)
        lo, hi = float(np.min(cz)), float(np.max(cz))
        if abs(hi - lo) < 1e-12:
            hi = lo + 1.0
        tt = (cz - lo) / (hi - lo)
        g = (0.30 + 0.70 * tt).astype(np.float32)
        base = np.column_stack([g, g, g, np.ones_like(g, dtype=np.float32)])

        self._height_min = float(lo)
        self._height_max = float(hi)
        self.base_face_colors = base.astype(np.float32, copy=False)
        self.face_colors_work = self.base_face_colors.copy()
        self.mesh_data.setFaceColors(self.face_colors_work)

        shader = str(self.cfg.get("mesh", {}).get("shader", "balloon"))
        self.mesh_item = gl.GLMeshItem(meshdata=self.mesh_data, smooth=True, drawEdges=False, shader=shader)
        self.mesh_item.setGLOptions(str(self.cfg.get("mesh", {}).get("gl_opaque", "opaque")))
        self.view.addItem(self.mesh_item)

        # ---- θy slice items ----
        self.slice_plane_y = gl.GLMeshItem(meshdata=gl.MeshData(), smooth=False, drawEdges=False, shader=shader)
        self.slice_plane_y.setGLOptions("translucent")
        self.slice_plane_y.setVisible(False)
        self.view.addItem(self.slice_plane_y)

        self.slice_border_y = gl.GLLinePlotItem(
            pos=np.zeros((2, 3), dtype=np.float32),
            mode="line_strip",
            width=3.0,
            antialias=True
        )
        self.slice_border_y.setVisible(False)
        self.view.addItem(self.slice_border_y)

        self.slice_lines_glow_y = gl.GLLinePlotItem(
            pos=np.zeros((2, 3), dtype=np.float32),
            mode="lines",
            width=6.0,
            antialias=True
        )
        self.slice_lines_glow_y.setVisible(False)
        self.view.addItem(self.slice_lines_glow_y)

        self.slice_lines_main_y = gl.GLLinePlotItem(
            pos=np.zeros((2, 3), dtype=np.float32),
            mode="lines",
            width=2.5,
            antialias=True
        )
        self.slice_lines_main_y.setVisible(False)
        self.view.addItem(self.slice_lines_main_y)

        # ---- θx slice items ----
        self.slice_plane_x = gl.GLMeshItem(meshdata=gl.MeshData(), smooth=False, drawEdges=False, shader=shader)
        self.slice_plane_x.setGLOptions("translucent")
        self.slice_plane_x.setVisible(False)
        self.view.addItem(self.slice_plane_x)

        self.slice_border_x = gl.GLLinePlotItem(
            pos=np.zeros((2, 3), dtype=np.float32),
            mode="line_strip",
            width=3.0,
            antialias=True
        )
        self.slice_border_x.setVisible(False)
        self.view.addItem(self.slice_border_x)

        self.slice_lines_glow_x = gl.GLLinePlotItem(
            pos=np.zeros((2, 3), dtype=np.float32),
            mode="lines",
            width=6.0,
            antialias=True
        )
        self.slice_lines_glow_x.setVisible(False)
        self.view.addItem(self.slice_lines_glow_x)

        self.slice_lines_main_x = gl.GLLinePlotItem(
            pos=np.zeros((2, 3), dtype=np.float32),
            mode="lines",
            width=2.5,
            antialias=True
        )
        self.slice_lines_main_x.setVisible(False)
        self.view.addItem(self.slice_lines_main_x)

    # ============================================================
    # Reference: Base grid plane + height axis
    # ============================================================

    def _ensure_reference_items(self):
        if self.base_grid_item is None:
            self.base_grid_item = gl.GLGridItem()
            try:
                self.base_grid_item.setColor(tuple(int(x) for x in self.cfg["grid"]["color"]))
            except Exception:
                pass
            self.base_grid_item.setGLOptions("translucent")
            self.base_grid_item.setVisible(False)
            self.view.addItem(self.base_grid_item)

        if self.z_axis_item is None:
            self.z_axis_item = gl.GLLinePlotItem(
                pos=np.zeros((2, 3), dtype=np.float32),
                mode="line_strip",
                width=2.0,
                antialias=True
            )
            self.z_axis_item.setVisible(False)
            self.view.addItem(self.z_axis_item)
            try:
                self.z_axis_item.setGLOptions("additive")
            except Exception:
                pass
            try:
                self.z_axis_item.setDepthValue(1000)
            except Exception:
                pass

        if self.z_ticks_item is None:
            self.z_ticks_item = gl.GLLinePlotItem(
                pos=np.zeros((2, 3), dtype=np.float32),
                mode="lines",
                width=1.5,
                antialias=True
            )
            self.z_ticks_item.setVisible(False)
            self.view.addItem(self.z_ticks_item)
            try:
                self.z_ticks_item.setGLOptions("additive")
            except Exception:
                pass
            try:
                self.z_ticks_item.setDepthValue(1001)
            except Exception:
                pass

    def _update_reference_geometry(self, grid_spacing=100.0, tick_step=100.0):
        if self.pts_xyz is None or self.default_z_at_0_0 is None:
            return
        self._ensure_reference_items()

        x = self.pts_xyz[:, 0].astype(float)
        y = self.pts_xyz[:, 1].astype(float)
        z = self.pts_xyz[:, 2].astype(float)

        hx = max(abs(float(np.min(x))), abs(float(np.max(x))), 50.0)
        hy = max(abs(float(np.min(y))), abs(float(np.max(y))), 50.0)

        size_x = _ceil_to_step(2.0 * hx, grid_spacing)
        size_y = _ceil_to_step(2.0 * hy, grid_spacing)

        z0 = float(self.default_z_at_0_0)

        try:
            self.base_grid_item.setColor(tuple(int(v) for v in self.cfg.get("grid", {}).get("color", [120, 120, 120, 90])))
        except Exception:
            pass

        self.base_grid_item.resetTransform()
        self.base_grid_item.setSize(x=size_x, y=size_y, z=1)
        self.base_grid_item.setSpacing(x=float(grid_spacing), y=float(grid_spacing), z=1)
        self.base_grid_item.translate(0.0, 0.0, z0)

        zmin = float(np.min(z))
        zmax = float(np.max(z))
        pad = 0.05 * (zmax - zmin if zmax > zmin else 1.0)
        zmin2 = zmin - pad
        zmax2 = zmax + pad

        axis_pts = np.array([[0.0, 0.0, zmin2],
                             [0.0, 0.0, zmax2]], dtype=np.float32)

        tick_len = 0.03 * max(size_x, size_y)
        tick_len = float(np.clip(tick_len, 10.0, 80.0))

        t0 = _ceil_to_step(zmin2, tick_step)
        ticks = []
        zz = t0
        while zz <= zmax2 + 1e-6:
            ticks.append(((0.0, 0.0, zz), (tick_len, 0.0, zz)))
            zz += tick_step

        if ticks:
            tick_pts = np.array([p for seg in ticks for p in seg], dtype=np.float32)
        else:
            tick_pts = np.zeros((2, 3), dtype=np.float32)

        ha = self.cfg.get("height_axis", default_settings()["height_axis"])
        axis_col = rgba255_to_gl(ha.get("axis_color", [255, 128, 51, 255]))
        ticks_col = rgba255_to_gl(ha.get("ticks_color", [255, 128, 51, 242]))

        self.z_axis_item.setData(pos=axis_pts, color=axis_col)
        self.z_ticks_item.setData(pos=tick_pts, color=ticks_col)

    def _set_reference_visibility(self):
        if self.base_grid_item is not None:
            self.base_grid_item.setVisible(self.chk_base_grid.isChecked())
        if self.z_axis_item is not None:
            self.z_axis_item.setVisible(self.chk_height_axis.isChecked())
        if self.z_ticks_item is not None:
            self.z_ticks_item.setVisible(self.chk_height_axis.isChecked())

    # ------------------------------------------------------------
    # colorbar
    # ------------------------------------------------------------

    def _update_colorbar_widget(self, lo, hi):
        lo = float(lo)
        hi = float(hi)
        if (not np.isfinite(lo)) or (not np.isfinite(hi)) or (hi <= lo):
            lo, hi = 0.0, 1.0
        self.cb_img.setRect(pg.QtCore.QRectF(lo, 0.0, hi - lo, 1.0))
        self.cb_view.setRange(xRange=(lo, hi), yRange=(0.0, 1.0), padding=0.0)
        self.cb_axis.setRange(lo, hi)
        self._animate_colorbar_change(lo, hi)

    def _animate_colorbar_change(self, lo, hi, tol=1e-4):
        new_rng = (float(lo), float(hi))
        prev = self._last_colorbar_range
        changed = (
            prev is None
            or abs(new_rng[0] - prev[0]) > tol
            or abs(new_rng[1] - prev[1]) > tol
        )
        self._last_colorbar_range = new_rng
        if changed:
            self._pulse_widget(self.cb_plot)

    # ============================================================
    # main update
    # ============================================================

    def update_scene(self):
        # During a DEM rebuild we may have a partially-updated GLMeshItem.
        # Drawing in this state can show "colors everywhere" until the next repaint.
        if getattr(self, "_rebuilding_dem", False):
            return
        if self.pts_xyz is None or self.triangles is None or self.face_centroids is None:
            return

        self._ensure_reference_items()

        grid_spacing = float(self.cfg.get("grid", {}).get("spacing", 100.0))
        tick_step = float(self.cfg.get("height_axis", {}).get("tick_step", 100.0))
        self._update_reference_geometry(grid_spacing=grid_spacing, tick_step=tick_step)
        self._set_reference_visibility()

        cx = float(self.edit_cx.text() or "0")
        cy = float(self.edit_cy.text() or "0")
        cz = float(self.edit_cz.text() or "0")
        det_center = np.array([cx, cy, cz], dtype=float)

        zen = float(self.edit_zen.text() or "76.6")
        az = float(self.edit_az.text() or "90.0")
        fovx = np.radians(float(self.edit_fovx.text() or "13.0"))
        fovy = np.radians(float(self.edit_fovy.text() or "13.0"))

        show_fov = self.chk_fov.isChecked()

        # Overlay selection
        try:
            overlay_key = self.combo_overlay.currentData()
        except Exception:
            overlay_key = "RHO"

        try:
            scale_mode = str(self.combo_scale.currentData() or "linear").lower()
        except Exception:
            scale_mode = "linear"

        self._update_colorbar_label_from_ui()

        show_overlay = (
            self.chk_density.isChecked()
            and getattr(self, "maps_loaded", False)
            and (overlay_key in getattr(self, "maps_interps", {}))
        )

        show_slice_y = self.chk_slice_y.isChecked()
        show_slice_x = self.chk_slice_x.isChecked()
        show_any_slice = show_slice_y or show_slice_x

        zprime = boresight_from_zen_az(zen, az)
        xprime, yprime, zprime = detector_frame_from_boresight(zprime)

        theta_x, theta_y, vz = project_to_detector_thetas(self.face_centroids, det_center, xprime, yprime, zprime)
        infront = (vz > 0.0)
        fov_mask = infront & (np.abs(theta_x) <= fovx) & (np.abs(theta_y) <= fovy)
        height_lo = self._height_min
        height_hi = self._height_max
        if (
            (height_lo is None) or (height_hi is None) or
            (not np.isfinite(height_lo)) or (not np.isfinite(height_hi)) or
            (height_hi <= height_lo)
        ):
            heights_all = np.asarray(self.face_centroids[:, 2], dtype=float)
            if heights_all.size == 0 or (not np.any(np.isfinite(heights_all))):
                height_lo, height_hi = 0.0, 1.0
            else:
                height_lo = float(np.nanmin(heights_all))
                height_hi = float(np.nanmax(heights_all))
                if (not np.isfinite(height_lo)) or (not np.isfinite(height_hi)) or (height_hi <= height_lo):
                    height_hi = height_lo + 1.0

        default_ranges = {
            "RHO": (1.5, 2.5),
            "FLUX": (0.0, 1.0),
            "THICK": (0.0, 1.0),
        }
        default_lo, default_hi = default_ranges.get(str(overlay_key).upper(), (0.0, 1.0))

        lo_cb, hi_cb = float(default_lo), float(default_hi)
        val_in = None

        if show_overlay and np.any(fov_mask):
            interp = self.maps_interps.get(str(overlay_key).upper(), None)
            if interp is not None:
                val = interp(theta_x[fov_mask], theta_y[fov_mask])
                val = np.asarray(val, dtype=float).ravel()

                if scale_mode == "log10":
                    good = np.isfinite(val) & (val > 0.0)
                    tmp = np.full(val.shape, np.nan, dtype=float)
                    tmp[good] = np.log10(val[good])
                    val = tmp

                good = np.isfinite(val)
                if np.any(good):
                    vv = val[good]
                    lo_cb = float(np.min(vv))
                    hi_cb = float(np.max(vv))
                    if (not np.isfinite(lo_cb)) or (not np.isfinite(hi_cb)) or abs(hi_cb - lo_cb) < 1e-12:
                        lo_cb, hi_cb = float(default_lo), float(default_hi)

                val_in = val

        self._update_colorbar_widget(lo_cb, hi_cb)

        mesh_cfg = self.cfg.get("mesh", default_settings()["mesh"])
        ov = self.cfg.get("overlay", default_settings()["overlay"])
        fov_use_cmap = bool(ov.get("fov_use_colormap", False))
        fov_cmap_lut = getattr(self, "_fov_lut", None)

        # NOTE:
        # Using GL 'translucent' on a big triangle mesh causes depth-sorting artifacts
        # (colors look like they "bleed" / stripe across the terrain) because triangles
        # are not depth-sorted. Instead, keep the terrain OPAQUE and implement "dimming"
        # by scaling RGB when a slice is enabled.
        mesh_dim = float(mesh_cfg.get("alpha_dim", 0.55) if show_any_slice else mesh_cfg.get("alpha_normal", 1.0))
        den_dim  = float(ov.get("density_alpha_dim", 0.8) if show_any_slice else ov.get("density_alpha_normal", 1.0))
        fov_dim  = float(ov.get("fov_alpha_dim", 0.55) if show_any_slice else ov.get("fov_alpha_normal", 1.0))
        inv_dim  = float(ov.get("invalid_alpha_dim", 0.30) if show_any_slice else ov.get("invalid_alpha_normal", 1.0))

        fov_rgba255 = ov.get("fov_color", [255, 217, 26, 255])
        inv_rgba255 = ov.get("invalid_color", [255, 217, 26, 255])

        fov_rgb = (np.array(fov_rgba255[:3], dtype=np.float32) / 255.0)
        inv_rgb = (np.array(inv_rgba255[:3], dtype=np.float32) / 255.0)

        fc = self.face_colors_work
        fc[:] = self.base_face_colors
        fc[:, :3] *= mesh_dim
        fc[:, 3] = 1.0

        # Always draw the terrain as opaque (no blending) to avoid per-triangle translucency artifacts.
        try:
            self.mesh_item.setGLOptions(str(mesh_cfg.get("gl_opaque", "opaque")))
        except Exception:
            pass

        if show_overlay and np.any(fov_mask) and (val_in is not None):
            rgba, valid = self._map_rho_to_rgba(val_in, lo_cb, hi_cb)
            rgba[:, :3] *= den_dim
            rgba[:, 3] = 1.0

            fov_idx = np.nonzero(fov_mask)[0]
            if np.any(valid):
                fc[fov_idx[valid]] = rgba[valid].astype(np.float32, copy=False)

            if show_fov:
                inv = ~valid
                if np.any(inv):
                    tmp = np.zeros((np.count_nonzero(inv), 4), dtype=np.float32)
                    tmp[:, :3] = inv_rgb[None, :] * inv_dim
                    tmp[:, 3] = 1.0
                    fc[fov_idx[inv]] = tmp

        elif show_fov and np.any(fov_mask):
            if fov_use_cmap and (fov_cmap_lut is not None):
                heights_fov = self.face_centroids[fov_mask, 2].astype(np.float64)
                rgba_h, valid_h = self._map_values_to_rgba(heights_fov, height_lo, height_hi, fov_cmap_lut)
                rgba_h[:, :3] *= fov_dim
                rgba_h[:, 3] = 1.0
                if np.any(valid_h):
                    fc[fov_mask] = rgba_h
                else:
                    tmp = np.zeros((np.count_nonzero(fov_mask), 4), dtype=np.float32)
                    tmp[:, :3] = fov_rgb[None, :] * fov_dim
                    tmp[:, 3] = 1.0
                    fc[fov_mask] = tmp
            else:
                tmp = np.zeros((np.count_nonzero(fov_mask), 4), dtype=np.float32)
                tmp[:, :3] = fov_rgb[None, :] * fov_dim
                tmp[:, 3] = 1.0
                fc[fov_mask] = tmp

        self.mesh_data.setFaceColors(fc)
        self.mesh_item.setMeshData(meshdata=self.mesh_data)

        if show_slice_y:
            self._update_slice_y(det_center, xprime, yprime, zprime, fovx, fovy)
        else:
            self._hide_slice_y()

        if show_slice_x:
            self._update_slice_x(det_center, xprime, yprime, zprime, fovx, fovy)
        else:
            self._hide_slice_x()

        n_faces = int(fov_mask.size)
        n_in = int(np.count_nonzero(fov_mask))
        overlay_name = "None" if not show_overlay else self._field_display_name(overlay_key)
        self.lbl_info.setText(
            f"faces in FOV: {n_in}/{n_faces} | overlay={overlay_name} | scale={scale_mode} | range=[{lo_cb:.3g},{hi_cb:.3g}] | center=({cx:.2f},{cy:.2f},{cz:.2f})"
        )
        self._pulse_widget(self.lbl_info)
        # Force a GL repaint. (Without this, face colors can look 'stale' until the next user interaction.)
        try:
            # Some pyqtgraph versions need an explicit dirty flag.
            if hasattr(self.mesh_item, "meshDataChanged"):
                self.mesh_item.meshDataChanged()
        except Exception:
            pass
        try:
            self.mesh_item.update()
        except Exception:
            pass
        try:
            self.view.update()
        except Exception:
            pass


    # ============================================================
    # θy slice
    # ============================================================

    def _hide_slice_y(self):
        self.slice_plane_y.setVisible(False)
        self.slice_border_y.setVisible(False)
        self.slice_lines_glow_y.setVisible(False)
        self.slice_lines_main_y.setVisible(False)

    def _update_slice_y(self, det_center, xprime, yprime, zprime, fovx, fovy):
        theta_y_deg = float(self.spin_slice_y.value())
        self.lbl_slice_y.setText(f"θy = {theta_y_deg:.1f}°")
        theta_y = np.radians(theta_y_deg)

        dir_L = direction_from_detector_thetas(-fovx, theta_y, xprime, yprime, zprime)
        dir_R = direction_from_detector_thetas(+fovx, theta_y, xprime, yprime, zprime)
        dir_C = direction_from_detector_thetas(0.0, theta_y, xprime, yprime, zprime)

        plane_n = _unit(np.cross(dir_C, xprime))
        if np.linalg.norm(plane_n) < 1e-10:
            plane_n = _unit(np.cross(dir_C, yprime))

        dists = np.linalg.norm(self.pts_xyz.astype(np.float64) - det_center[None, :], axis=1)
        far = float(np.nanmax(dists)) if dists.size else 1000.0
        far = max(far, 10.0)
        near = max(1.0, 0.02 * far)

        A = det_center + near * dir_L
        B = det_center + near * dir_R
        C = det_center + far * dir_R
        D = det_center + far * dir_L

        quad_v = np.asarray([A, B, C, D], dtype=np.float32)
        quad_f = np.asarray([[0, 1, 2], [0, 2, 3]], dtype=np.int32)
        md = gl.MeshData(vertexes=quad_v, faces=quad_f)
        self.slice_plane_y.setMeshData(meshdata=md)

        sc = self.cfg.get("slices", default_settings()["slices"])["y"]
        self.slice_plane_y.setColor(rgba255_to_gl(sc["plane_color"]))
        self.slice_plane_y.setVisible(True)

        border = np.asarray([A, B, C, D, A], dtype=np.float32)
        self.slice_border_y.setData(pos=border, color=rgba255_to_gl(sc["border_color"]), width=float(sc["border_width"]))
        self.slice_border_y.setVisible(True)

        eps = float(self.cfg.get("performance", default_settings()["performance"]).get("intersection_eps", 1e-8))
        segs = triangle_plane_intersections(
            self.pts_xyz.astype(np.float64),
            self.triangles,
            plane_n,
            det_center,
            eps=eps
        )

        if segs.shape[0] > 0:
            mids = 0.5 * (segs[:, 0, :] + segs[:, 1, :])
            thx_m, thy_m, vz_m = project_to_detector_thetas(mids, det_center, xprime, yprime, zprime)
            keep = (vz_m > 0.0) & (np.abs(thx_m) <= fovx + 1e-12) & (np.abs(thy_m) <= fovy + 1e-12)
            segs = segs[keep]

        if segs.shape[0] == 0:
            self.slice_lines_glow_y.setVisible(False)
            self.slice_lines_main_y.setVisible(False)
            return

        MAX_SEGS = int(self.cfg.get("slices", default_settings()["slices"]).get("max_segs", 200000))
        if segs.shape[0] > MAX_SEGS:
            step = int(np.ceil(segs.shape[0] / MAX_SEGS))
            segs = segs[::max(1, step)]

        pts = segs.reshape(-1, 3).astype(np.float32)
        self.slice_lines_glow_y.setData(pos=pts, color=rgba255_to_gl(sc["line_glow"]), width=float(sc["glow_width"]))
        self.slice_lines_main_y.setData(pos=pts, color=rgba255_to_gl(sc["line_main"]), width=float(sc["main_width"]))
        self.slice_lines_glow_y.setVisible(True)
        self.slice_lines_main_y.setVisible(True)

    # ============================================================
    # θx slice
    # ============================================================

    def _hide_slice_x(self):
        self.slice_plane_x.setVisible(False)
        self.slice_border_x.setVisible(False)
        self.slice_lines_glow_x.setVisible(False)
        self.slice_lines_main_x.setVisible(False)

    def _update_slice_x(self, det_center, xprime, yprime, zprime, fovx, fovy):
        theta_x_deg = float(self.spin_slice_x.value())
        self.lbl_slice_x.setText(f"θx = {theta_x_deg:.1f}°")
        theta_x = np.radians(theta_x_deg)

        dir_B = direction_from_detector_thetas(theta_x, -fovy, xprime, yprime, zprime)
        dir_T = direction_from_detector_thetas(theta_x, +fovy, xprime, yprime, zprime)
        dir_C = direction_from_detector_thetas(theta_x, 0.0, xprime, yprime, zprime)

        plane_n = _unit(np.cross(dir_C, yprime))
        if np.linalg.norm(plane_n) < 1e-10:
            plane_n = _unit(np.cross(dir_C, xprime))

        dists = np.linalg.norm(self.pts_xyz.astype(np.float64) - det_center[None, :], axis=1)
        far = float(np.nanmax(dists)) if dists.size else 1000.0
        far = max(far, 10.0)
        near = max(1.0, 0.02 * far)

        A = det_center + near * dir_B
        B = det_center + near * dir_T
        C = det_center + far * dir_T
        D = det_center + far * dir_B

        quad_v = np.asarray([A, B, C, D], dtype=np.float32)
        quad_f = np.asarray([[0, 1, 2], [0, 2, 3]], dtype=np.int32)
        md = gl.MeshData(vertexes=quad_v, faces=quad_f)
        self.slice_plane_x.setMeshData(meshdata=md)

        sc = self.cfg.get("slices", default_settings()["slices"])["x"]
        self.slice_plane_x.setColor(rgba255_to_gl(sc["plane_color"]))
        self.slice_plane_x.setVisible(True)

        border = np.asarray([A, B, C, D, A], dtype=np.float32)
        self.slice_border_x.setData(pos=border, color=rgba255_to_gl(sc["border_color"]), width=float(sc["border_width"]))
        self.slice_border_x.setVisible(True)

        eps = float(self.cfg.get("performance", default_settings()["performance"]).get("intersection_eps", 1e-8))
        segs = triangle_plane_intersections(
            self.pts_xyz.astype(np.float64),
            self.triangles,
            plane_n,
            det_center,
            eps=eps
        )

        if segs.shape[0] > 0:
            mids = 0.5 * (segs[:, 0, :] + segs[:, 1, :])
            thx_m, thy_m, vz_m = project_to_detector_thetas(mids, det_center, xprime, yprime, zprime)
            keep = (vz_m > 0.0) & (np.abs(thx_m) <= fovx + 1e-12) & (np.abs(thy_m) <= fovy + 1e-12)
            segs = segs[keep]

        if segs.shape[0] == 0:
            self.slice_lines_glow_x.setVisible(False)
            self.slice_lines_main_x.setVisible(False)
            return

        MAX_SEGS = int(self.cfg.get("slices", default_settings()["slices"]).get("max_segs", 200000))
        if segs.shape[0] > MAX_SEGS:
            step = int(np.ceil(segs.shape[0] / MAX_SEGS))
            segs = segs[::max(1, step)]

        pts = segs.reshape(-1, 3).astype(np.float32)
        self.slice_lines_glow_x.setData(pos=pts, color=rgba255_to_gl(sc["line_glow"]), width=float(sc["glow_width"]))
        self.slice_lines_main_x.setData(pos=pts, color=rgba255_to_gl(sc["line_main"]), width=float(sc["main_width"]))
        self.slice_lines_glow_x.setVisible(True)
        self.slice_lines_main_x.setVisible(True)

    # ------------------------------------------------------------
    # slice range sync
    # ------------------------------------------------------------

    def _update_slice_range_from_fovy(self, call_update=True):
        try:
            fovy_deg = float(self.edit_fovy.text() or "0")
        except Exception:
            fovy_deg = 0.0

        lim = abs(float(fovy_deg))
        new_min, new_max = -lim, lim

        cur = float(self.spin_slice_y.value())
        cur = max(new_min, min(new_max, cur))

        self.spin_slice_y.blockSignals(True)
        self.slider_slice_y.blockSignals(True)
        try:
            self.spin_slice_y.setRange(new_min, new_max)
            self.slider_slice_y.setRange(
                int(np.floor(new_min * self.SLICE_SCALE_Y)),
                int(np.ceil(new_max * self.SLICE_SCALE_Y)),
            )
            self.spin_slice_y.setValue(cur)
            self.slider_slice_y.setValue(int(round(cur * self.SLICE_SCALE_Y)))
        finally:
            self.spin_slice_y.blockSignals(False)
            self.slider_slice_y.blockSignals(False)

        self.lbl_slice_y.setText(f"θy = {cur:.1f}°")
        if call_update:
            self.update_scene()

    def _update_slice_range_from_fovx(self, call_update=True):
        try:
            fovx_deg = float(self.edit_fovx.text() or "0")
        except Exception:
            fovx_deg = 0.0

        lim = abs(float(fovx_deg))
        new_min, new_max = -lim, lim

        cur = float(self.spin_slice_x.value())
        cur = max(new_min, min(new_max, cur))

        self.spin_slice_x.blockSignals(True)
        self.slider_slice_x.blockSignals(True)
        try:
            self.spin_slice_x.setRange(new_min, new_max)
            self.slider_slice_x.setRange(
                int(np.floor(new_min * self.SLICE_SCALE_X)),
                int(np.ceil(new_max * self.SLICE_SCALE_X)),
            )
            self.spin_slice_x.setValue(cur)
            self.slider_slice_x.setValue(int(round(cur * self.SLICE_SCALE_X)))
        finally:
            self.spin_slice_x.blockSignals(False)
            self.slider_slice_x.blockSignals(False)

        self.lbl_slice_x.setText(f"θx = {cur:.1f}°")
        if call_update:
            self.update_scene()


def launch_viewer(npz_path: str | os.PathLike | None = None, settings_path: str | os.PathLike | None = None):
    app = QApplication(sys.argv)
    apply_system_theme(app)
    app_icon = load_app_icon()
    if app_icon is not None:
        try:
            app.setWindowIcon(app_icon)
        except Exception:
            pass

    # 1) Show splash immediately (smooth startup)
    splash = StartupSplash(
        title_top="National Central University",
        title_main="Muography",
        subtitle="3D DEM Viewer",
        duration_ms=3200,
        sound=True,
        sound_path=str(resolve_asset_path("startup_sound.wav") or ""),
        app_icon=app_icon,
    )

    splash.show()

    state = {"viewer": None, "viewer_ready": False, "anim_done": False}

    def maybe_finish():
        if state["viewer_ready"] and state["anim_done"]:
            try:
                splash.close()
            except Exception:
                pass
            w = state["viewer"]
            w.show()
            QTimer.singleShot(0, w.update_scene)
            QTimer.singleShot(0, lambda: warmup_gl_widget(w.view))

    def build_viewer():
        # 2) Build the heavy OpenGL viewer while splash is visible
        w = DEMViewerPG(npz_path=str(npz_path or default_dem_path()), settings_path=settings_path)
        w.resize(1300, 900)
        state["viewer"] = w
        state["viewer_ready"] = True
        maybe_finish()

    def on_splash_finished():
        state["anim_done"] = True
        maybe_finish()

    splash.finished.connect(on_splash_finished)

    # Slight delay helps ensure splash is painted before heavy init begins
    QTimer.singleShot(50, build_viewer)

    sys.exit(app.exec())


if __name__ == "__main__":
    launch_viewer()
