import argparse
import sys
from pathlib import Path

# Garante que o Python encontre o pacote em /src
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zendesk_ticket_exporter.app import run


def parse_args():
    p = argparse.ArgumentParser(
        description="Exportador de tickets do Zendesk em PDF com checkpoint e inventário."
    )
    p.add_argument(
        "--config",
        required=True,
        help="Caminho do arquivo config.json (baseado em config.example.json).",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(config_path=args.config)

