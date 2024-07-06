import logging


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter that includes the filename
    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(filename)s:%(lineno)d:: %(message)s')

    # Set the formatter for the console handler
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()