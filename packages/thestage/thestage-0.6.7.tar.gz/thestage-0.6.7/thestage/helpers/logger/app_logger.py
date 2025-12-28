import logging
import platform
from logging.handlers import RotatingFileHandler
from pathlib import Path
from thestage import __app_name__, __version__

from thestage.config import THESTAGE_CONFIG_DIR

from thestage.config import THESTAGE_LOGGING_FILE
from thestage.exceptions.file_system_exception import FileSystemException


def get_log_path_from_os() -> Path:
    system = platform.system()
    if system == 'Linux':
        path = Path.home().joinpath(THESTAGE_CONFIG_DIR).joinpath('logs')
    elif system == 'Windows':
        path = Path.home().joinpath(THESTAGE_CONFIG_DIR).joinpath('logs')
    elif system == 'Darwin':
        path = Path.home().joinpath('library').joinpath('logs').joinpath('thestage')
    else:
        path = Path.home().joinpath(THESTAGE_CONFIG_DIR).joinpath('logs')

    if not path.exists():
        try:
            path.mkdir(exist_ok=True, parents=True)
        except OSError:
            raise FileSystemException("Error create log dir")

    return path


def build_logger(level) -> logging.Logger:
    logger = logging.getLogger(f"{__app_name__} v{__version__}")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(level)

    log_path = get_log_path_from_os()
    tsr_log_file = log_path.joinpath(THESTAGE_LOGGING_FILE)

    if tsr_log_file:
        file_h = RotatingFileHandler(filename=tsr_log_file, maxBytes=1024 * 10, backupCount=5)
        file_h.setLevel(level)
        file_h.setFormatter(formatter)
        logger.addHandler(file_h)

    return logger


app_logger = build_logger(level=logging.DEBUG)
