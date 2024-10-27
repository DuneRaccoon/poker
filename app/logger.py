import sys
from loguru import logger

def setup_logging():
    logger.remove()
    logger.add(sys.stderr, format="{time} {level} {message}")
    logger.level("INFO")

setup_logging()