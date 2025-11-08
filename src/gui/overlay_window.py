"""Floating overlay window for displaying ongoing operations."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QListWidget, QProgressBar, QVBoxLayout, QWidget


class OverlayWindow(QWidget):
    """A small, always-on-top window showing task progress and logs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_offset: QPoint | None = None

        self._configure_window_flags()
        self._setup_ui()
        self.hide()

    def _configure_window_flags(self) -> None:
        """Apply the overlay window behaviour flags."""

        flags = self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        self.setWindowFlags(flags)

    def _setup_ui(self) -> None:
        """Create the progress bar, status label, and log list."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("overlayStatusLabel")
        layout.addWidget(self.status_label)

        self.log_list = QListWidget(self)
        layout.addWidget(self.log_list)

        self.setLayout(layout)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API naming convention
        """Store the offset when the user starts dragging the window."""

        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API naming convention
        """Move the window according to the mouse position while dragging."""

        if event.buttons() & Qt.LeftButton and self._drag_offset is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API naming convention
        """Clear the drag offset when the drag ends."""

        if event.button() == Qt.LeftButton:
            self._drag_offset = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
