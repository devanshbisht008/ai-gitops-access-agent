"""File handling utilities for JSON, YAML, and text operations."""

import json
import os
from typing import Any, Dict
import yaml

def read_json_file(file_path: str) -> Dict[str, Any]:
    """Reads and parses a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_text_file(file_path: str) -> str:
    """Reads content from a text file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Text file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Loads and parses a YAML configuration file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data is not None else {}

def save_yaml_file(file_path: str, data: Dict[str, Any]) -> None:
    """Saves dictionary data to a YAML file preserving formatting."""
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
