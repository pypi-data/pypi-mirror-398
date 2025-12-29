import logging
class Config:
    VERBOSE = False
    DRYRUN = False

# Setup a module-level logger using the standard logging library
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    # Add handler if not present (avoid duplicate handlers)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG if getattr(Config, "VERBOSE", False) else logging.INFO)