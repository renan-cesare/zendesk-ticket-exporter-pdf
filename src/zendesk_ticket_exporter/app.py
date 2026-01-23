import logging

from .config import Config
from .logging_config import setup_logging
from .exporter import ExporterConfig, export_all

logger = logging.getLogger("zendesk_ticket_exporter")


def run(config_path: str):
    cfg = Config.load(config_path)
    setup_logging(cfg.log_level)

    logger.info("Iniciando exportador de tickets do Zendesk (PDF)")

    exporter_cfg = ExporterConfig(
        subdomain=cfg.subdomain,
        excel_codigos=cfg.excel_codigos,
        output_dir=cfg.output_dir,
        chrome_driver_path=cfg.chrome_driver_path,
        headless=cfg.headless,
        keep_browser_open=cfg.keep_browser_open,
        reset_checkpoint=cfg.reset_checkpoint,
        between_tickets_min_s=cfg.between_tickets_min_s,
        between_tickets_max_s=cfg.between_tickets_max_s,
        after_print_min_s=cfg.after_print_min_s,
        after_print_max_s=cfg.after_print_max_s,
        max_pages=cfg.max_pages,
        retry_create_driver=cfg.retry_create_driver,
        max_tickets_per_assessor=cfg.max_tickets_per_assessor,
    )

    export_all(exporter_cfg, cfg.auth_dict)
