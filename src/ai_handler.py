# src/ai_handler.py
import json
from openai import OpenAI
from src.config import OPENAI_API_KEY, DEBUG_MODE

class AIHandler:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.system_prompt = """
        Te egy hasznos asztali asszisztens vagy. A feladatod, hogy a felhasználó kérését
        és a képernyő aktuális állapotát figyelembe véve egyetlen, konkrét, végrehajtható
        parancsot adj vissza JSON formátumban. A lehetséges parancsok: 'kattints',
        'gepelj', 'indits_programot', 'valaszolj_a_felhasznalonak', 'futtass_plugint',
        'kerj_jobb_minosegu_kepet', 'feladat_befejezve'. A 'futtass_plugint' parancs
        esetén add meg, hogy melyik plugint kell futtatni a "plugin_nev" mezőben.
        Például:
        {"command": "futtass_plugint", "arguments": {"plugin_nev": "open_notepad"}}
        A 'kattints' parancs formátuma: '- 'kattints': {'x': <szám>, 'y': <szám>,
        'leiras': '<MIT LÁTSZ OTT?>'}. Ha vizuálisan azonosítasz egy elemet a
        képernyőn, KÖTELEZŐ megadnod a 'leiras' mezőt is!
        Mindig kapsz egy lekicsinyített képet a teljes képernyőről. A válaszodban a
        'kattints' parancs koordinátáit MINDIG ehhez a lekicsinyített képhez
        viszonyítva, annak a koordináta-rendszerében add meg!
        A 'feladat_befejezve' parancsot akkor add vissza, ha a felhasználó kérése
        teljesült. Az argumentumban opcionálisan visszaadhatsz egy "uzenet" mezőt a
        felhasználónak szánt rövid visszajelzéssel. A 'kerj_jobb_minosegu_kepet'
        parancsnál add meg a "leiras" mezőben, miért van szükség jobb képre.
        Fontos: Ha a kapott kép minősége túl alacsony ahhoz, hogy egy kritikus részletet
        (pl. egy gomb feliratát) elolvass, akkor ne tippelj! Használd a
        'kerj_jobb_minosegu_kepet' parancsot, és kérj egy részletesebb képet.
        Minden lépés után kaphatsz visszajelzést az előző parancsod eredményéről. Ha egy
        parancs sikertelen volt, KÖTELEZŐ egy másik stratégiát választanod! Például, ha az
        'indits_programot' parancs elbukik, mert a program nem található, akkor a
        következő lépésben próbáld meg vizuálisan megkeresni a program ikonját a képernyőn
        a 'kattints' paranccsal.
        """

    def get_ai_decision(
        self,
        user_prompt: str,
        screen_info: dict | None,
        available_plugins: list[dict[str, str]] | None = None,
        detail_level: str = "low",
        feedback: str = "",
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

            feedback_text = (
                f"Visszajelzés az előző lépésről: {feedback}. " if feedback else ""
            )

            image_data = screen_info.get("image_data", "") if isinstance(screen_info, dict) else ""
            image_width = screen_info.get("width", 0) if isinstance(screen_info, dict) else 0
            image_height = screen_info.get("height", 0) if isinstance(screen_info, dict) else 0

            if DEBUG_MODE:
                print("\n--- AI PROMPT KÜLDÉSE ---")
                print("SZÖVEGES PROMPT:")
                print(f"    Feladat: '{user_prompt}'")
                print(f"    Visszajelzés: '{feedback if feedback else 'Nincs'}'")
                print(f"    Pluginek: {plugins_text}")
                print(f"KÉP ADAT (hossz): {len(image_data)} karakter")
                print(f"    KÉP MÉRET: {image_width}x{image_height}")
                print(f"KÉP MINŐSÉG: {detail_level}")
                print("--------------------------")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Feladat: '{user_prompt}'. A mellékelt kép mérete {image_width}x{image_height} pixel. "
                                    f"{feedback_text}A pluginek: {plugins_text}. "
                                    "Mi a következő lépés?"
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": detail_level,
                                },
                            },
                        ],
                    },
                ],
                response_format={"type": "json_object"}
            )
            decision_str = response.choices[0].message.content
            if DEBUG_MODE:
                print("\n--- NYERS AI VÁLASZ ---")
                print(decision_str)
                print("----------------------")
            return json.loads(decision_str)
        except Exception as e:
            print(f"Hiba az API hívás során: {e}")
            return {"command": "api_hiba", "arguments": {"hiba_uzenet": str(e)}}
