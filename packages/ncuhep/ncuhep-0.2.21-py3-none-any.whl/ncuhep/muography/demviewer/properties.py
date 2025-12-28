#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys
import platform
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

from PyQt6.QtCore import QT_VERSION_STR, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit
)
from PyQt6.QtGui import QFont, QGuiApplication, QSurfaceFormat

# Prefer PyOpenGL (pyqtgraph.opengl setups usually have it)
try:
    from OpenGL.GL import (
        glGetString,
        glGetIntegerv,
        GL_VENDOR, GL_RENDERER, GL_VERSION, GL_SHADING_LANGUAGE_VERSION,
        GL_NUM_EXTENSIONS
    )
    _HAVE_PYOPENGL = True
except Exception:
    glGetString = None
    glGetIntegerv = None
    _HAVE_PYOPENGL = False


# ----------------------------
# Cache (so dialog can show something even if live query fails once)
# ----------------------------
_GL_CACHE: Dict[str, Any] = {}


def _safe_str(x) -> str:
    if x is None:
        return ""
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="replace")
    return str(x)


def _classify_renderer(vendor: str, renderer: str, version: str) -> Tuple[str, str]:
    v = (vendor or "").lower()
    r = (renderer or "").lower()
    ver = (version or "").lower()
    s = f"{v} {r} {ver}"

    # CPU/software renderers (strong signals)
    software_markers = [
        "llvmpipe", "softpipe", "lavapipe", "swiftshader",
        "software rasterizer", "gdi generic", "microsoft basic render driver",
        "angle (swiftshader)",
    ]
    for m in software_markers:
        if m in s:
            return "CPU (software)", f"Detected software renderer marker: '{m}'."

    # Discrete GPU signals
    discrete_markers = [
        "nvidia", "geforce", "quadro", "rtx", "gtx",
        "radeon rx", "radeon pro",
        "intel arc", "arc a"
    ]
    for m in discrete_markers:
        if m in s:
            return "Discrete GPU", f"Detected discrete GPU marker: '{m}'."

    # Integrated GPU signals
    integrated_markers = [
        "intel", "uhd", "iris", "hd graphics",
        "apple", "apple m",
        "apu", "vega", "radeon graphics"
    ]
    for m in integrated_markers:
        if m in s:
            return "Integrated GPU", f"Detected integrated GPU marker: '{m}'."

    # Vendor-only fallback
    if "nvidia" in v:
        return "Discrete GPU", "Vendor is NVIDIA."
    if "intel" in v:
        return "Integrated GPU", "Vendor is Intel."
    if "amd" in v or "ati" in v:
        return "GPU (AMD)", "Vendor is AMD/ATI (could be integrated or discrete)."

    return "Unknown", "Could not confidently classify from vendor/renderer/version strings."


def _fmt_surface_profile(fmt: QSurfaceFormat) -> str:
    prof = fmt.profile()
    if prof == QSurfaceFormat.OpenGLContextProfile.CoreProfile:
        return "Core"
    if prof == QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile:
        return "Compatibility"
    if prof == QSurfaceFormat.OpenGLContextProfile.NoProfile:
        return "NoProfile"
    return str(prof)


def _try_read_gl_strings(gl_widget) -> Dict[str, str]:
    """
    Attempt to read GL strings from an existing QOpenGLWidget/GLViewWidget.
    Must be called after the widget is realized (shown/painted).
    """
    info = {"vendor": "", "renderer": "", "version": "", "glsl": "", "extensions_count": ""}

    if gl_widget is None:
        return info

    # Ensure context current
    try:
        if hasattr(gl_widget, "makeCurrent"):
            gl_widget.makeCurrent()
    except Exception:
        return info

    try:
        if _HAVE_PYOPENGL:
            vendor = _safe_str(glGetString(GL_VENDOR))
            renderer = _safe_str(glGetString(GL_RENDERER))
            version = _safe_str(glGetString(GL_VERSION))
            glsl = _safe_str(glGetString(GL_SHADING_LANGUAGE_VERSION))
            info.update(vendor=vendor, renderer=renderer, version=version, glsl=glsl)

            # Extensions count best effort
            try:
                n_ext = glGetIntegerv(GL_NUM_EXTENSIONS)
                if hasattr(n_ext, "__len__"):
                    n_ext = int(n_ext[0])
                info["extensions_count"] = str(int(n_ext))
            except Exception:
                pass

        # If you ever want a Qt-only fallback, we can add it,
        # but PyOpenGL is the most reliable here.
    finally:
        try:
            if hasattr(gl_widget, "doneCurrent"):
                gl_widget.doneCurrent()
        except Exception:
            pass

    return info


