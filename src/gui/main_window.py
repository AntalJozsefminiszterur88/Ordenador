# src/gui/main_window.py

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QInputDialog, QLineEdit, QMainWindow,
    QPushButton, QSystemTrayIcon, QVBoxLayout, QWidget
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle

from src.assistant import DesktopAssistant
from src.gui.click_interceptor import ClickInterceptor
from src.gui.overlay_window import OverlayWindow
from src.memory_handler import MemoryHandler

class MainWindow(QMainWindow):
    start_task_requested = Signal(str)
    start_calibration_requested = Signal()
    stop_task_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ordenador")

        self.assistant = None
        self.assistant_thread = None
        self.click_interceptor = None
        self.memory_handler = MemoryHandler()

        self._setup_ui()
        self.overlay = OverlayWindow(self)
        self.tray_icon = QSystemTrayIcon(self)

        # A kapcsolatokat itt hozzuk létre egyszer
        self.start_button.clicked.connect(self._on_start_clicked)
        self.training_button.clicked.connect(self._on_train_element_clicked)
        self.calibration_button.clicked.connect(self._on_start_calibration)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.overlay.stop_button.clicked.connect(self.stop_task_requested.emit)

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.input_field = QLineEdit(placeholderText="Mit szeretnél tenni?")
        self.start_button = QPushButton("Indítás")
        self.training_button = QPushButton("Elem tanítása")
        self.calibration_button = QPushButton("Kalibráció")

        layout.addWidget(self.input_field)
        layout.addWidget(self.start_button)
        layout.addWidget(self.training_button)
        layout.addWidget(self.calibration_button)

    def _run_task(self, task_type: str, *args):
        if self.assistant_thread and self.assistant_thread.isRunning():
            return

        self.hide()
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.show()
        self.overlay.prepare_ui()
        self.overlay.show()

        self.assistant_thread = QThread()
        self.assistant = DesktopAssistant()
        self.assistant.moveToThread(self.assistant_thread)

        # Signal-slot kapcsolatok felépítése
        self.stop_task_requested.connect(self.assistant.request_stop)
        self.assistant.status_updated.connect(self.overlay.status_label.setText)
        self.assistant.progress_updated.connect(self.overlay.progress_bar.setValue)
        self.assistant.log_message.connect(self.overlay.log_list.addItem)
        self.assistant.task_finished.connect(self._on_task_finished)

        # A szál leállítása után a worker törlődik
        self.assistant_thread.finished.connect(self.assistant.deleteLater)
        self.assistant_thread.finished.connect(self.assistant_thread.deleteLater)
        self.assistant_thread.finished.connect(self._cleanup_thread_references)

        if task_type == "start_task":
            self.start_task_requested.connect(self.assistant.start_task)
            self.assistant_thread.started.connect(lambda: self.start_task_requested.emit(*args))
        elif task_type == "start_calibration":
            self.start_calibration_requested.connect(self.assistant.start_calibration_task)
            self.assistant_thread.started.connect(self.start_calibration_requested.emit)

        self.assistant_thread.start()

    def _on_start_clicked(self):
        command = self.input_field.text().strip()
        if command:
            self._run_task("start_task", command)

    def _on_start_calibration(self):
        self._run_task("start_calibration")

    def _on_task_finished(self):
        if self.assistant_thread:
            # A jelek lecsatlakoztatása a duplikáció elkerülésére
            try:
                self.start_task_requested.disconnect()
                self.start_calibration_requested.disconnect()
            except RuntimeError:
                pass # Ha már lecsatlakoztak, nem baj

            self.assistant_thread.quit()
            self.assistant_thread.wait() # Megvárjuk, amíg a szál tényleg leáll

        self.overlay.hide()
        self.tray_icon.hide()
        self.showNormal()
        self.activateWindow()

    def _cleanup_thread_references(self):
        self.assistant = None
        self.assistant_thread = None

    def _on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Ha fut egy feladat, állítsa le
            if self.assistant_thread and self.assistant_thread.isRunning():
                self.stop_task_requested.emit()
            else: # Ha nem fut, csak hozza vissza az ablakot
                self._on_task_finished()

    # A "Tanítás" módhoz tartozó metódusok, ahogy az előző verzióban voltak
    def _on_train_element_clicked(self):
        if self.click_interceptor is not None: return
        self.hide()
        self.click_interceptor = ClickInterceptor(self)
        self.click_interceptor.clicked.connect(self._on_element_click_captured)
        self.click_interceptor.closed.connect(self._finalize_training)
        self.click_interceptor.showFullScreen()

    def _on_element_click_captured(self, x, y):
        name, ok = QInputDialog.getText(self, "Elem tanítása", "Add meg az elem nevét:")
        if ok and name.strip():
            self.memory_handler.save_element_location(name.strip(), {"x": x, "y": y})
        self.click_interceptor.close()

    def _finalize_training(self):
        if self.click_interceptor:
            self.click_interceptor.deleteLater()
            self.click_interceptor = None
        self.showNormal()
        self.activateWindow()
