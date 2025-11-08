# src/computer_interface.py

from __future__ import annotations

import base64
import io
import subprocess
from collections.abc import Sequence

import pyautogui
from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtGui import QGuiApplication

from src.gui.widgets import ClickIndicator


class ComputerInterface:
    def __init__(self) -> None:
        self._active_indicators: list[ClickIndicator] = []

    def get_screen_state(self) -> str:
        """Készítsen teljes képernyőképet és adja vissza Base64 formátumban."""

        try:
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
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

    def execute_command(self, command: str, arguments: dict) -> None:
        """Valódi parancsok végrehajtása PyAutoGUI és subprocess segítségével."""

        args = arguments if isinstance(arguments, dict) else {}

        if command == "kattints":
            x = args.get("x")
            y = args.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                self.click_at(int(x), int(y), args.get("description"))
            else:
                print("A 'kattints' parancshoz érvényes x és y koordináták szükségesek.")
            return

        if command == "gepelj":
            text = args.get("szoveg") or args.get("text") or ""
            if not isinstance(text, str):
                print("A 'gepelj' parancshoz szöveg szükséges.")
                return
            try:
                pyautogui.typewrite(text)
            except Exception as exc:  # pragma: no cover - vizuális környezet hiánya esetén
                print(f"A gépelés nem sikerült: {exc}")
            return

        if command == "indits_programot":
            program = (
                args.get("program")
                or args.get("path")
                or args.get("command")
                or args.get("exe")
            )
            extra_args = args.get("args")
            if isinstance(extra_args, str):
                extra_args = [extra_args]
            if isinstance(extra_args, Sequence):
                extra_args = list(extra_args)
            else:
                extra_args = []

            if isinstance(program, str) and program.strip():
                command_list = [program.strip(), *extra_args]
                try:
                    subprocess.Popen(command_list)
                except Exception as exc:  # pragma: no cover - rendszerfüggő hibák
                    print(f"A program indítása nem sikerült: {exc}")
            else:
                print("Az 'indits_programot' parancshoz érvényes program elérési út szükséges.")
            return

        print(f"Ismeretlen parancs: {command} {arguments}")

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
