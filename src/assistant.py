# src/assistant.py
"""Worker object running the assistant logic in a background thread."""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot

from pynput.keyboard import Key, Listener

from src.ai_handler import AIHandler
from src.computer_interface import ComputerInterface
from src.plugin_handler import PluginHandler
from src.memory_handler import MemoryHandler
from src.context_handler import ContextHandler
from src.config import DEBUG_MODE


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
        self.context_handler = ContextHandler()
        self._stop_requested = False
        self._stop_notified = False
        self._keyboard_listener: Listener | None = None
        self.failure_counter = 0
        self.max_failures = 3

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

            iteration = 0
            detail_level = "low"

            self.context_handler.start_new_task(user_input)
            self.failure_counter = 0

            while not self._stop_requested and self.failure_counter < self.max_failures:
                iteration += 1

                if DEBUG_MODE:
                    print("\n" + "=" * 20 + f" CIKLUS #{iteration} " + "=" * 20)
                    print(f"HIBA SZÁMLÁLÓ: {self.failure_counter}/{self.max_failures}")
                    print(f"KÉP MINŐSÉG A KÖR ELEJÉN: {detail_level}")
                    print("AKTUÁLIS ELŐZMÉNYEK:")
                    print(self.context_handler.get_formatted_history())
                    print("=" * 55)

                if self._check_for_stop():
                    break

                self.status_updated.emit("Képernyőállapot lekérése...")
                screen_info = self.computer_interface.get_screen_state(
                    detail_level=detail_level
                )
                self.progress_updated.emit(min(30, 10 + iteration * 5))

                if self._check_for_stop():
                    break

                self.status_updated.emit("AI döntés előkészítése...")
                available_plugins = self.plugin_handler.get_available_plugins()
                history_for_ai = self.context_handler.get_formatted_history()
                ai_action = self.ai_handler.get_ai_decision(
                    self.context_handler.original_task,
                    screen_info,
                    available_plugins,
                    detail_level=detail_level,
                    history=history_for_ai,
                )
                self.progress_updated.emit(min(60, 40 + iteration * 5))

                if self._check_for_stop():
                    break

                command = ai_action.get("command") if isinstance(ai_action, dict) else None
                arguments = (
                    ai_action.get("arguments", {}) if isinstance(ai_action, dict) else {}
                )

                recognized_commands = [
                    "kattints",
                    "gepelj",
                    "indits_programot",
                    "futtass_plugint",
                    "feladat_befejezve",
                    "kerj_jobb_minosegu_kepet",
                ]

                if command not in recognized_commands:
                    command_label = command if command else "ismeretlen parancs"
                    self.failure_counter += 1
                    self.log_message.emit(
                        f"Értelmezhetetlen vagy hibás parancs: {command}. "
                        f"Próbálkozás: {self.failure_counter}/{self.max_failures}"
                    )
                    self.status_updated.emit(
                        f"Hiba észlelve, újrapróbálkozás... ({self.failure_counter})"
                    )
                    self.context_handler.add_system_feedback(
                        (
                            f"Az előző parancsod ('{command_label}') sikertelen volt. "
                            "Hiba: Ismeretlen parancs. Próbálj egy másik megoldást, például egy vizuális keresést!"
                        )
                    )
                    detail_level = "low"
                    if command != "valaszolj_a_felhasznalonak":
                        continue

                if command == "kerj_jobb_minosegu_kepet":
                    self.log_message.emit(
                        "AI jobb minőségű képet kért, újrapróbálkozás..."
                    )
                    self.status_updated.emit("Képminőség növelése...")
                    detail_level = "high"
                    self.context_handler.add_assistant_action(ai_action)
                    continue

                if command == "feladat_befejezve":
                    if isinstance(arguments, dict):
                        message = arguments.get("uzenet")
                        if isinstance(message, str) and message.strip():
                            self.status_updated.emit(message.strip())
                            self.log_message.emit(f"AI üzenet: {message.strip()}")
                    detail_level = "low"
                    self.context_handler.add_assistant_action(ai_action)
                    break

                if command and isinstance(arguments, dict):
                    self.status_updated.emit("Parancs végrehajtása...")
                    if command == "kattints":
                        ai_coords = self._extract_coordinates(arguments)
                        if ai_coords:
                            real_coords = self._transform_coordinates(
                                ai_coords,
                                screen_info if isinstance(screen_info, dict) else {},
                            )
                            arguments.update(real_coords)
                    self.log_message.emit(f"Parancs: {command} {arguments}")
                    execution_result = self._handle_ai_action(
                        {"command": command, "arguments": arguments}
                    )
                    self.progress_updated.emit(min(90, 70 + iteration * 5))
                    detail_level = "low"
                    if execution_result.get("success"):
                        self.failure_counter = 0
                        self.context_handler.add_assistant_action(ai_action)
                    else:
                        command_label = command if command else "ismeretlen parancs"
                        self.failure_counter += 1
                        error_message = execution_result.get(
                            "error", "Ismeretlen hiba."
                        )
                        self.log_message.emit(f"Parancs sikertelen: {error_message}")
                        self.status_updated.emit(
                            f"Hiba észlelve, újrapróbálkozás... ({self.failure_counter})"
                        )
                        self.context_handler.add_system_feedback(
                            (
                                f"Az előző parancsod ('{command_label}') sikertelen volt. "
                                f"Hiba: {error_message}. Próbálj egy másik megoldást, például egy vizuális keresést!"
                            )
                        )
                        continue

                if self._check_for_stop():
                    break

            if self.failure_counter >= self.max_failures:
                self.log_message.emit(
                    f"A feladat leállt {self.max_failures} sikertelen próbálkozás után."
                )
                self.status_updated.emit("A feladatot nem sikerült végrehajtani.")

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
                if self.failure_counter < self.max_failures:
                    self.status_updated.emit("Feladat befejezve.")
            self.task_finished.emit()
            self._stop_requested = False
            self._stop_notified = False

    @Slot()
    def start_calibration_task(self) -> None:
        """Runs the automated calibration routine."""

        self._reset_stop_state()
        self._start_keyboard_listener()

        self.progress_updated.emit(0)
        self.status_updated.emit("Kalibráció indítása...")

        try:
            elements_to_calibrate = [
                {"name": "Start Menü", "prompt": "a Windows Start Menü ikonja a tálcán"},
                {
                    "name": "Rendszertálca Óra",
                    "prompt": "a rendszertálca területe, ahol az óra található",
                },
            ]

            total_elements = len(elements_to_calibrate) or 1

            for index, element in enumerate(elements_to_calibrate, start=1):
                if self._check_for_stop():
                    break

                element_name = element["name"]
                element_prompt = element["prompt"]

                self.status_updated.emit(f"Kalibráció: '{element_name}' keresése...")
                self.progress_updated.emit(int(((index - 1) / total_elements) * 100))

                screen_info = self.computer_interface.get_screen_state(detail_level="high")
                ai_action = self.ai_handler.get_calibration_coordinates(
                    screen_info, element_prompt
                )

                if self._check_for_stop():
                    break

                if not isinstance(ai_action, dict):
                    self.log_message.emit(
                        f"❌ Sikertelen kalibráció a(z) '{element_name}' elemhez. Váratlan AI válasz."
                    )
                    continue

                command = ai_action.get("command")
                arguments = ai_action.get("arguments", {}) or {}

                if command == "kattints":
                    ai_coords = self._extract_coordinates(arguments)
                    if ai_coords:
                        real_coords = self._transform_coordinates(ai_coords, screen_info)
                        self.memory_handler.save_element_location(element_name, real_coords)
                        self.log_message.emit(
                            f"✅ Elem kalibrálva: '{element_name}' -> {real_coords}"
                        )
                        try:
                            self.computer_interface._display_click_indicator(
                                real_coords["x"], real_coords["y"]
                            )
                        except Exception:
                            pass
                    else:
                        self.log_message.emit(
                            f"❌ AI nem talált koordinátákat a(z) '{element_name}' elemhez."
                        )
                else:
                    self.log_message.emit(
                        f"❌ Sikertelen kalibráció a(z) '{element_name}' elemhez. AI válasza: {ai_action}"
                    )

                self.progress_updated.emit(int((index / total_elements) * 100))

        finally:
            self._stop_keyboard_listener()
            self.progress_updated.emit(100)
            if self._stop_requested:
                self.log_message.emit("Kalibráció megszakítva.")
                self.status_updated.emit("Kalibráció megszakítva.")
            else:
                self.status_updated.emit("Kalibráció befejezve.")
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

    def _transform_coordinates(
        self, ai_coords: dict, image_dims: dict
    ) -> dict:
        """Scales coordinates from the downscaled image to the real screen size."""

        real_width = self.computer_interface.screen_width
        real_height = self.computer_interface.screen_height

        img_width = image_dims.get("width") if isinstance(image_dims, dict) else None
        img_height = image_dims.get("height") if isinstance(image_dims, dict) else None

        ai_x = ai_coords.get("x") if isinstance(ai_coords, dict) else None
        ai_y = ai_coords.get("y") if isinstance(ai_coords, dict) else None

        if not all(
            [
                real_width,
                real_height,
                img_width,
                img_height,
                isinstance(ai_x, (int, float)),
                isinstance(ai_y, (int, float)),
            ]
        ):
            return ai_coords

        scale_x = real_width / img_width
        scale_y = real_height / img_height

        real_x = int(float(ai_x) * scale_x)
        real_y = int(float(ai_y) * scale_y)

        return {"x": real_x, "y": real_y}

    def _handle_ai_action(self, ai_action: dict) -> dict:
        command = ai_action.get("command")
        arguments = ai_action.get("arguments", {}) or {}

        if command == "futtass_plugint":
            plugin_name = self._extract_plugin_name(arguments)
            if not plugin_name:
                self.log_message.emit("A plugin futtatásához plugin_nev megadása szükséges.")
                return {
                    "success": False,
                    "error": "A plugin futtatásához plugin_nev megadása szükséges.",
                }

            try:
                self.plugin_handler.execute_plugin(plugin_name)
                self.log_message.emit(f"Plugin futtatva: {plugin_name}")
            except Exception as exc:
                error_message = f"Plugin futtatása sikertelen ({plugin_name}): {exc}"
                self.log_message.emit(error_message)
                return {"success": False, "error": error_message}
            return {"success": True}

        if command == "kattints":
            element_name = self._extract_element_name_from_arguments(arguments)
            coords = self._extract_coordinates(arguments)

            click_source: str | None = None

            if element_name:
                stored_coords = self.memory_handler.get_element_location(element_name)

                if coords:
                    self.memory_handler.save_element_location(element_name, coords)
                    message_prefix = "Pozíció frissítve" if stored_coords else "Új pozíció elmentve"
                    self.log_message.emit(
                        f"{message_prefix}: {element_name} -> ({coords['x']}, {coords['y']})"
                    )
                elif stored_coords:
                    coords = stored_coords
                    click_source = "memória"
                    self.log_message.emit(
                        f"Memóriából kattintás: {element_name} -> ({coords['x']}, {coords['y']})"
                    )
                else:
                    self.log_message.emit(
                        f"Leírás alapján az elem azonosítva ('{element_name}'), de koordinátát nem kaptunk."
                    )

            if coords:
                self.computer_interface.click_at(
                    coords["x"],
                    coords["y"],
                    element_name,
                    source=click_source,
                )
                return {"success": True}

            error_message = "A kattintáshoz érvényes koordináták szükségesek."
            self.log_message.emit(error_message)
            return {"success": False, "error": error_message}

        return self.computer_interface.execute_command(command, arguments)

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
