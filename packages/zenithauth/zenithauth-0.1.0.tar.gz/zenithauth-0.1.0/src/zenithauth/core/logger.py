import logging
import sys

# Define a library-specific logger
logger = logging.getLogger("zenithauth")

def setup_logger(level: int = logging.INFO):
    """
    Configures the library logger. 
    By default, we follow the 'Library Logging' best practice:
    We add a NullHandler so we don't force logs on the user 
    unless they want them.
    """
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

# Initially add NullHandler as per Python library standards
logger.addHandler(logging.NullHandler())