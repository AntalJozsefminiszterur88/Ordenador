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
        Az eredeti feladat mellett kapsz egy 'Előzmények' szekciót is, ami leírja, hol tart a
        folyamat. A következő lépést mindig az eredeti cél és az eddigi előzmények alapján
        határozd meg! Minden lépés után kaphatsz visszajelzést az előző parancsod
        eredményéről. Ha egy parancs sikertelen volt, KÖTELEZŐ egy másik stratégiát
        választanod! Például, ha az 'indits_programot' parancs elbukik, mert a program nem
        található, akkor a következő lépésben próbáld meg vizuálisan megkeresni a program
        ikonját a képernyőn a 'kattints' paranccsal.
        """
        self.system_prompt_grid_calibration = """
        Te egy precíz vizuális elem felismerő vagy. Egy képernyőképet kapsz, amin egy kalibrációs
        rács látható feliratozott célpontokkal (A, B, C, stb.). A feladatod, hogy az ÖSSZES LÁTHATÓ
        célpontot azonosítsd, és visszaadd a pozícióikat a lekicsinyített kép koordináta-
        rendszerében. A választ egy JSON listaként add vissza, ahol minden elem egy szótár,
        ami tartalmazza a pont 'label' (címke) és 'coords' (koordináták) mezőit.
        Példa válasz:
        [
          {"label": "A", "coords": {"x": 50, "y": 50}},
          {"label": "B", "coords": {"x": 950, "y": 50}},
          {"label": "C", "coords": {"x": 950, "y": 950}},
          {"label": "D", "coords": {"x": 50, "y": 950}},
          {"label": "E", "coords": {"x": 500, "y": 500}}
        ]
        """

    def get_ai_decision(
        self,
        user_prompt: str,
        screen_info: dict | None,
        available_plugins: list[dict[str, str]] | None = None,
        detail_level: str = "low",
        history: str = "",
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

            image_data = screen_info.get("image_data", "") if isinstance(screen_info, dict) else ""
            image_width = screen_info.get("width", 0) if isinstance(screen_info, dict) else 0
            image_height = screen_info.get("height", 0) if isinstance(screen_info, dict) else 0

            if DEBUG_MODE:
                print("\n--- AI PROMPT KÜLDÉSE ---")
                print("SZÖVEGES PROMPT:")
                print(f"    Feladat: '{user_prompt}'")
                print(f"    Előzmények: {history if history else 'Nincs'}")
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
                                    f"Eredeti Feladat: '{user_prompt}'.\n{history}\n\n"
                                    f"A mellékelt kép mérete {image_width}x{image_height} pixel. "
                                    f"A pluginek: {plugins_text}. "
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

    def get_grid_calibration_points(self, screen_info: dict) -> list:
        print("🔬 Kalibrációs rács elemzése...")
        image_data = screen_info.get("image_data", "") if isinstance(screen_info, dict) else ""
        image_width = screen_info.get("width", 0) if isinstance(screen_info, dict) else 0
        image_height = screen_info.get("height", 0) if isinstance(screen_info, dict) else 0

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt_grid_calibration},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Feladat: Azonosítsd az összes feliratozott célpontot a képen.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                response_format={"type": "json_object"},
            )
            result_data = json.loads(response.choices[0].message.content)
            if isinstance(result_data, list):
                return result_data
            if isinstance(result_data, dict):
                for key in result_data:
                    value = result_data[key]
                    if isinstance(value, list):
                        return value
            return []
        except Exception as e:  # pragma: no cover - defensive logging
            print(f"Hiba a rács kalibráció során: {e}")
            return []
