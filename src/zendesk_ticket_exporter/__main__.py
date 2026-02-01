import argparse
from .app import run


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


def main():
    args = parse_args()
    run(config_path=args.config)


if __name__ == "__main__":
    main()
