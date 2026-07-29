# [Ngày 1] Cấu hình logging cho ứng dụng

import logging
import sys


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("taskhub")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
