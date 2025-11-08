# src/computer_interface.py

class ComputerInterface:
    def get_screen_state(self) -> str:
        """Szimulálja a képernyő "látását"."""
        print("🖥️  Képernyő 'beolvasása'...")
        return "Az asztalon egy 'Levelezés' és egy 'Böngésző' ikon látható."

    def click_at(self, x: int, y: int, description: str | None = None, source: str | None = None) -> None:
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
                self.click_at(int(x), int(y))
                return

        print(f"⚡️ Parancs végrehajtása: {command} {arguments}")
        # A JÖVŐBEN: Ide jön a valós PyAutoGUI logika
