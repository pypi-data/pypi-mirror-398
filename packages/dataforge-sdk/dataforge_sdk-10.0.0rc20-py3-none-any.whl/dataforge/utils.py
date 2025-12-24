import logging

def _setup_logger(name: str = "SDK"):
    """Set up and return a configured logger for the SDK.

    Returns:
        logging.Logger: Configured logger for SDK outputs.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Create handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter with timestamp
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    console_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        # Add handler to the logger
        logger.addHandler(console_handler)

    return logger