import logging
import os
import sys as system


def get_logger(name="multimodal_agent") -> logging.Logger:
    """
    Create or retrieve a module-level logger with a sane configuration.
    This avoids duplicate handlers and ensures consistent format.
    """
    logger = logging.getLogger(name)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    level = os.getenv("LOGLEVEL", "INFO").upper()

    logger.setLevel(level)

    handler = logging.StreamHandler(system.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False

    return logger
