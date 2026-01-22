import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    input_codes_file: Path
    output_dir: Path
    base_url: str
    headless: bool
    reset_checkpoint: bool
    cooldown_seconds: int
    log_level: str

    @classmethod
    def load(cls, path: str) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            input_codes_file=Path(data["paths"]["input_codes_file"]),
            output_dir=Path(data["paths"]["output_dir"]),
            base_url=data["zendesk"]["base_url"],
            headless=data["zendesk"].get("headless", False),
            reset_checkpoint=data["processing"].get("reset_checkpoint", False),
            cooldown_seconds=int(data["processing"].get("cooldown_seconds", 2)),
            log_level=data["logging"].get("level", "INFO"),
        )
