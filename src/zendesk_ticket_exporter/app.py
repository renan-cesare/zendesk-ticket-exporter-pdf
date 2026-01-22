import logging
from pathlib import Path

from .config import Config
from .logging_config import setup_logging

logger = logging.getLogger("zendesk_ticket_exporter")


def run(config_path: str):
    cfg = Config.load(config_path)
    setup_logging(cfg.log_level)

    logger.info("Iniciando exportador de tickets do Zendesk")
    logger.info(f"Config: {Path(config_path).resolve()}")
    logger.info(f"Output dir: {cfg.output_dir}")

    # Aqui depois vamos ligar:
    # - cliente zendesk
    # - coletor de tickets
    # - exportador de PDF
    # - checkpoint
    # - inventário

    logger.info("Pipeline ainda não conectado (estrutura base criada).")
