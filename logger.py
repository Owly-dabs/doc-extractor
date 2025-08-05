import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

# Console handler with formatter
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)