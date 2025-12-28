#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
import tempfile
import wave
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtGui import QPainter, QFont, QLinearGradient, QColor, QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QPauseAnimation
from .resources import resolve_asset_path

# Sound is optional (some systems / minimal Qt builds may not ship multimedia plugins)
try:
    from PyQt6.QtMultimedia import QSoundEffect
    _HAVE_QT_SOUND = True
except Exception:
    QSoundEffect = None
    _HAVE_QT_SOUND = False


def _ensure_default_startup_wav(path: str, seconds: float = 0.22, freq_hz: float = 880.0, sr: int = 44100):
    """
    Create a tiny sine-beep WAV so the project is self-contained (no external asset needed).
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        return

    n = int(max(1, seconds * sr))
    amp = 0.35  # safe volume
    fade_n = max(1, int(0.02 * sr))

    with wave.open(str(target), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sr)

        frames = bytearray()
        for i in range(n):
            # fade in/out to avoid clicks
            g = 1.0
            if i < fade_n:
                g = i / float(fade_n)
            elif i > (n - fade_n):
                g = max(0.0, (n - i) / float(fade_n))

            t = i / float(sr)
            x = amp * g * math.sin(2.0 * math.pi * freq_hz * t)
            s = int(max(-1.0, min(1.0, x)) * 32767.0)
            frames += int(s).to_bytes(2, byteorder="little", signed=True)

        wf.writeframes(frames)


class StartupSplash(QWidget):
    """
    Frameless splash with fade-in -> hold -> fade-out animation, and an optional beep.

    Usage:
        splash = StartupSplash()
        splash.finished.connect(...)
        splash.show()
        splash.start()
    """
    finished = pyqtSignal()

    def __init__(
        self,
        title_top: str = "National Central University",
        title_main: str = "Muography",
        subtitle: str = "",
        duration_ms: int = 2200,
        sound: bool = True,
        sound_path: str | None = "startup_sound.wav",
        app_icon: Optional[QIcon] = None,
        parent=None,
    ):
        super().__init__(parent)

        self._duration_ms = int(max(600, duration_ms))
        self._sound_enabled = bool(sound)
        self._sound_path = sound_path
        if app_icon is not None:
            try:
                self.setWindowIcon(app_icon)
            except Exception:
                pass
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # --- UI ---
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_top = QLabel(title_top)
        self.lbl_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_top.setStyleSheet("color: rgba(230,230,230,220);")
        f1 = QFont()
        f1.setPointSize(18)
        f1.setBold(True)
        self.lbl_top.setFont(f1)

        self.lbl_main = QLabel(title_main)
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main.setStyleSheet("color: rgba(255,255,255,245);")
        f2 = QFont()
        f2.setPointSize(42)
        f2.setBold(True)
        self.lbl_main.setFont(f2)

        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setStyleSheet("color: rgba(200,200,200,200);")
        f3 = QFont()
        f3.setPointSize(12)
        self.lbl_sub.setFont(f3)
        self.lbl_sub.setVisible(bool(subtitle.strip()))

        lay.addWidget(self.lbl_top)
        lay.addWidget(self.lbl_main)
        lay.addWidget(self.lbl_sub)

        # --- Opacity effect for smooth fade ---
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        # --- Animations ---
        self._anim = QSequentialAnimationGroup(self)

        fade_in = QPropertyAnimation(self._opacity, b"opacity")
        fade_in.setDuration(int(self._duration_ms * 0.28))
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        hold = QPauseAnimation(int(self._duration_ms * 0.44))

        fade_out = QPropertyAnimation(self._opacity, b"opacity")
        fade_out.setDuration(int(self._duration_ms * 0.28))
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

        self._anim.addAnimation(fade_in)
        self._anim.addAnimation(hold)
        self._anim.addAnimation(fade_out)
        self._anim.finished.connect(self._on_anim_finished)

        # --- Optional sound effect ---
        self._sound: Optional["QSoundEffect"] = None
        self._wav_path: Optional[str] = None

        self.resize(640, 260)

    def paintEvent(self, ev):
        # Rounded-rect gradient panel
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        p.end()

    def mousePressEvent(self, ev):
        # click to skip
        try:
            self._anim.stop()
        except Exception:
            pass
        self._opacity.setOpacity(0.0)
        self._on_anim_finished()

    def showEvent(self, ev):
        super().showEvent(ev)
        # Start on next tick so the widget is actually on screen first
        QTimer.singleShot(0, self.start)

    def _play_sound(self):
        if not self._sound_enabled:
            return

        # resolve path relative to startup.py
        path_obj = resolve_asset_path(getattr(self, "_sound_path", None))
        path = str(path_obj) if path_obj else None

        # Prefer QtMultimedia QSoundEffect (WAV works well)
        if path and _HAVE_QT_SOUND:
            try:
                self._sound = QSoundEffect(self)
                self._sound.setSource(QUrl.fromLocalFile(path))
                self._sound.setVolume(0.35)
                self._sound.play()
                return
            except Exception:
                pass

        # Windows fallback for wav if QtMultimedia isn't available
        if path and path.lower().endswith(".wav"):
            try:
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception:
                pass

        # last resort
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.beep()
        except Exception:
            pass

    def start(self):
        # center on screen (active screen)
        try:
            screen = self.screen()
            if screen is not None:
                geo = screen.availableGeometry()
                self.move(
                    int(geo.center().x() - self.width() * 0.5),
                    int(geo.center().y() - self.height() * 0.5),
                )
        except Exception:
            pass

        self._play_sound()

        # ensure fully transparent at start
        self._opacity.setOpacity(0.0)

        try:
            self._anim.stop()
        except Exception:
            pass
        self._anim.start()

    def _on_anim_finished(self):
        # emit once
        if getattr(self, "_emitted", False):
            return
        self._emitted = True
        self.finished.emit()
