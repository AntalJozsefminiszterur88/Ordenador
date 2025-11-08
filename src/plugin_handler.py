"""Dynamic plugin discovery and execution utilities."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, List

PLUGIN_PACKAGE = "src.plugins"


@dataclass
class PluginInfo:
    """Container describing a discovered plugin."""

    name: str
    function: Callable
    description: str


class PluginHandler:
    """Load and expose plugin functions located in ``src/plugins``."""

    def __init__(self) -> None:
        self.plugins: Dict[str, PluginInfo] = {}
        self._load_plugins()

    def _load_plugins(self) -> None:
        package = PLUGIN_PACKAGE
        package_path = Path(__file__).resolve().parent / "plugins"

        if not package_path.exists():
            return

        for module_info in pkgutil.iter_modules([str(package_path)]):
            if module_info.name.startswith("_"):
                continue

            module = self._import_module(f"{package}.{module_info.name}")
            if module is None:
                continue

            self._register_module_functions(module)

    def _import_module(self, module_name: str) -> ModuleType | None:
        try:
            return importlib.import_module(module_name)
        except Exception as exc:
            print(f"Nem sikerült importálni a plugint ({module_name}): {exc}")
            return None

    def _register_module_functions(self, module: ModuleType) -> None:
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ != module.__name__:
                continue

            description = inspect.getdoc(obj) or "Nincs leírás megadva."
            self.plugins[name] = PluginInfo(name=name, function=obj, description=description)

    def get_available_plugins(self) -> List[dict]:
        """Return a serialisable list of available plugin descriptions."""

        return [
            {"name": info.name, "description": info.description}
            for info in sorted(self.plugins.values(), key=lambda item: item.name)
        ]

    def execute_plugin(self, name: str, *args, **kwargs):
        """Execute the plugin function by name."""

        plugin = self.plugins.get(name)
        if not plugin:
            raise ValueError(f"Ismeretlen plugin: {name}")
        return plugin.function(*args, **kwargs)
