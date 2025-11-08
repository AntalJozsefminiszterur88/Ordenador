# src/assistant.py
from src.ai_handler import AIHandler
from src.computer_interface import ComputerInterface

class DesktopAssistant:
    def __init__(self):
        print("--- Asztali AI Asszisztens inicializálása ---")
        self.ai_handler = AIHandler()
        self.computer_interface = ComputerInterface()

    def run(self):
        print("Asszisztens elindítva. Írj be egy parancsot, vagy 'kilepes' a bezáráshoz.")
        while True:
            try:
                user_input = input("\n> Te: ")
                if user_input.lower() == "kilepes":
                    break

                # 1. Érzékelés
                screen_state = self.computer_interface.get_screen_state()
                
                # 2. Gondolkodás
                ai_action = self.ai_handler.get_ai_decision(user_input, screen_state)
                
                # 3. Cselekvés
                if "command" in ai_action and "arguments" in ai_action:
                    self.computer_interface.execute_command(
                        ai_action["command"], 
                        ai_action["arguments"]
                    )
                else:
                    print("Az AI nem adott érvényes parancsot.")

            except KeyboardInterrupt:
                break
        
        print("\nProgram leállítva.")
