# src/computer_interface.py

from __future__ import annotations

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtGui import QGuiApplication

from src.gui.widgets import ClickIndicator


class ComputerInterface:
    def __init__(self) -> None:
        self._active_indicators: list[ClickIndicator] = []

    def get_screen_state(self) -> str:
        """Szimulálja a képernyő "látását"."""
        print("🖥️  Képernyő 'beolvasása'...")
        return "Az asztalon egy 'Levelezés' és egy 'Böngésző' ikon látható."

    def click_at(
        self,
        x: int,
        y: int,
        description: str | None = None,
        source: str | None = None,
    ) -> None:
        """Szimulálja egy adott koordinátára történő kattintást."""

        details = f" ({description})" if description else ""
        origin = f" forrás: {source}" if source else ""
        print(f"🖱️  Kattintás a {x}, {y} pozíción{details}.{origin}")

    def execute_command(self, command: str, arguments: dict):
        """Szimulálja egy parancs végrehajtását."""
        if command == "kattints":
            x = arguments.get("x")
            y = arguments.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                x_int = int(x)
                y_int = int(y)
                self._display_click_indicator(x_int, y_int)
                self.click_at(x_int, y_int)
                return

        print(f"⚡️ Parancs végrehajtása: {command} {arguments}")
        # A JÖVŐBEN: Ide jön a valós PyAutoGUI logika

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
