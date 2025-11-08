# src/config.py
import os
from dotenv import load_dotenv

# .env fájl betöltése
load_dotenv()

# API kulcs kiolvasása a környezeti változókból
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ellenőrzés, hogy a kulcs meg van-e adva
if not OPENAI_API_KEY:
    raise ValueError("Az OPENAI_API_KEY nincs beállítva! Hozd létre a .env fájlt a .env.example alapján.")

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")
