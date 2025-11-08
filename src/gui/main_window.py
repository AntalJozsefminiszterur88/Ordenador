"""Application main window built with PySide6."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Simple main window with a tray icon toggle."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ordenador")

        self._setup_ui()
        self._setup_tray_icon()

    def _setup_ui(self) -> None:
        """Create the central widget layout."""

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Mit szeretnél tenni?")
        layout.addWidget(self.input_field)

        self.start_button = QPushButton("Indítás", self)
        self.start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _setup_tray_icon(self) -> None:
        """Configure the system tray icon used to restore the window."""

        icon = self._default_icon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Ordenador fut a háttérben")
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.hide()

    def _on_start_clicked(self) -> None:
        """Hide the main window and show the tray icon."""

        if not self.tray_icon.icon().isNull():
            self.tray_icon.show()
        else:
            self.tray_icon.setIcon(self._default_icon())
            self.tray_icon.show()
        self.hide()

    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Restore the main window when the tray icon is clicked."""

        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self.tray_icon.hide()

    @staticmethod
    def _default_icon() -> QIcon:
        """Return a default application icon from the current style."""

        app = QApplication.instance()
        if app is not None:
            return app.style().standardIcon(QStyle.SP_ComputerIcon)
        return QIcon()
