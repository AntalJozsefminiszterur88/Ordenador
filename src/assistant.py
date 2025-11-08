# src/assistant.py
"""Worker object running the assistant logic in a background thread."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from src.ai_handler import AIHandler
from src.computer_interface import ComputerInterface
from src.memory_handler import MemoryHandler


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
        self.memory_handler = MemoryHandler()

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
            if self._try_handle_from_memory(user_input):
                return

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
                self._handle_ai_action(ai_action)
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

    def _try_handle_from_memory(self, user_input: str) -> bool:
        element_name = self._extract_element_name(user_input)
        if not element_name:
            return False

        coords = self.memory_handler.get_element_location(element_name)
        if not coords:
            return False

        self.status_updated.emit("Korábban mentett pozíció használata...")
        self.log_message.emit(
            f"Memóriában talált pozíció: {element_name} -> ({coords['x']}, {coords['y']})"
        )
        self.computer_interface.click_at(
            coords["x"], coords["y"], element_name, source="memória"
        )
        return True

    def _handle_ai_action(self, ai_action: dict) -> None:
        command = ai_action.get("command")
        arguments = ai_action.get("arguments", {}) or {}

        if command == "kattints":
            element_name = self._extract_element_name_from_arguments(arguments)
            coords = self._extract_coordinates(arguments)

            if element_name:
                stored_coords = self.memory_handler.get_element_location(element_name)
                if stored_coords:
                    self.log_message.emit(
                        f"Memóriából kattintás: {element_name} -> ({stored_coords['x']}, {stored_coords['y']})"
                    )
                    self.computer_interface.click_at(
                        stored_coords["x"],
                        stored_coords["y"],
                        element_name,
                        source="memória",
                    )
                    return

                if coords:
                    self.memory_handler.save_element_location(element_name, coords)
                    self.log_message.emit(
                        f"Új pozíció elmentve: {element_name} -> ({coords['x']}, {coords['y']})"
                    )

            if coords:
                self.computer_interface.click_at(
                    coords["x"], coords["y"], element_name
                )
                return

        self.computer_interface.execute_command(command, arguments)

    @staticmethod
    def _extract_element_name(text: str) -> str | None:
        for quote in ("'", '"'):
            if quote in text:
                parts = text.split(quote)
                if len(parts) >= 3:
                    candidate = parts[1].strip()
                    if candidate:
                        return candidate
        return None

    @staticmethod
    def _extract_element_name_from_arguments(arguments: dict) -> str | None:
        possible_keys = [
            "element_name",
            "element",
            "elem",
            "elem_leirasa",
            "leiras",
            "description",
        ]
        for key in possible_keys:
            value = arguments.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _extract_coordinates(arguments: dict) -> dict[str, int] | None:
        candidates = []
        if isinstance(arguments.get("coords"), dict):
            candidates.append(arguments["coords"])
        candidates.append(arguments)

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            x = candidate.get("x")
            y = candidate.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                return {"x": int(x), "y": int(y)}
        return None
