# [Ngày 1] Cấu hình logging cho ứng dụng
# [Ngày 7] nâng cấp: cấu hình logging chuẩn, level và format theo settings.ENV

import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("taskhub")
    
    # Lấy level theo settings.ENV
    env = settings.ENV.lower() if hasattr(settings, "ENV") else "development"
    log_level = logging.DEBUG if env in ("dev", "development") else logging.INFO
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()

