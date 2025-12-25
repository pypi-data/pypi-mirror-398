##########################################################################################
# Copyright (c) 2024 Nordic Semiconductor
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
##########################################################################################

import copy
import os
import sys
import termcolor
import logging
import inspect

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
LOG_FILENAME = os.getenv("LOG_FILENAME", "att_test_log")
LOG_PREFIX = os.getenv("LOG_PREFIX")
LOG_PREFIX_COLOR = os.getenv("LOG_PREFIX_COLOR")

LOG_DIR = "outcomes/logs"


def get_logger(log_level=LOG_LEVEL) -> logging.Logger:
    caller = inspect.stack()[1]
    filename = caller.filename

    # Global Logging Function
    logger = logging.getLogger(filename)
    formatter = None

    if not logger.handlers:
        # Prevent logging from propagating to the root logger
        logger.propagate = 0
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(log_level)
        logger.addHandler(console)

        formatter = "%(asctime)s:%(module)s:%(levelname)s:%(message)s"

        formatter = ColoredFormatter(formatter, datefmt="%H:%M:%S")
        console.setFormatter(formatter)

    if LOG_FILENAME:
        os.makedirs(LOG_DIR, exist_ok=True)
        for level in ["debug"]:
            file_handler = logging.FileHandler(f"{LOG_DIR}/{LOG_FILENAME}_{level}.txt")
            file_handler.setLevel(level.upper())
            logger.addHandler(file_handler)
            formatter = "%(asctime)s:%(module)s:%(levelname)s:%(message)s"
            file_handler.setFormatter(
                logging.Formatter(formatter, datefmt="%Y-%m-%d %H:%M:%S")
            )

    logger.setLevel(logging.DEBUG)

    return logger


class ColoredFormatter(logging.Formatter):
    """Format log levels with color"""

    MAPPING = {
        "DEBUG": dict(color="cyan", on_color=None),
        "INFO": dict(color="green", on_color=None),
        "WARNING": dict(color="yellow", on_color=None),
        "ERROR": dict(color="grey", on_color="on_red"),
        "CRITICAL": dict(color="grey", on_color="on_blue"),
    }

    def format(self, record):
        """Add log ansi colors"""
        crecord = copy.copy(record)
        seq = self.MAPPING.get(crecord.levelname, self.MAPPING["INFO"])
        crecord.levelname = termcolor.colored(crecord.levelname, **seq)
        if LOG_PREFIX:
            crecord.msg = (
                f"\033[43;1m\033[{LOG_PREFIX_COLOR}m{LOG_PREFIX}\033[0m"
                + str(crecord.msg)
            )
        return super().format(crecord)


class LogFilter(object):
    """
    Filters logging levels which will exclude every logs that are
    not on the same level

    Parameters
    -------

    level: str
        sets the only type of log level to output
        ex: 'INFO' will only show info level logs
    """

    def __init__(self, level) -> None:
        self.__level = getattr(logging, level.upper())

    def filter(self, logRecord) -> bool:
        return logRecord.levelno <= self.__level
