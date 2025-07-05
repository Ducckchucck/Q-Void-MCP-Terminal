import logging

def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Creates and returns a logger with standardized format.

    Args:
        name (str): Name of the logger.
        level (str): Logging level - "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.propagate = False

    return logger


if __name__ == "__main__":
    log = get_logger("LoggerExample", level="DEBUG")
    log.debug("Debugging info for development")
    log.info("Logger is working!")
    log.warning("This is a warning message")
    log.error("Oops! Something went wrong")
    log.critical("Critical error encountered!")
