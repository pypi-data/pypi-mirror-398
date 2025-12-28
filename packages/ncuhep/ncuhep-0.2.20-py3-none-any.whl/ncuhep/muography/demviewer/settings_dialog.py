# settings_dialog.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import copy
from typing import Any, Dict, Optional, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QLabel, QComboBox, QDoubleSpinBox, QSpinBox,
    QCheckBox, QColorDialog, QFileDialog, QMessageBox
)


# ------------------------------------------------------------
# defaults + IO + helpers
# ------------------------------------------------------------

def default_settings() -> Dict[str, Any]:
    """
    All colors are stored as RGBA 0..255 lists so it is JSON friendly.
    """
    return {
        "version": 1,

        "appearance": {
            "background": [30, 30, 30, 255],
            "colormap": "viridis",
        },

        "camera": {
            "distance": 800.0,
            "elevation": 30.0,
            "azimuth": -60.0,
            "fov": 60.0,
            "perspective": True,  # applied only if GLViewWidget supports it
        },

        "mesh": {
            "shader": "balloon",
            "alpha_normal": 1.0,   # when no slice
            "alpha_dim": 0.55,     # when any slice enabled
            "gl_opaque": "opaque",
            "gl_translucent": "translucent",
        },

        "overlay": {
            "density_alpha_normal": 1.0,
            "density_alpha_dim": 0.80,

            # FOV color used when "Show FOV mask" with no density overlay
            "fov_color": [255, 217, 26, 255],
            "fov_alpha_normal": 1.0,
            "fov_alpha_dim": 0.55,
            "fov_use_colormap": False,
            "fov_colormap": "viridis",

            # "invalid density" color inside FOV when density overlay is on but rho is NaN
            "invalid_color": [255, 217, 26, 255],
            "invalid_alpha_normal": 1.0,
            "invalid_alpha_dim": 0.30,
        },

        "grid": {
            "color": [120, 120, 120, 90],
            "spacing": 100.0,
        },

        "height_axis": {
            "axis_color": [255, 128, 51, 255],
            "ticks_color": [255, 128, 51, 242],
            "tick_step": 100.0,
        },

        "slices": {
            "max_segs": 200000,  # max intersection segments to draw

            "y": {
                "plane_color":  [38, 217, 255, 56],
                "border_color": [38, 217, 255, 242],
                "line_main":    [255, 242, 51, 255],
                "line_glow":    [255, 242, 51, 56],
                "border_width": 3.0,
                "main_width":   2.5,
                "glow_width":   6.0,
            },

            "x": {
                "plane_color":  [242, 64, 242, 46],
                "border_color": [242, 64, 242, 242],
                "line_main":    [64, 255, 64, 255],
                "line_glow":    [64, 255, 64, 51],
                "border_width": 3.0,
                "main_width":   2.5,
                "glow_width":   6.0,
            },
        },

        "performance": {
            "max_points": 250000,
            "dedupe_round_decimals": 6,
            "intersection_eps": 1e-8,
        },
    }


def deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


