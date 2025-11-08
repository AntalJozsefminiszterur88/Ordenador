# main.py
# Ez a projekt fő belépési pontja.
# Egyetlen feladata, hogy elindítsa az AI asszisztenst.

from src.assistant import DesktopAssistant

if __name__ == "__main__":
    # Létrehozzuk az asszisztens egy példányát
    asszisztens = DesktopAssistant()
    
    # Elindítjuk az asszisztens fő ciklusát
    asszisztens.run()