def collect_properties(gl_widget=None) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    # Runtime / env
    out["python"] = sys.version.replace("\n", " ")
    out["platform"] = platform.platform()
    out["machine"] = platform.machine()
    out["processor"] = platform.processor()
    out["qt_version"] = QT_VERSION_STR

    try:
        from PyQt6.QtCore import PYQT_VERSION_STR
        out["pyqt_version"] = PYQT_VERSION_STR
    except Exception:
        out["pyqt_version"] = "Unknown"

    out["qt_platform"] = ""
    try:
        out["qt_platform"] = QGuiApplication.platformName()
    except Exception:
        pass

    out["env_QT_OPENGL"] = os.environ.get("QT_OPENGL", "")
    out["env_QSG_RHI_BACKEND"] = os.environ.get("QSG_RHI_BACKEND", "")
    out["env_QT_QUICK_BACKEND"] = os.environ.get("QT_QUICK_BACKEND", "")

    try:
        import pyqtgraph as pg
        out["pyqtgraph_version"] = getattr(pg, "__version__", "Unknown")
    except Exception:
        out["pyqtgraph_version"] = "Not installed"

    # OpenGL strings
    gls = _try_read_gl_strings(gl_widget)
    out["gl_vendor"] = gls.get("vendor", "")
    out["gl_renderer"] = gls.get("renderer", "")
    out["gl_version"] = gls.get("version", "")
    out["gl_glsl"] = gls.get("glsl", "")
    out["gl_extensions_count"] = gls.get("extensions_count", "")

    backend, reason = _classify_renderer(out["gl_vendor"], out["gl_renderer"], out["gl_version"])
    out["backend"] = backend
    out["backend_reason"] = reason

    # Surface format: prefer widget.format() if available
    fmt = None
    try:
        if gl_widget is not None and hasattr(gl_widget, "format"):
            fmt = gl_widget.format()
    except Exception:
        fmt = None
    if fmt is None:
        fmt = QSurfaceFormat.defaultFormat()

    out["surface_format"] = {
        "version": f"{fmt.majorVersion()}.{fmt.minorVersion()}",
        "profile": _fmt_surface_profile(fmt),
        "depth": fmt.depthBufferSize(),
        "stencil": fmt.stencilBufferSize(),
        "samples": fmt.samples(),
        "swap_interval": fmt.swapInterval(),
    }

    return out


