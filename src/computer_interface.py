# src/computer_interface.py

from __future__ import annotations

import base64
import io
import subprocess
from collections.abc import Sequence

import pyautogui
from PIL import Image
from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtGui import QGuiApplication

from src.gui.widgets import ClickIndicator


class ComputerInterface:
    def __init__(self) -> None:
        self._active_indicators: list[ClickIndicator] = []

    def get_screen_state(self, detail_level: str = "low") -> str:
        """Készítsen teljes képernyőképet és adja vissza Base64 formátumban."""

        try:
            screenshot = pyautogui.screenshot()

            if detail_level == "high":
                max_size = (2048, 2048)
                quality = 95
            else:
                max_size = (1024, 1024)
                quality = 80

            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            screenshot.save(buffer, format="JPEG", quality=quality)
            img_bytes = buffer.getvalue()
            encoded = base64.b64encode(img_bytes).decode("ascii")
            return encoded
        except Exception as exc:  # pragma: no cover - vizuális környezet hiánya esetén
            print(f"Nem sikerült képernyőképet készíteni: {exc}")
            return ""

    def click_at(
        self,
        x: int,
        y: int,
        description: str | None = None,
        source: str | None = None,
    ) -> None:
        details = f" ({description})" if description else ""
        origin = f" forrás: {source}" if source else ""
        print(f"🖱️  Kattintás a {x}, {y} pozíción{details}.{origin}")
        self._display_click_indicator(x, y)
        try:
            pyautogui.click(x, y)
        except Exception as exc:  # pragma: no cover - vizuális környezet hiánya esetén
            print(f"A kattintás végrehajtása nem sikerült: {exc}")

    def execute_command(self, command: str, arguments: dict) -> dict:
        """Valódi parancsok végrehajtása PyAutoGUI és subprocess segítségével."""

        args = arguments if isinstance(arguments, dict) else {}

        if command == "kattints":
            x = args.get("x")
            y = args.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                self.click_at(int(x), int(y), args.get("description"))
                return {"success": True}
            print("A 'kattints' parancshoz érvényes x és y koordináták szükségesek.")
            return {
                "success": False,
                "error": "A 'kattints' parancshoz érvényes x és y koordináták szükségesek.",
            }

        if command == "gepelj":
            text = args.get("szoveg") or args.get("text") or ""
            if not isinstance(text, str):
                error_message = "A 'gepelj' parancshoz szöveg szükséges."
                print(error_message)
                return {"success": False, "error": error_message}
            try:
                pyautogui.typewrite(text)
            except Exception as exc:  # pragma: no cover - vizuális környezet hiánya esetén
                error_message = f"A gépelés nem sikerült: {exc}"
                print(error_message)
                return {"success": False, "error": error_message}
            return {"success": True}

        if command == "indits_programot":
            program_nev = (
                args.get("program_nev")
                or args.get("program")
                or args.get("path")
                or args.get("command")
                or args.get("exe")
            )

            if not program_nev:
                return {"success": False, "error": "A program_nev megadása kötelező."}

            if isinstance(program_nev, Sequence) and not isinstance(program_nev, str):
                command_sequence = list(program_nev)
            else:
                command_sequence = [str(program_nev)]

            extra_args = args.get("args")
            if isinstance(extra_args, str):
                command_sequence.append(extra_args)
            elif isinstance(extra_args, Sequence):
                command_sequence.extend(str(arg) for arg in extra_args)

            try:
                subprocess.Popen(command_sequence)
                return {"success": True}
            except FileNotFoundError:
                program_display = command_sequence[0] if command_sequence else program_nev
                return {
                    "success": False,
                    "error": f"A(z) '{program_display}' program nem található.",
                }
            except Exception as exc:  # pragma: no cover - rendszerfüggő hibák
                return {"success": False, "error": str(exc)}

        print(f"Ismeretlen parancs: {command} {arguments}")
        return {"success": False, "error": f"Ismeretlen parancs: {command}"}

    def _display_click_indicator(self, x: int, y: int) -> None:
        """Display the click indicator centred on the provided coordinates."""

        app = QGuiApplication.instance()
        if app is None:
            return

        def spawn_indicator() -> None:
            indicator = ClickIndicator()
            indicator.move(x - indicator.width() // 2, y - indicator.height() // 2)
            indicator.show()
            indicator.raise_()
            self._active_indicators.append(indicator)
            indicator.destroyed.connect(
                lambda _=None, ref=indicator: self._remove_indicator(ref)
            )

        QMetaObject.invokeMethod(app, spawn_indicator, Qt.QueuedConnection)

    def _remove_indicator(self, indicator: ClickIndicator) -> None:
        try:
            self._active_indicators.remove(indicator)
        except ValueError:
            pass
