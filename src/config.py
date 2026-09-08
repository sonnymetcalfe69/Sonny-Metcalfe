"""Loads config/settings.yaml and config/businesses.yaml, with a clear
error pointing at the .example.yaml if the real file hasn't been created yet."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        example = CONFIG_DIR / f"{path.stem}.example.yaml"
        sys.exit(f"Missing {path}. Copy {example} to {path} and edit it first.")
    return yaml.safe_load(path.read_text()) or {}


def load_settings() -> dict[str, Any]:
    return load_yaml("settings.yaml")


def load_businesses() -> list[dict[str, Any]]:
    return load_yaml("businesses.yaml").get("businesses", [])