def format_properties_text(p: Dict[str, Any]) -> str:
    sf = p.get("surface_format", {}) or {}

    lines = []
    lines.append(f"Graphics backend : {p.get('backend','')}")
    lines.append(f"Why              : {p.get('backend_reason','')}")
    lines.append("")
    lines.append("OpenGL")
    lines.append(f"  Vendor         : {p.get('gl_vendor','')}")
    lines.append(f"  Renderer       : {p.get('gl_renderer','')}")
    lines.append(f"  Version        : {p.get('gl_version','')}")
    lines.append(f"  GLSL           : {p.get('gl_glsl','')}")
    if p.get("gl_extensions_count"):
        lines.append(f"  Extensions     : {p.get('gl_extensions_count')}")
    lines.append("")
    lines.append("SurfaceFormat (Qt)")
    lines.append(f"  Requested GL   : {sf.get('version','')}")
    lines.append(f"  Profile        : {sf.get('profile','')}")
    lines.append(f"  Depth/Stencil  : {sf.get('depth','')} / {sf.get('stencil','')}")
    lines.append(f"  MSAA samples   : {sf.get('samples','')}")
    lines.append(f"  Swap interval  : {sf.get('swap_interval','')}")
    lines.append("")
    lines.append("Runtime")
    lines.append(f"  Python         : {p.get('python','')}")
    lines.append(f"  Qt             : {p.get('qt_version','')}")
    lines.append(f"  PyQt           : {p.get('pyqt_version','')}")
    lines.append(f"  pyqtgraph      : {p.get('pyqtgraph_version','')}")
    lines.append(f"  Platform       : {p.get('platform','')}")
    lines.append(f"  Machine        : {p.get('machine','')}")
    if p.get("processor"):
        lines.append(f"  Processor      : {p.get('processor','')}")
    if p.get("qt_platform"):
        lines.append(f"  Qt platform    : {p.get('qt_platform','')}")

    # env hints
    if p.get("env_QT_OPENGL") or p.get("env_QSG_RHI_BACKEND") or p.get("env_QT_QUICK_BACKEND"):
        lines.append("")
        lines.append("Env")
        if p.get("env_QT_OPENGL"):
            lines.append(f"  QT_OPENGL      : {p.get('env_QT_OPENGL')}")
        if p.get("env_QSG_RHI_BACKEND"):
            lines.append(f"  QSG_RHI_BACKEND: {p.get('env_QSG_RHI_BACKEND')}")
        if p.get("env_QT_QUICK_BACKEND"):
            lines.append(f"  QT_QUICK_BACKEND: {p.get('env_QT_QUICK_BACKEND')}")

    return "\n".join(lines)


def warmup_gl_widget(gl_widget, max_tries: int = 20, interval_ms: int = 30):
    """
    Call after w.show() to ensure GL context is realized and cache GL strings.
    Safe to call even if it never becomes ready.
    """
    if gl_widget is None:
        return

    state = {"tries": 0}

    def _tick():
        state["tries"] += 1
        p = collect_properties(gl_widget)
        if p.get("gl_renderer") or p.get("gl_vendor"):
            _GL_CACHE.clear()
            _GL_CACHE.update(p)
            return
        if state["tries"] >= max_tries:
            # store last attempt (might still be empty)
            _GL_CACHE.clear()
            _GL_CACHE.update(p)
            return
        QTimer.singleShot(interval_ms, _tick)

    QTimer.singleShot(0, _tick)


class PropertiesDialog(QDialog):
    def __init__(self, gl_widget=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Properties")
        self.resize(860, 520)

        self._gl_widget = gl_widget
        self._retry_left = 20

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        head = QLabel("OpenGL / System Properties")
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        head.setFont(f)
        lay.addWidget(head)

        self.txt = QPlainTextEdit()
        self.txt.setReadOnly(True)
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(10)
        self.txt.setFont(mono)
        lay.addWidget(self.txt, 1)

        row = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_copy = QPushButton("Copy")
        self.btn_close = QPushButton("Close")
        row.addWidget(self.btn_refresh)
        row.addStretch(1)
        row.addWidget(self.btn_copy)
        row.addWidget(self.btn_close)
        lay.addLayout(row)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_close.clicked.connect(self.close)

        # Do an initial deferred refresh (important!)
        QTimer.singleShot(0, self.refresh)

    def refresh(self):
        # Try live
        p = collect_properties(self._gl_widget)

        # If empty, use cache if it exists (often warmed up by warmup_gl_widget)
        if not (p.get("gl_renderer") or p.get("gl_vendor")) and _GL_CACHE:
            p = dict(_GL_CACHE)

        # Still empty? retry a few times automatically (context may be created after first paint)
        if not (p.get("gl_renderer") or p.get("gl_vendor")) and self._retry_left > 0:
            self._retry_left -= 1
            self.txt.setPlainText(
                format_properties_text(p)
                + "\n\n[OpenGL] Waiting for context... (try painting the 3D view once, or click Refresh)"
            )
            QTimer.singleShot(50, self.refresh)
            return

        self.txt.setPlainText(format_properties_text(p))

    def copy_to_clipboard(self):
        cb = QGuiApplication.clipboard()
        cb.setText(self.txt.toPlainText())
