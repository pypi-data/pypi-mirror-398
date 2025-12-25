import logging

def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Возвращает настроенный логгер с потоковым выводом и форматированием.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger