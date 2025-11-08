from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class CalibrationGrid(QWidget):
    """Egy teljes képernyős, áttetsző ablak, ami feliratozott célpontokat rajzol."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.points = self._generate_points()

    def _generate_points(self) -> dict[str, tuple[int, int]]:
        """Generálja a célpontok valós képernyő-koordinátáit."""

        margin = 100
        screen = self.screen()
        if screen is None:
            return {}
        size = screen.size()
        w, h = size.width(), size.height()
        return {
            "A": (margin, margin),
            "B": (w - margin, margin),
            "C": (w - margin, h - margin),
            "D": (margin, h - margin),
            "E": (w // 2, h // 2),
        }

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt metódusnév
        """Felrajzolja a célpontokat és a feliratokat."""

        del event  # event objektum nem használt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("red"), 2, Qt.SolidLine)
        painter.setPen(pen)

        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)

        for label, (x, y) in self.points.items():
            painter.drawLine(x - 15, y, x + 15, y)
            painter.drawLine(x, y - 15, x, y + 15)
            painter.drawText(x + 20, y + 20, label)
