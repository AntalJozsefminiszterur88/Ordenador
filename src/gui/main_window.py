"""Application main window built with PySide6."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from src.assistant import DesktopAssistant
from src.gui.click_interceptor import ClickInterceptor
from src.gui.overlay_window import OverlayWindow
from src.memory_handler import MemoryHandler


class MainWindow(QMainWindow):
    """Simple main window with a tray icon toggle."""

    start_task_requested = Signal(str)
    start_calibration_requested = Signal()
    stop_task_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ordenador")

        self.assistant: DesktopAssistant | None = None
        self.assistant_thread: QThread | None = None
        self.click_interceptor: ClickInterceptor | None = None
        self.memory_handler = MemoryHandler()

        self._setup_ui()
        self._setup_tray_icon()
        self._setup_overlay()

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

        self.training_button = QPushButton("Elem tanítása", self)
        self.training_button.clicked.connect(self._on_train_element_clicked)
        layout.addWidget(self.training_button)

        self.calibration_button = QPushButton("Kalibráció", self)
        self.calibration_button.clicked.connect(self._on_start_calibration)
        layout.addWidget(self.calibration_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _setup_tray_icon(self) -> None:
        """Configure the system tray icon used to restore the window."""

        icon = self._default_icon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Ordenador fut a háttérben")
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.hide()

    def _setup_overlay(self) -> None:
        """Create the floating overlay window used during task execution."""

        self.overlay = OverlayWindow(self)
        self.overlay.stop_button.clicked.connect(self._on_stop_clicked)

    def _on_start_clicked(self) -> None:
        """Hide the main window, show overlay and run the assistant task."""

        command = self.input_field.text().strip()
        if not command:
            return

        if not self.tray_icon.icon().isNull():
            self.tray_icon.show()
        else:
            self.tray_icon.setIcon(self._default_icon())
            self.tray_icon.show()

        self._prepare_overlay()
        self.hide()

        self._start_assistant(command)

    def _on_start_calibration(self) -> None:
        """Launch the automated calibration flow."""

        if self.assistant_thread is not None and self.assistant_thread.isRunning():
            return

        if not self.tray_icon.icon().isNull():
            self.tray_icon.show()
        else:
            self.tray_icon.setIcon(self._default_icon())
            self.tray_icon.show()

        self._prepare_overlay()
        self.hide()

        self._start_calibration()

    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Restore the main window when the tray icon is clicked."""

        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self.tray_icon.hide()

    def _prepare_overlay(self) -> None:
        """Reset and display the overlay window at the right edge of the screen."""

        self.overlay.progress_bar.setValue(0)
        self.overlay.status_label.clear()
        self.overlay.log_list.clear()

        self.overlay.show()
        self.overlay.raise_()
        self._position_overlay()

    def _position_overlay(self) -> None:
        """Position the overlay at the vertical centre of the right screen edge."""

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        geometry = screen.availableGeometry()
        self.overlay.adjustSize()
        window_size = self.overlay.size()
        x = geometry.right() - window_size.width() - 24
        y = geometry.top() + (geometry.height() - window_size.height()) // 2
        self.overlay.move(max(geometry.left(), x), max(geometry.top(), y))

    def _start_assistant(self, command: str) -> None:
        """Create the assistant worker and start it on a background thread."""

        if not self._ensure_assistant_worker():
            return

        self.start_task_requested.emit(command)

    def _start_calibration(self) -> None:
        """Ensure the assistant worker exists and trigger calibration."""

        if not self._ensure_assistant_worker():
            return

        self.start_calibration_requested.emit()

    def _ensure_assistant_worker(self) -> bool:
        """Initialise the assistant worker thread if it is not already running."""

        if self.assistant_thread is not None and self.assistant_thread.isRunning():
            return False

        self.assistant_thread = QThread(self)
        self.assistant = DesktopAssistant()
        self.assistant.moveToThread(self.assistant_thread)

        self.start_task_requested.connect(self.assistant.start_task, Qt.QueuedConnection)
        self.start_calibration_requested.connect(
            self.assistant.start_calibration_task, Qt.QueuedConnection
        )
        self.stop_task_requested.connect(self.assistant.request_stop, Qt.QueuedConnection)
        self.assistant.status_updated.connect(self.overlay.status_label.setText)
        self.assistant.progress_updated.connect(self.overlay.progress_bar.setValue)
        self.assistant.log_message.connect(self.overlay.log_list.addItem)
        self.assistant.task_finished.connect(self._on_task_finished)
        self.assistant.task_finished.connect(self.assistant_thread.quit)
        self.assistant_thread.finished.connect(self._cleanup_assistant)

        self.assistant_thread.start()
        return True

    def _on_task_finished(self) -> None:
        """Handle assistant completion by restoring the main window."""

        self.overlay.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.tray_icon.hide()

    def _on_train_element_clicked(self) -> None:
        """Start the interactive element training flow."""

        if self.click_interceptor is not None:
            return

        self.hide()
        self.click_interceptor = ClickInterceptor(self)
        self.click_interceptor.clicked.connect(self._on_element_click_captured)
        self.click_interceptor.closed.connect(self._on_click_interceptor_closed)
        self.click_interceptor.showFullScreen()
        self.click_interceptor.activateWindow()

    def _on_element_click_captured(self, x: int, y: int) -> None:
        """Ask for the element name and persist the captured coordinates."""

        name, ok = QInputDialog.getText(self, "Elem tanítása", "Add meg az elem nevét:")
        if ok:
            cleaned_name = name.strip()
            if cleaned_name:
                self.memory_handler.save_element_location(cleaned_name, {"x": x, "y": y})
        self._finalize_training()

    def _on_click_interceptor_closed(self) -> None:
        """Ensure the main window is restored when the interceptor closes."""

        self._finalize_training()

    def _finalize_training(self) -> None:
        """Clean up the click interceptor and restore the window."""

        if self.click_interceptor is not None:
            try:
                self.click_interceptor.clicked.disconnect(self._on_element_click_captured)
            except (TypeError, RuntimeError):
                pass
            try:
                self.click_interceptor.closed.disconnect(self._on_click_interceptor_closed)
            except (TypeError, RuntimeError):
                pass
            if self.click_interceptor.isVisible():
                self.click_interceptor.hide()
            self.click_interceptor.deleteLater()
            self.click_interceptor = None

        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.tray_icon.hide()

    def _cleanup_assistant(self) -> None:
        """Disconnect signals and delete the worker/thread objects."""

        if self.assistant is not None:
            try:
                self.start_task_requested.disconnect(self.assistant.start_task)
            except (TypeError, RuntimeError):
                pass
            try:
                self.start_calibration_requested.disconnect(
                    self.assistant.start_calibration_task
                )
            except (TypeError, RuntimeError):
                pass
            try:
                self.stop_task_requested.disconnect(self.assistant.request_stop)
            except (TypeError, RuntimeError):
                pass
            self.assistant.deleteLater()
            self.assistant = None

        if self.assistant_thread is not None:
            self.assistant_thread.deleteLater()
            self.assistant_thread = None

    @staticmethod
    def _default_icon() -> QIcon:
        """Return a default application icon from the current style."""

        app = QApplication.instance()
        if app is not None:
            return app.style().standardIcon(QStyle.SP_ComputerIcon)
        return QIcon()

    def _on_stop_clicked(self) -> None:
        """Allow the user to request task interruption from the overlay."""

        self.stop_task_requested.emit()
