# src/assistant.py
"""Worker object running the assistant logic in a background thread."""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot

from pynput.keyboard import Key, Listener

from src.ai_handler import AIHandler
from src.computer_interface import ComputerInterface
from src.plugin_handler import PluginHandler
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
        self.plugin_handler = PluginHandler()
        self._stop_requested = False
        self._stop_notified = False
        self._keyboard_listener: Listener | None = None

    @Slot(str)
    def start_task(self, user_input: str) -> None:
        """Execute the assistant workflow for the provided user input."""

        if not user_input.strip():
            self.log_message.emit("Nem érkezett parancs a feldolgozáshoz.")
            self.progress_updated.emit(100)
            self.status_updated.emit("Nincs végrehajtható feladat.")
            self.task_finished.emit()
            return

        self._reset_stop_state()
        self._start_keyboard_listener()

        self.progress_updated.emit(0)
        self.status_updated.emit("Feladat indítása...")
        self.log_message.emit(f"Felhasználói utasítás: {user_input}")

        try:
            if self._check_for_stop():
                return

            if self._try_handle_from_memory(user_input):
                return

            original_task = user_input
            iteration = 0

            while not self._stop_requested:
                iteration += 1

                if self._check_for_stop():
                    break

                self.status_updated.emit("Képernyőállapot lekérése...")
                screen_state = self.computer_interface.get_screen_state()
                self.progress_updated.emit(min(30, 10 + iteration * 5))

                if self._check_for_stop():
                    break

                self.status_updated.emit("AI döntés előkészítése...")
                available_plugins = self.plugin_handler.get_available_plugins()
                ai_action = self.ai_handler.get_ai_decision(
                    original_task,
                    screen_state,
                    available_plugins,
                )
                self.progress_updated.emit(min(60, 40 + iteration * 5))

                if self._check_for_stop():
                    break

                command = ai_action.get("command") if isinstance(ai_action, dict) else None
                arguments = ai_action.get("arguments", {}) if isinstance(ai_action, dict) else {}

                if command == "feladat_befejezve":
                    if isinstance(arguments, dict):
                        message = arguments.get("uzenet")
                        if isinstance(message, str) and message.strip():
                            self.status_updated.emit(message.strip())
                            self.log_message.emit(f"AI üzenet: {message.strip()}")
                    break

                if command and isinstance(arguments, dict):
                    self.status_updated.emit("Parancs végrehajtása...")
                    self.log_message.emit(f"Parancs: {command} {arguments}")
                    self._handle_ai_action({"command": command, "arguments": arguments})
                    self.progress_updated.emit(min(90, 70 + iteration * 5))
                else:
                    self.log_message.emit("Az AI nem adott érvényes parancsot.")
                    self.status_updated.emit("Érvénytelen AI parancs érkezett.")

                if self._check_for_stop():
                    break

        except Exception as exc:  # pragma: no cover - defensive logging
            self.log_message.emit(f"Hiba történt: {exc}")
            self.status_updated.emit("Hiba történt a feldolgozás során.")
        finally:
            self._stop_keyboard_listener()
            self.progress_updated.emit(100)
            if self._stop_requested:
                self.log_message.emit("Feladat megszakítva.")
                self.status_updated.emit("Feladat megszakítva.")
            else:
                self.status_updated.emit("Feladat befejezve.")
            self.task_finished.emit()
            self._stop_requested = False
            self._stop_notified = False

    def _start_keyboard_listener(self) -> None:
        """Start the global keyboard listener to capture ESC presses."""

        if self._keyboard_listener is None:
            self._keyboard_listener = Listener(on_press=self._handle_key_press)
            self._keyboard_listener.start()

    def _stop_keyboard_listener(self) -> None:
        """Ensure the keyboard listener is stopped and cleaned up."""

        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener.join()
            self._keyboard_listener = None

    def _reset_stop_state(self) -> None:
        """Reset stop flags before starting a new task."""

        self._stop_requested = False
        self._stop_notified = False

    def _handle_key_press(self, key: Key) -> None:
        """React to ESC key presses by queueing a stop request."""

        if key == Key.esc:
            print("ESC lenyomva, leállítás kérése...")
            QMetaObject.invokeMethod(self, "request_stop", Qt.QueuedConnection)

    @Slot()
    def request_stop(self) -> None:
        """Idempotent stop request that can be triggered from multiple sources."""

        if not self._stop_requested:
            self._stop_requested = True
            self._stop_notified = False

    def _check_for_stop(self) -> bool:
        """Check whether a stop was requested and emit user feedback once."""

        if not self._stop_requested:
            return False

        if not self._stop_notified:
            self._stop_notified = True
            self.status_updated.emit("Megszakítás folyamatban...")
            self.log_message.emit("Feladat megszakítása kérése érkezett.")
        return True

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

        if command == "futtass_plugint":
            plugin_name = self._extract_plugin_name(arguments)
            if not plugin_name:
                self.log_message.emit("A plugin futtatásához plugin_nev megadása szükséges.")
                return

            try:
                self.plugin_handler.execute_plugin(plugin_name)
                self.log_message.emit(f"Plugin futtatva: {plugin_name}")
            except Exception as exc:
                self.log_message.emit(f"Plugin futtatása sikertelen ({plugin_name}): {exc}")
            return

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
    def _extract_plugin_name(arguments: dict) -> str | None:
        for key in ("plugin_nev", "plugin", "name"):
            value = arguments.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

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
