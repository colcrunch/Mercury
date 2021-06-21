import logging
from logging.handlers import RotatingFileHandler
from settings import log_level

parent_logger = logging.getLogger("discord")
parent_logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    filename="logs/mercury.log",
    encoding='utf-8',
    mode='a',
    maxBytes=1024000,
    backupCount=5
)
handler.setFormatter(
    logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
)
parent_logger.addHandler(handler)


def get_logger(name):
    """
    Takes the name of the file and generates a child logger of the discord logger to be used by the file to log
    events to the discord logger.

    The logging level is determined by the parent logger (the discord logger in this case).

    :param name: Should always be passed via __name__
    :return: a logger object.
    """

    logger = logging.getLogger('discord.' + name)
    logger.name = name
    logger.level = log_level

    return logger
