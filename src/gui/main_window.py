# src/gui/main_window.py

from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QInputDialog, QLineEdit, QMainWindow,
    QPushButton, QSystemTrayIcon, QVBoxLayout, QWidget, QStyle
)
from PySide6.QtGui import QIcon

from src.assistant import DesktopAssistant
from src.gui.click_interceptor import ClickInterceptor
from src.gui.overlay_window import OverlayWindow
from src.memory_handler import MemoryHandler

class MainWindow(QMainWindow):
    stop_task_requested = Signal() # Csak a leállításhoz kell jel

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
        self._setup_connections()

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

    def _setup_connections(self):
        self.start_button.clicked.connect(self._on_start_clicked)
        self.training_button.clicked.connect(self._on_train_element_clicked)
        self.calibration_button.clicked.connect(self._on_start_calibration)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.overlay.stop_button.clicked.connect(self.stop_task_requested.emit)

    def _run_task(self, start_slot, *args):
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

        # Signal-slot kapcsolatok
        self.stop_task_requested.connect(self.assistant.request_stop)
        self.assistant.status_updated.connect(self.overlay.status_label.setText)
        self.assistant.progress_updated.connect(self.overlay.progress_bar.setValue)
        self.assistant.log_message.connect(self.overlay.log_list.addItem)
        self.assistant.task_finished.connect(self._on_task_finished)
        
        # A szál leállítása után a worker törlődik
        self.assistant_thread.finished.connect(self.assistant.deleteLater)
        self.assistant_thread.finished.connect(self.assistant_thread.deleteLater)
        self.assistant_thread.finished.connect(self._cleanup_thread_references)

        # KÖZVETLEN METÓDUSHÍVÁS A SZÁL INDULÁSAKOR
        # A 'start_slot' a worker metódusa (pl. start_task), amit átadunk.
        # A lambda biztosítja, hogy a paraméterek is átadódjanak.
        self.assistant_thread.started.connect(lambda: start_slot(*args))

        self.assistant_thread.start()

    def _on_start_clicked(self):
        command = self.input_field.text().strip()
        if command:
            # Itt a DesktopAssistant.start_task metódusát adjuk át
            self._run_task(DesktopAssistant.start_task, command)

    def _on_start_calibration(self):
        # Itt a DesktopAssistant.start_calibration_task metódusát adjuk át
        self._run_task(DesktopAssistant.start_calibration_task)

    def _on_task_finished(self):
        if self.assistant_thread:
            self.assistant_thread.quit()
            self.assistant_thread.wait()
        
        self.overlay.hide()
        self.tray_icon.hide()
        self.showNormal()
        self.activateWindow()

    def _cleanup_thread_references(self):
        # A lecsatlakoztatást ide helyezzük, hogy biztosan megtörténjen
        if self.assistant:
            try:
                self.stop_task_requested.disconnect(self.assistant.request_stop)
            except RuntimeError:
                pass
        self.assistant = None
        self.assistant_thread = None
        
    def _on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.assistant_thread and self.assistant_thread.isRunning():
                self.stop_task_requested.emit()
            else:
                self._on_task_finished()
                
    # A "Tanítás" módhoz tartozó metódusok
    def _on_train_element_clicked(self):
        if self.click_interceptor: return
        self.hide()
        self.click_interceptor = ClickInterceptor(self)
        self.click_interceptor.clicked.connect(self._on_element_click_captured)
        self.click_interceptor.closed.connect(self._finalize_training)
        self.click_interceptor.showFullScreen()

    def _on_element_click_captured(self, x, y):
        name, ok = QInputDialog.getText(self, "Elem tanítása", "Add meg az elem nevét:")
        if ok and name.strip():
            self.memory_handler.save_element_location(name.strip(), {"x": x, "y": y})
        if self.click_interceptor:
            self.click_interceptor.close()

    def _finalize_training(self):
        if self.click_interceptor:
            self.click_interceptor.deleteLater()
            self.click_interceptor = None
        self.showNormal()
        self.activateWindow()