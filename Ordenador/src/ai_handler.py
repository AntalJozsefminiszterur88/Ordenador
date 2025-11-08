# src/ai_handler.py
import json
from openai import OpenAI
from src.config import OPENAI_API_KEY

class AIHandler:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.system_prompt = """
        Te egy hasznos asztali asszisztens vagy. A feladatod, hogy a felhasználó kérését
        és a képernyő aktuális állapotát figyelembe véve egyetlen, konkrét, végrehajtható
        parancsot adj vissza JSON formátumban. A lehetséges parancsok: 'kattints', 
        'gepelj', 'indits_programot', 'valaszolj_a_felhasznalonak'.
        Például: {"command": "indits_programot", "arguments": {"program_nev": "böngésző"}}
        """

    def get_ai_decision(self, user_prompt: str, screen_state: str) -> dict:
        print("🧠 AI gondolkodik...")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Képernyő: '{screen_state}'. Feladat: '{user_prompt}'. Mi a következő lépés?"}
                ],
                response_format={"type": "json_object"}
            )
            decision_str = response.choices[0].message.content
            return json.loads(decision_str)
        except Exception as e:
            print(f"Hiba az API hívás során: {e}")
            return {"command": "valaszolj_a_felhasznalonak", "arguments": {"uzenet": "Hiba történt."}}
