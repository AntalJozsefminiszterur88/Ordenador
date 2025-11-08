"""Full-screen transparent widget that captures the next mouse click."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QCloseEvent, QMouseEvent
from PySide6.QtWidgets import QWidget


class ClickInterceptor(QWidget):
    """Transparent overlay used to capture a single global mouse click."""

    clicked = Signal(int, int)
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMouseTracking(True)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: D401
        """Capture the first mouse press, emit its global coordinates and close."""

        global_pos: QPointF = event.globalPosition()
        point = global_pos.toPoint()
        self.clicked.emit(point.x(), point.y())
        event.accept()
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        self.closed.emit()
        super().closeEvent(event)
