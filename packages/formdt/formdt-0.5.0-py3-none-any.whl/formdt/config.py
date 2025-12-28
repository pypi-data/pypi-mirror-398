from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Config:
    line_length: int = 80


def load_config(path: Path | None = None) -> Config:
    if path is None:
        path = Path.cwd() / ".formdt"

    if not path.exists():
        return Config()

    with open(path) as f:
        data = json.load(f)

    return Config(line_length=data.get("line_length", 80))
