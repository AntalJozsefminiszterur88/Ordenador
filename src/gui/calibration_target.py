from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget


class CalibrationTarget(QWidget):
    """Egy egyszerű, mindig felül lévő ablak, ami egy célpontot jelenít meg."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(50, 50)
        self.setStyleSheet("background-color: red; border-radius: 25px;")
