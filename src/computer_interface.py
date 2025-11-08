# src/computer_interface.py

class ComputerInterface:
    def get_screen_state(self) -> str:
        """Szimulálja a képernyő "látását"."""
        print("🖥️  Képernyő 'beolvasása'...")
        return "Az asztalon egy 'Levelezés' és egy 'Böngésző' ikon látható."

    def execute_command(self, command: str, arguments: dict):
        """Szimulálja egy parancs végrehajtását."""
        print(f"⚡️ Parancs végrehajtása: {command} {arguments}")
        # A JÖVŐBEN: Ide jön a valós PyAutoGUI logika
