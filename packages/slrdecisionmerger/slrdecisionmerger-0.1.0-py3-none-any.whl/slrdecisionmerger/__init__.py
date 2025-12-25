import logging

logger = logging.getLogger("slrdecisionmerger")

# Create and add a handler if it doesn't exist
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
