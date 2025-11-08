"""Custom widgets used by the Ordenador GUI."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget


class ClickIndicator(QWidget):
    """Transient circular widget that highlights AI click positions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.NoFocus)

        diameter = 30
        self.setFixedSize(diameter, diameter)
        radius = diameter // 2
        self.setStyleSheet(
            f"background-color: rgba(255, 0, 0, 0.7); border-radius: {radius}px;"
        )

        QTimer.singleShot(300, self.close)
