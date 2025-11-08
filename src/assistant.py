# src/assistant.py
"""Worker object running the assistant logic in a background thread."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from src.ai_handler import AIHandler
from src.computer_interface import ComputerInterface


class DesktopAssistant(QObject):
    """Qt compatible assistant that reports progress back to the GUI."""

    status_updated = Signal(str)
    progress_updated = Signal(int)
    log_message = Signal(str)
    task_finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.ai_handler = AIHandler()
        self.computer_interface = ComputerInterface()

    @Slot(str)
    def start_task(self, user_input: str) -> None:
        """Execute the assistant workflow for the provided user input."""

        if not user_input.strip():
            self.log_message.emit("Nem érkezett parancs a feldolgozáshoz.")
            self.progress_updated.emit(100)
            self.status_updated.emit("Nincs végrehajtható feladat.")
            self.task_finished.emit()
            return

        self.progress_updated.emit(0)
        self.status_updated.emit("Feladat indítása...")
        self.log_message.emit(f"Felhasználói utasítás: {user_input}")

        try:
            self.status_updated.emit("Képernyőállapot lekérése...")
            screen_state = self.computer_interface.get_screen_state()
            self.progress_updated.emit(25)

            self.status_updated.emit("AI döntés előkészítése...")
            ai_action = self.ai_handler.get_ai_decision(user_input, screen_state)
            self.progress_updated.emit(50)

            if "command" in ai_action and "arguments" in ai_action:
                self.status_updated.emit("Parancs végrehajtása...")
                self.log_message.emit(
                    f"Parancs: {ai_action['command']} {ai_action['arguments']}"
                )
                self.computer_interface.execute_command(
                    ai_action["command"], ai_action["arguments"]
                )
                self.progress_updated.emit(90)
            else:
                self.log_message.emit("Az AI nem adott érvényes parancsot.")

        except Exception as exc:  # pragma: no cover - defensive logging
            self.log_message.emit(f"Hiba történt: {exc}")
            self.status_updated.emit("Hiba történt a feldolgozás során.")
        finally:
            self.progress_updated.emit(100)
            self.status_updated.emit("Feladat befejezve.")
            self.task_finished.emit()
