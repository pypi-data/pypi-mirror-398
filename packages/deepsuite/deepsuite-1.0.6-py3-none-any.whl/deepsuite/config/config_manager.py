"""Config Manager module."""

import json
from pathlib import Path

from loguru import logger
import toml
import yaml


class ConfigManager:
    def __init__(self, config_dir="configs") -> None:
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True, parents=True)

    def save_yaml(self, config: dict, name: str) -> None:
        path = self.config_dir / f"{name}.yaml"
        with open(path, "w") as f:
            yaml.safe_dump(config, f)
        logger.success(f"✅ Config gespeichert als YAML: {path}")

    def save_json(self, config: dict, name: str) -> None:
        path = self.config_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(config, f, indent=4)
        logger.success(f"✅ Config gespeichert als JSON: {path}")

    def load_yaml(self, name: str) -> dict:
        path = self.config_dir / f"{name}.yaml"
        with open(path) as f:
            return yaml.safe_load(f)

    def load_json(self, name: str) -> dict:
        path = self.config_dir / f"{name}.json"
        with open(path) as f:
            return json.load(f)

    def save_toml(self, config: dict, name: str) -> None:
        path = self.config_dir / f"{name}.toml"
        with open(path, "w") as f:
            toml.dump(config, f)
        logger.success(f"✅ Config gespeichert als TOML: {path}")

    def load_toml(self, name: str) -> dict:
        path = self.config_dir / f"{name}.toml"
        with open(path) as f:
            return toml.load(f)

    def load_config(self, name: str, format: str = "yaml") -> dict:
        """Lädt eine Konfiguration aus einem bestimmten Format (yaml, json, toml).
        :param name: Name der Konfigurationsdatei ohne Erweiterung.
        :param format: Format der Konfigurationsdatei (yaml, json, toml).
        :return: Geladene Konfiguration als Dictionary.
        """
        match format.lower():
            case "yaml":
                return self.load_yaml(name)
            case "json":
                return self.load_json(name)
            case "toml":
                return self.load_toml(name)
            case _:
                raise ValueError(f"Unbekanntes Format: {format}")