def load_settings(path: str, defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = copy.deepcopy(defaults or default_settings())
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                deep_update(cfg, data)
        except Exception:
            # if file is corrupted, ignore and keep defaults
            pass
    return cfg


def save_settings(path: str, cfg: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def rgba255_to_gl(rgba: List[int]) -> tuple:
    r, g, b, a = [int(x) for x in rgba]
    return (r / 255.0, g / 255.0, b / 255.0, a / 255.0)


def clamp_rgba(rgba: List[int]) -> List[int]:
    if rgba is None or len(rgba) != 4:
        return [0, 0, 0, 255]
    out = []
    for i, x in enumerate(rgba):
        xi = int(round(float(x)))
        if i < 3:
            out.append(max(0, min(255, xi)))
        else:
            out.append(max(0, min(255, xi)))
    return out


# ------------------------------------------------------------
# small UI: ColorButton
# ------------------------------------------------------------

class ColorButton(QPushButton):
    rgbaChanged = pyqtSignal(list)

    def __init__(self, label: str = "", rgba: Optional[List[int]] = None, parent=None):
        super().__init__(parent)
        self.setText(label)
        self._rgba = clamp_rgba(rgba or [255, 255, 255, 255])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._pick)
        self._sync_style()

    def rgba(self) -> List[int]:
        return list(self._rgba)

    def set_rgba(self, rgba: List[int]):
        self._rgba = clamp_rgba(rgba)
        self._sync_style()
        self.rgbaChanged.emit(self.rgba())

    def _sync_style(self):
        r, g, b, a = self._rgba
        # show the color as button background
        # keep text readable-ish (simple heuristic)
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        fg = "black" if lum > 140 else "white"
        self.setStyleSheet(
            f"QPushButton {{"
            f"background-color: rgba({r},{g},{b},{a});"
            f"color: {fg};"
            f"padding: 6px;"
            f"}}"
        )

    def _pick(self):
        r, g, b, a = self._rgba
        q0 = QColor(r, g, b, a)
        q = QColorDialog.getColor(q0, self, "Pick Color", options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if q.isValid():
            self.set_rgba([q.red(), q.green(), q.blue(), q.alpha()])


# ------------------------------------------------------------
# Settings Dialog
# ------------------------------------------------------------

class SettingsDialog(QDialog):
    """
    A comprehensive settings dialog.
    Emits settingsApplied(dict) when Apply/OK is pressed.
    """
    settingsApplied = pyqtSignal(dict)

    def __init__(self, cfg: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Viewer Preferences")
        self.setModal(True)
        self.resize(720, 540)

        self._base_defaults = default_settings()
        self._cfg = copy.deepcopy(cfg)

        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # buttons row
        btn_row = QHBoxLayout()
        root.addLayout(btn_row)

        self.btn_load = QPushButton("Load…")
        self.btn_save = QPushButton("Save…")
        self.btn_reset = QPushButton("Reset to defaults")
        self.btn_apply = QPushButton("Apply")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_load.clicked.connect(self._load_clicked)
        self.btn_save.clicked.connect(self._save_clicked)
        self.btn_reset.clicked.connect(self._reset_clicked)
        self.btn_apply.clicked.connect(self._apply_clicked)
        self.btn_ok.clicked.connect(self._ok_clicked)
        self.btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_load)
        btn_row.addWidget(self.btn_save)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_reset)
        btn_row.addWidget(self.btn_apply)
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)

        # build tabs
        self._build_tab_appearance()
        self._build_tab_camera()
        self._build_tab_overlays()
        self._build_tab_slices()
        self._build_tab_reference()
        self._build_tab_performance()

        self._populate_widgets_from_cfg()

    # -------------------------
    # tabs
    # -------------------------

    def _build_tab_appearance(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)

        form = QFormLayout()
        lay.addLayout(form)
        lay.addStretch(1)

        self.btn_bg = ColorButton("Pick…", [30, 30, 30, 255])
        form.addRow("Background", self.btn_bg)

        self.cmb_cmap = QComboBox()
        for name in ["viridis", "plasma", "inferno", "magma", "cividis", "grey", "gray"]:
            self.cmb_cmap.addItem(name)
        form.addRow("Colormap (density)", self.cmb_cmap)

        self.cmb_shader = QComboBox()
        # common pyqtgraph shaders (some may not exist on older versions; you can still type/extend)
        for s in ["balloon", "shaded", "normalColor", "edgeHilight", "heightColor"]:
            self.cmb_shader.addItem(s)
        form.addRow("Mesh shader", self.cmb_shader)

        self.cmb_gl_opaque = QComboBox()
        for s in ["opaque", "translucent", "additive"]:
            self.cmb_gl_opaque.addItem(s)
        form.addRow("Mesh GL options (no slice)", self.cmb_gl_opaque)

        self.cmb_gl_trans = QComboBox()
        for s in ["translucent", "opaque", "additive"]:
            self.cmb_gl_trans.addItem(s)
        form.addRow("Mesh GL options (slice on)", self.cmb_gl_trans)

        self.tabs.addTab(tab, "Appearance")

    def _build_tab_camera(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        form = QFormLayout()
        lay.addLayout(form)
        lay.addStretch(1)

        self.sp_dist = QDoubleSpinBox(); self.sp_dist.setRange(1.0, 1e9); self.sp_dist.setDecimals(1); self.sp_dist.setSingleStep(10.0)
        self.sp_elev = QDoubleSpinBox(); self.sp_elev.setRange(-89.9, 89.9); self.sp_elev.setDecimals(1); self.sp_elev.setSingleStep(1.0)
        self.sp_azim = QDoubleSpinBox(); self.sp_azim.setRange(-3600.0, 3600.0); self.sp_azim.setDecimals(1); self.sp_azim.setSingleStep(5.0)
        self.sp_fov  = QDoubleSpinBox(); self.sp_fov.setRange(1.0, 179.0); self.sp_fov.setDecimals(1); self.sp_fov.setSingleStep(1.0)

        self.chk_persp = QCheckBox("Perspective (if supported by GLViewWidget)")
        self.chk_persp.setChecked(True)

        form.addRow("Distance", self.sp_dist)
        form.addRow("Elevation (deg)", self.sp_elev)
        form.addRow("Azimuth (deg)", self.sp_azim)
        form.addRow("Field of view (deg)", self.sp_fov)
        form.addRow(self.chk_persp)

        self.tabs.addTab(tab, "Camera")

    def _build_tab_overlays(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)

        g1 = QGroupBox("Opacity behavior")
        f1 = QFormLayout(g1)

        self.sp_mesh_alpha_normal = QDoubleSpinBox(); self.sp_mesh_alpha_normal.setRange(0.0, 1.0); self.sp_mesh_alpha_normal.setDecimals(3); self.sp_mesh_alpha_normal.setSingleStep(0.05)
        self.sp_mesh_alpha_dim = QDoubleSpinBox(); self.sp_mesh_alpha_dim.setRange(0.0, 1.0); self.sp_mesh_alpha_dim.setDecimals(3); self.sp_mesh_alpha_dim.setSingleStep(0.05)

        self.sp_den_alpha_normal = QDoubleSpinBox(); self.sp_den_alpha_normal.setRange(0.0, 1.0); self.sp_den_alpha_normal.setDecimals(3); self.sp_den_alpha_normal.setSingleStep(0.05)
        self.sp_den_alpha_dim = QDoubleSpinBox(); self.sp_den_alpha_dim.setRange(0.0, 1.0); self.sp_den_alpha_dim.setDecimals(3); self.sp_den_alpha_dim.setSingleStep(0.05)

        f1.addRow("Mesh alpha (no slice)", self.sp_mesh_alpha_normal)
        f1.addRow("Mesh alpha (slice enabled)", self.sp_mesh_alpha_dim)
        f1.addRow("Density alpha (no slice)", self.sp_den_alpha_normal)
        f1.addRow("Density alpha (slice enabled)", self.sp_den_alpha_dim)

        g2 = QGroupBox("FOV / invalid-density colors")
        f2 = QFormLayout(g2)

        self.btn_fov_color = ColorButton("Pick…", [255, 217, 26, 255])
        self.sp_fov_alpha_normal = QDoubleSpinBox(); self.sp_fov_alpha_normal.setRange(0.0, 1.0); self.sp_fov_alpha_normal.setDecimals(3); self.sp_fov_alpha_normal.setSingleStep(0.05)
        self.sp_fov_alpha_dim = QDoubleSpinBox(); self.sp_fov_alpha_dim.setRange(0.0, 1.0); self.sp_fov_alpha_dim.setDecimals(3); self.sp_fov_alpha_dim.setSingleStep(0.05)
        self.chk_fov_colormap = QCheckBox("Color FOV mask by height using colormap")
        self.cmb_fov_colormap = QComboBox()
        for name in ["viridis", "plasma", "inferno", "magma", "cividis", "grey", "gray"]:
            self.cmb_fov_colormap.addItem(name)

        self.btn_invalid_color = ColorButton("Pick…", [255, 217, 26, 255])
        self.sp_invalid_alpha_normal = QDoubleSpinBox(); self.sp_invalid_alpha_normal.setRange(0.0, 1.0); self.sp_invalid_alpha_normal.setDecimals(3); self.sp_invalid_alpha_normal.setSingleStep(0.05)
        self.sp_invalid_alpha_dim = QDoubleSpinBox(); self.sp_invalid_alpha_dim.setRange(0.0, 1.0); self.sp_invalid_alpha_dim.setDecimals(3); self.sp_invalid_alpha_dim.setSingleStep(0.05)

        f2.addRow("FOV color", self.btn_fov_color)
        f2.addRow("FOV alpha (no slice)", self.sp_fov_alpha_normal)
        f2.addRow("FOV alpha (slice enabled)", self.sp_fov_alpha_dim)
        f2.addRow(self.chk_fov_colormap)
        f2.addRow("FOV colormap", self.cmb_fov_colormap)
        f2.addRow("Invalid density color", self.btn_invalid_color)
        f2.addRow("Invalid alpha (no slice)", self.sp_invalid_alpha_normal)
        f2.addRow("Invalid alpha (slice enabled)", self.sp_invalid_alpha_dim)

        lay.addWidget(g1)
        lay.addWidget(g2)
        lay.addStretch(1)
        self.tabs.addTab(tab, "Overlays")

    def _build_tab_slices(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)

        # shared
        row = QHBoxLayout()
        lay.addLayout(row)

        lbl = QLabel("Max segments to draw (per slice):")
        self.sp_max_segs = QSpinBox()
        self.sp_max_segs.setRange(1000, 5_000_000)
        self.sp_max_segs.setSingleStep(10_000)

        row.addWidget(lbl)
        row.addWidget(self.sp_max_segs, 1)

        # θy slice
        gy = QGroupBox("θy slice style")
        fy = QFormLayout(gy)
        self.btn_y_plane = ColorButton("Pick…", [38, 217, 255, 56])
        self.btn_y_border = ColorButton("Pick…", [38, 217, 255, 242])
        self.btn_y_main = ColorButton("Pick…", [255, 242, 51, 255])
        self.btn_y_glow = ColorButton("Pick…", [255, 242, 51, 56])
        self.sp_y_border_w = QDoubleSpinBox(); self.sp_y_border_w.setRange(0.1, 50.0); self.sp_y_border_w.setDecimals(1); self.sp_y_border_w.setSingleStep(0.5)
        self.sp_y_main_w   = QDoubleSpinBox(); self.sp_y_main_w.setRange(0.1, 50.0); self.sp_y_main_w.setDecimals(1); self.sp_y_main_w.setSingleStep(0.5)
        self.sp_y_glow_w   = QDoubleSpinBox(); self.sp_y_glow_w.setRange(0.1, 50.0); self.sp_y_glow_w.setDecimals(1); self.sp_y_glow_w.setSingleStep(0.5)
        fy.addRow("Plane", self.btn_y_plane)
        fy.addRow("Border", self.btn_y_border)
        fy.addRow("Lines main", self.btn_y_main)
        fy.addRow("Lines glow", self.btn_y_glow)
        fy.addRow("Border width", self.sp_y_border_w)
        fy.addRow("Main width", self.sp_y_main_w)
        fy.addRow("Glow width", self.sp_y_glow_w)

        # θx slice
        gx = QGroupBox("θx slice style")
        fx = QFormLayout(gx)
        self.btn_x_plane = ColorButton("Pick…", [242, 64, 242, 46])
        self.btn_x_border = ColorButton("Pick…", [242, 64, 242, 242])
        self.btn_x_main = ColorButton("Pick…", [64, 255, 64, 255])
        self.btn_x_glow = ColorButton("Pick…", [64, 255, 64, 51])
        self.sp_x_border_w = QDoubleSpinBox(); self.sp_x_border_w.setRange(0.1, 50.0); self.sp_x_border_w.setDecimals(1); self.sp_x_border_w.setSingleStep(0.5)
        self.sp_x_main_w   = QDoubleSpinBox(); self.sp_x_main_w.setRange(0.1, 50.0); self.sp_x_main_w.setDecimals(1); self.sp_x_main_w.setSingleStep(0.5)
        self.sp_x_glow_w   = QDoubleSpinBox(); self.sp_x_glow_w.setRange(0.1, 50.0); self.sp_x_glow_w.setDecimals(1); self.sp_x_glow_w.setSingleStep(0.5)
        fx.addRow("Plane", self.btn_x_plane)
        fx.addRow("Border", self.btn_x_border)
        fx.addRow("Lines main", self.btn_x_main)
        fx.addRow("Lines glow", self.btn_x_glow)
        fx.addRow("Border width", self.sp_x_border_w)
        fx.addRow("Main width", self.sp_x_main_w)
        fx.addRow("Glow width", self.sp_x_glow_w)

        lay.addWidget(gy)
        lay.addWidget(gx)
        lay.addStretch(1)
        self.tabs.addTab(tab, "Slices")

    def _build_tab_reference(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)

        g1 = QGroupBox("Base grid")
        f1 = QFormLayout(g1)
        self.btn_grid = ColorButton("Pick…", [120, 120, 120, 90])
        self.sp_grid_spacing = QDoubleSpinBox(); self.sp_grid_spacing.setRange(1.0, 1e6); self.sp_grid_spacing.setDecimals(1); self.sp_grid_spacing.setSingleStep(10.0)
        f1.addRow("Grid color", self.btn_grid)
        f1.addRow("Grid spacing (m)", self.sp_grid_spacing)

        g2 = QGroupBox("Height axis + ticks")
        f2 = QFormLayout(g2)
        self.btn_axis = ColorButton("Pick…", [255, 128, 51, 255])
        self.btn_ticks = ColorButton("Pick…", [255, 128, 51, 242])
        self.sp_tick_step = QDoubleSpinBox(); self.sp_tick_step.setRange(1.0, 1e6); self.sp_tick_step.setDecimals(1); self.sp_tick_step.setSingleStep(10.0)
        f2.addRow("Axis color", self.btn_axis)
        f2.addRow("Tick color", self.btn_ticks)
        f2.addRow("Tick step (m)", self.sp_tick_step)

        lay.addWidget(g1)
        lay.addWidget(g2)
        lay.addStretch(1)
        self.tabs.addTab(tab, "Reference")

    def _build_tab_performance(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        form = QFormLayout()
        lay.addLayout(form)
        lay.addStretch(1)

        self.sp_max_points = QSpinBox()
        self.sp_max_points.setRange(10_000, 5_000_000)
        self.sp_max_points.setSingleStep(10_000)

        self.sp_dedupe = QSpinBox()
        self.sp_dedupe.setRange(0, 12)
        self.sp_dedupe.setSingleStep(1)

        self.sp_eps = QDoubleSpinBox()
        self.sp_eps.setRange(1e-12, 1e-3)
        self.sp_eps.setDecimals(12)
        self.sp_eps.setSingleStep(1e-8)

        form.addRow("Max DEM points (decimation)", self.sp_max_points)
        form.addRow("Dedupe round decimals", self.sp_dedupe)
        form.addRow("Plane intersection eps", self.sp_eps)

        note = QLabel(
            "Note: Changing DEM decimation/dedupe only affects the DEM on next reload,\n"
            "unless your main script keeps raw DEM and rebuilds on apply."
        )
        note.setStyleSheet("color: #dcdcdc;")
        lay.addWidget(note)

        self.tabs.addTab(tab, "Performance")

    # -------------------------
    # populate / collect
    # -------------------------

    def _populate_widgets_from_cfg(self):
        c = self._cfg

        self.btn_bg.set_rgba(c["appearance"]["background"])
        self.cmb_cmap.setCurrentText(str(c["appearance"]["colormap"]))
        self.cmb_shader.setCurrentText(str(c["mesh"]["shader"]))
        self.cmb_gl_opaque.setCurrentText(str(c["mesh"]["gl_opaque"]))
        self.cmb_gl_trans.setCurrentText(str(c["mesh"]["gl_translucent"]))

        self.sp_dist.setValue(float(c["camera"]["distance"]))
        self.sp_elev.setValue(float(c["camera"]["elevation"]))
        self.sp_azim.setValue(float(c["camera"]["azimuth"]))
        self.sp_fov.setValue(float(c["camera"]["fov"]))
        self.chk_persp.setChecked(bool(c["camera"].get("perspective", True)))

        self.sp_mesh_alpha_normal.setValue(float(c["mesh"]["alpha_normal"]))
        self.sp_mesh_alpha_dim.setValue(float(c["mesh"]["alpha_dim"]))
        self.sp_den_alpha_normal.setValue(float(c["overlay"]["density_alpha_normal"]))
        self.sp_den_alpha_dim.setValue(float(c["overlay"]["density_alpha_dim"]))

        self.btn_fov_color.set_rgba(c["overlay"]["fov_color"])
        self.sp_fov_alpha_normal.setValue(float(c["overlay"]["fov_alpha_normal"]))
        self.sp_fov_alpha_dim.setValue(float(c["overlay"]["fov_alpha_dim"]))
        self.chk_fov_colormap.setChecked(bool(c["overlay"].get("fov_use_colormap", False)))
        self.cmb_fov_colormap.setCurrentText(str(c["overlay"].get("fov_colormap", c["appearance"]["colormap"])))
        self.btn_invalid_color.set_rgba(c["overlay"]["invalid_color"])
        self.sp_invalid_alpha_normal.setValue(float(c["overlay"]["invalid_alpha_normal"]))
        self.sp_invalid_alpha_dim.setValue(float(c["overlay"]["invalid_alpha_dim"]))

        self.sp_max_segs.setValue(int(c["slices"]["max_segs"]))

        self.btn_y_plane.set_rgba(c["slices"]["y"]["plane_color"])
        self.btn_y_border.set_rgba(c["slices"]["y"]["border_color"])
        self.btn_y_main.set_rgba(c["slices"]["y"]["line_main"])
        self.btn_y_glow.set_rgba(c["slices"]["y"]["line_glow"])
        self.sp_y_border_w.setValue(float(c["slices"]["y"]["border_width"]))
        self.sp_y_main_w.setValue(float(c["slices"]["y"]["main_width"]))
        self.sp_y_glow_w.setValue(float(c["slices"]["y"]["glow_width"]))

        self.btn_x_plane.set_rgba(c["slices"]["x"]["plane_color"])
        self.btn_x_border.set_rgba(c["slices"]["x"]["border_color"])
        self.btn_x_main.set_rgba(c["slices"]["x"]["line_main"])
        self.btn_x_glow.set_rgba(c["slices"]["x"]["line_glow"])
        self.sp_x_border_w.setValue(float(c["slices"]["x"]["border_width"]))
        self.sp_x_main_w.setValue(float(c["slices"]["x"]["main_width"]))
        self.sp_x_glow_w.setValue(float(c["slices"]["x"]["glow_width"]))

        self.btn_grid.set_rgba(c["grid"]["color"])
        self.sp_grid_spacing.setValue(float(c["grid"]["spacing"]))

        self.btn_axis.set_rgba(c["height_axis"]["axis_color"])
        self.btn_ticks.set_rgba(c["height_axis"]["ticks_color"])
        self.sp_tick_step.setValue(float(c["height_axis"]["tick_step"]))

        self.sp_max_points.setValue(int(c["performance"]["max_points"]))
        self.sp_dedupe.setValue(int(c["performance"]["dedupe_round_decimals"]))
        self.sp_eps.setValue(float(c["performance"]["intersection_eps"]))

    def current_cfg(self) -> Dict[str, Any]:
        c = copy.deepcopy(self._cfg)

        c["appearance"]["background"] = self.btn_bg.rgba()
        c["appearance"]["colormap"] = self.cmb_cmap.currentText().strip()

        c["mesh"]["shader"] = self.cmb_shader.currentText().strip()
        c["mesh"]["gl_opaque"] = self.cmb_gl_opaque.currentText().strip()
        c["mesh"]["gl_translucent"] = self.cmb_gl_trans.currentText().strip()

        c["camera"]["distance"] = float(self.sp_dist.value())
        c["camera"]["elevation"] = float(self.sp_elev.value())
        c["camera"]["azimuth"] = float(self.sp_azim.value())
        c["camera"]["fov"] = float(self.sp_fov.value())
        c["camera"]["perspective"] = bool(self.chk_persp.isChecked())

        c["mesh"]["alpha_normal"] = float(self.sp_mesh_alpha_normal.value())
        c["mesh"]["alpha_dim"] = float(self.sp_mesh_alpha_dim.value())
        c["overlay"]["density_alpha_normal"] = float(self.sp_den_alpha_normal.value())
        c["overlay"]["density_alpha_dim"] = float(self.sp_den_alpha_dim.value())

        c["overlay"]["fov_color"] = self.btn_fov_color.rgba()
        c["overlay"]["fov_alpha_normal"] = float(self.sp_fov_alpha_normal.value())
        c["overlay"]["fov_alpha_dim"] = float(self.sp_fov_alpha_dim.value())
        c["overlay"]["fov_use_colormap"] = bool(self.chk_fov_colormap.isChecked())
        c["overlay"]["fov_colormap"] = self.cmb_fov_colormap.currentText().strip()
        c["overlay"]["invalid_color"] = self.btn_invalid_color.rgba()
        c["overlay"]["invalid_alpha_normal"] = float(self.sp_invalid_alpha_normal.value())
        c["overlay"]["invalid_alpha_dim"] = float(self.sp_invalid_alpha_dim.value())

        c["slices"]["max_segs"] = int(self.sp_max_segs.value())

        c["slices"]["y"]["plane_color"] = self.btn_y_plane.rgba()
        c["slices"]["y"]["border_color"] = self.btn_y_border.rgba()
        c["slices"]["y"]["line_main"] = self.btn_y_main.rgba()
        c["slices"]["y"]["line_glow"] = self.btn_y_glow.rgba()
        c["slices"]["y"]["border_width"] = float(self.sp_y_border_w.value())
        c["slices"]["y"]["main_width"] = float(self.sp_y_main_w.value())
        c["slices"]["y"]["glow_width"] = float(self.sp_y_glow_w.value())

        c["slices"]["x"]["plane_color"] = self.btn_x_plane.rgba()
        c["slices"]["x"]["border_color"] = self.btn_x_border.rgba()
        c["slices"]["x"]["line_main"] = self.btn_x_main.rgba()
        c["slices"]["x"]["line_glow"] = self.btn_x_glow.rgba()
        c["slices"]["x"]["border_width"] = float(self.sp_x_border_w.value())
        c["slices"]["x"]["main_width"] = float(self.sp_x_main_w.value())
        c["slices"]["x"]["glow_width"] = float(self.sp_x_glow_w.value())

        c["grid"]["color"] = self.btn_grid.rgba()
        c["grid"]["spacing"] = float(self.sp_grid_spacing.value())

        c["height_axis"]["axis_color"] = self.btn_axis.rgba()
        c["height_axis"]["ticks_color"] = self.btn_ticks.rgba()
        c["height_axis"]["tick_step"] = float(self.sp_tick_step.value())

        c["performance"]["max_points"] = int(self.sp_max_points.value())
        c["performance"]["dedupe_round_decimals"] = int(self.sp_dedupe.value())
        c["performance"]["intersection_eps"] = float(self.sp_eps.value())

        # ensure shape
        deep_update(c, {})  # no-op, but ensures dict
        return c

    # -------------------------
    # actions
    # -------------------------

    def _apply_clicked(self):
        self._cfg = self.current_cfg()
        self.settingsApplied.emit(copy.deepcopy(self._cfg))

    def _ok_clicked(self):
        self._apply_clicked()
        self.accept()

    def _reset_clicked(self):
        self._cfg = copy.deepcopy(self._base_defaults)
        self._populate_widgets_from_cfg()

    def _load_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load settings", "", "JSON (*.json);;All Files (*)")
        if not path:
            return
        try:
            cfg = load_settings(path, defaults=self._base_defaults)
            self._cfg = cfg
            self._populate_widgets_from_cfg()
        except Exception as e:
            QMessageBox.critical(self, "Load failed", str(e))

    def _save_clicked(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save settings", "", "JSON (*.json);;All Files (*)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            cfg = self.current_cfg()
            save_settings(path, cfg)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
