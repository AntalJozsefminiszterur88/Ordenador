"""Memory handler for storing GUI element coordinates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json


class MemoryHandler:
    """Persist and retrieve GUI element coordinates for faster access."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self._storage_path = Path(storage_path) if storage_path else base_dir / "gui_elements.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_memory(self) -> Dict[str, Dict[str, int]]:
        if not self._storage_path.exists():
            return {}
        try:
            with self._storage_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}
        if not isinstance(data, dict):
            return {}

        valid_data: Dict[str, Dict[str, int]] = {}
        for name, coords in data.items():
            if (
                isinstance(name, str)
                and isinstance(coords, dict)
                and "x" in coords
                and "y" in coords
                and isinstance(coords["x"], (int, float))
                and isinstance(coords["y"], (int, float))
            ):
                valid_data[name] = {"x": int(coords["x"]), "y": int(coords["y"])}
        return valid_data

    def _save_memory(self, data: Dict[str, Dict[str, int]]) -> None:
        try:
            with self._storage_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def save_element_location(self, name: str, coords: Dict[str, Any]) -> None:
        if not isinstance(name, str):
            return
        if not isinstance(coords, dict):
            return
        if "x" not in coords or "y" not in coords:
            return

        x, y = coords["x"], coords["y"]
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return

        memory = self._load_memory()
        memory[name] = {"x": int(x), "y": int(y)}
        self._save_memory(memory)

    def get_element_location(self, name: str) -> Optional[Dict[str, int]]:
        if not isinstance(name, str):
            return None
        memory = self._load_memory()
        return memory.get(name)
