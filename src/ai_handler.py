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
        'gepelj', 'indits_programot', 'valaszolj_a_felhasznalonak', 'futtass_plugint'.
        A 'futtass_plugint' parancs esetén add meg, hogy melyik plugint kell futtatni a
        "plugin_nev" mezőben. Például: {"command": "futtass_plugint", "arguments": {"plugin_nev": "open_notepad"}}
        """

    def get_ai_decision(
        self,
        user_prompt: str,
        screen_state: str,
        available_plugins: list[dict[str, str]] | None = None,
    ) -> dict:
        print("🧠 AI gondolkodik...")
        try:
            plugins_text = "Nincsenek elérhető pluginek."
            if available_plugins:
                plugin_lines = [
                    f"- {plugin['name']}: {plugin['description']}"
                    for plugin in available_plugins
                ]
                plugins_text = "\n".join(plugin_lines)

            user_message = (
                "Képernyő: '{screen}'. Feladat: '{task}'.\n"
                "Használhatod a GUI-t, vagy ha releváns, futtathatod az alábbi pluginek"
                " egyikét:\n{plugins}\nMi a következő lépés?"
            ).format(screen=screen_state, task=user_prompt, plugins=plugins_text)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"}
            )
            decision_str = response.choices[0].message.content
            return json.loads(decision_str)
        except Exception as e:
            print(f"Hiba az API hívás során: {e}")
            return {"command": "valaszolj_a_felhasznalonak", "arguments": {"uzenet": "Hiba történt."}}
