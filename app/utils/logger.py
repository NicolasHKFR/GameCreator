import logging
import os
from datetime import datetime

from app.utils.config import get_app_config, resolve_path


class ImmediateFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logger():
    config = get_app_config()
    log_dir = resolve_path(config.get('log_directory', 'logs'))
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f'application_{datetime.now().strftime("%Y%m%d")}.log')

    level = getattr(logging, config.get('log_level', 'INFO').upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        fh = ImmediateFileHandler(log_file, encoding='utf-8')
        fh.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        root.addHandler(fh)
        root.addHandler(ch)

    logger = logging.getLogger('game_asset_factory')
    return logger
