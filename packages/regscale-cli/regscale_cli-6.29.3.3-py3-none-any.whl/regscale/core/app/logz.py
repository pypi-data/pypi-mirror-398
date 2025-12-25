#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rich Logging"""

# standard python imports
import logging
import os
import sys
import tempfile
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Optional

import click
from rich.logging import RichHandler
from rich.traceback import install
from rich.console import Console

from regscale import exceptions

if not os.getenv("REGSCALE_DEBUG", False):
    install(suppress=[click, exceptions])


class AirflowStreamHandler(logging.Handler):
    """
    Custom Handler for Airflow that writes all logs to stderr.

    Airflow only captures stderr (not stdout), so all logs must go to stderr to be visible.
    Airflow adds its own timestamp prefix, so we don't include a timestamp in our format.
    The log level is preserved in the formatted message (via [%(levelname)s]),
    which helps identify the actual log level even though Airflow may display them in the error section.
    """

    terminator = "\n"  # Line terminator for log records

    def __init__(self):
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to stderr (where Airflow captures logs).

        Since Airflow only captures stderr, all logs go there.
        The formatted message includes [INFO], [DEBUG], [WARNING], [ERROR], etc.
        so the log level is preserved even though Airflow may display them in the error section.

        :param logging.LogRecord record: The log record to emit
        """
        try:
            msg = self.format(record)
            formatted_msg = msg + self.terminator

            # Write all logs to stderr since Airflow only captures stderr
            # The log level is preserved in the formatted message format
            sys.stderr.write(formatted_msg)
            sys.stderr.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            # Log the error but don't let it propagate to avoid infinite loops
            # Use handleError which will write to stderr if possible
            self.handleError(record)


def create_logger(propagate: Optional[bool] = None, custom_handler: Optional[Any] = None) -> logging.Logger:
    """
    Create a logger for use in all cases

    :param Optional[bool] propagate: Whether to propagate the logger, defaults to None
    :param Optional[Any] custom_handler: Custom handler to add to the logger, defaults to None
    :return: logger object
    :rtype: logging.Logger
    """
    loglevel = os.environ.get("LOGLEVEL", "INFO").upper()
    # Convert string log level to logging constant
    numeric_level = getattr(logging, loglevel, logging.INFO)

    # Check if running in Airflow - use simple StreamHandler instead of RichHandler
    running_in_airflow = os.getenv("REGSCALE_AIRFLOW") == "true"

    if running_in_airflow:
        # Use custom AirflowStreamHandler that writes all logs to stderr
        # Airflow captures stderr and adds its own timestamp prefix, so we don't include timestamp
        # Disable propagation to avoid duplicates with Airflow's handlers
        stream_handler = AirflowStreamHandler()
        stream_handler.setLevel(numeric_level)
        # Format includes levelname but no timestamp (Airflow adds its own timestamp prefix)
        formatter = logging.Formatter("[%(levelname)s] %(name)s - %(message)s")
        stream_handler.setFormatter(formatter)
        handlers: list[logging.Handler] = [stream_handler]
    else:
        # Use RichHandler for normal CLI usage
        try:
            width = int(os.environ.get("REGSCALE_LOG_WIDTH"))  # Default to 160 if not set
            rich_handler = RichHandler(
                rich_tracebacks=False, markup=True, show_time=False, console=Console(width=width)
            )
        except (TypeError, ValueError):
            # If the value is not an integer, set it to None (goes to default to use the full width of the terminal)
            # Without this except block, the logs do NOT print
            rich_handler = RichHandler(rich_tracebacks=False, markup=True, show_time=False)

        rich_handler.setLevel(numeric_level)
        handlers: list[logging.Handler] = [rich_handler]

        # Only create file handler if not in container
        if os.getenv("REGSCALE_ECS", False) != "True":
            file_handler = TimedRotatingFileHandler(
                filename=f"{tempfile.gettempdir()}{os.sep}RegScale.log",
                when="D",
                interval=3,
                backupCount=10,
            )
            file_handler.setLevel(numeric_level)
            handlers.append(file_handler)

    if custom_handler:
        handlers.append(custom_handler)

    logging.getLogger("botocore").setLevel(logging.CRITICAL)

    # In Airflow mode, configure logger with our custom handler
    if running_in_airflow:
        logger = logging.getLogger("regscale")
        # Remove any existing handlers of the same type to avoid duplicates
        logger.handlers = [h for h in logger.handlers if not isinstance(h, AirflowStreamHandler)]
        # Add our custom handler
        for handler in handlers:
            logger.addHandler(handler)
        logger.setLevel(numeric_level)
        # Disable propagation to avoid duplicates - our handler writes to stderr which Airflow captures
        logger.propagate = False
    else:
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
            datefmt="[%Y/%m/%d %H:%M;%S]",
            handlers=handlers,
            force=os.getenv("REGSCALE_ECS", False) == "True",
        )
        logger = logging.getLogger("regscale")
        logger.handlers = handlers
        logger.setLevel(numeric_level)
        logger.parent.handlers = []
        if propagate is not None:
            logger.propagate = propagate

    return logger
