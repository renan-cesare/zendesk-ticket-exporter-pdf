import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    # zendesk
    subdomain: str

    # auth (preferir ENV)
    auth_dict: dict

    # paths
    excel_codigos: Path
    output_dir: Path
    chrome_driver_path: Path

    # runtime
    headless: bool
    keep_browser_open: bool
    reset_checkpoint: bool

    # throttle
    between_tickets_min_s: float
    between_tickets_max_s: float
    after_print_min_s: float
    after_print_max_s: float

    # limits
    max_pages: int
    retry_create_driver: int
    max_tickets_per_assessor: int | None

    # logging
    log_level: str

    @classmethod
    def load(cls, path: str) -> "Config":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))

        subdomain = data["zendesk"]["subdomain"].strip()

        auth = data.get("auth", {})
        paths = data["paths"]
        runtime = data.get("runtime", {})
        throttle = data.get("throttle", {})
        limits = data.get("limits", {})
        logging = data.get("logging", {"level": "INFO"})

        max_tickets = limits.get("max_tickets_per_assessor", None)
        if max_tickets is not None:
            try:
                max_tickets = int(max_tickets)
            except Exception:
                max_tickets = None

        return cls(
            subdomain=subdomain,
            auth_dict=auth,
            excel_codigos=Path(paths["excel_codigos"]),
            output_dir=Path(paths["output_dir"]),
            chrome_driver_path=Path(paths["chrome_driver_path"]),
            headless=bool(runtime.get("headless", False)),
            keep_browser_open=bool(runtime.get("keep_browser_open", True)),
            reset_checkpoint=bool(runtime.get("reset_checkpoint", False)),
            between_tickets_min_s=float(throttle.get("between_tickets_min_s", 1.0)),
            between_tickets_max_s=float(throttle.get("between_tickets_max_s", 2.0)),
            after_print_min_s=float(throttle.get("after_print_min_s", 0.6)),
            after_print_max_s=float(throttle.get("after_print_max_s", 1.0)),
            max_pages=int(limits.get("max_pages", 5000)),
            retry_create_driver=int(limits.get("retry_create_driver", 2)),
            max_tickets_per_assessor=max_tickets,
            log_level=str(logging.get("level", "INFO")).upper(),
        )
