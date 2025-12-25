import logging


def setup_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s.%(msecs)03d] %(levelname)s:\t%(name)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S",
    )
    return logger
