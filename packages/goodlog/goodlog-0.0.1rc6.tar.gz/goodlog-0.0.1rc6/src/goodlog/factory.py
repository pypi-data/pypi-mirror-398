import logging


def create_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
