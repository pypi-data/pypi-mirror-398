
""" Custom logging classes and helper functions to support custom log levels and setup. """
import functools
import logging
import sys
from enum import IntEnum
from types import TracebackType
from typing import Any, cast

from rich.logging import RichHandler

from fluffless.utils.console import console


class LogLevels(IntEnum):
    """ List of permitted log level names, and their associated integer values. """

    # Default log levels Python's logging provides, defined for clarity.
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    # PRINT is used for informational statements that should always be shown to the user.
    # It is set to the highest level, such that it is never disabled.
    PRINT = 100


class CustomLogger(logging.Logger):
    """ Extension of standard logger class to introduce custom behaviour. """

    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        super().__init__(name, level)
        logging.addLevelName(LogLevels.PRINT, LogLevels.PRINT.name)

    def print(self, msg: object, *args, **kwargs) -> None:
        """ Log 'msg % args' with severity 'PRINT'.

        To pass exception information, use the keyword argument `exc_info` with a True value.

        Example usage:

            logger.print("Houston, we have %s", "no problem, hello!", exc_info=1)
        """
        if self.isEnabledFor(LogLevels.PRINT):
            self._log(LogLevels.PRINT, msg, args, **kwargs)


class CustomRichHandler(RichHandler):
    """ Custom Rich logging handler, allowing configuration per log level. """

    omit_print_level = True

    def emit(self, record: logging.LogRecord) -> None:
        """ Modify emit function to omit display level for `logger.print` calls, if no verbosity was requried.

        This results in print statements with levels attached when logger output is noisy with
        `info` and `debug` statements, but omitted when used without verbose logging enabled.
        """
        if self.omit_print_level:
            if record.levelno == LogLevels.PRINT:
                if self.level >= LogLevels.WARNING or self.level == logging.NOTSET:
                    self._log_render.show_level = False
            else:
                self._log_render.show_level = True

        super().emit(record)


def setup_logger(verbosity: int, modules: list[str] | None = None, omit_print_level: bool = False) -> None:
    """ Set up the root logger based on arguments to the main function.

    Args:
        verbosity (int): Verbosity level to display, highest is more verbose.
        modules (list[str] | None, optional): Additional root modules to set to the users custom log level. \
                                              Defaults to None, where no additional modules will be set.
        omit_print_level (bool, optional): Do not show the level of print statements when no verbosity was required. \
                                           Defaults to False.
    """
    # Set log levels based on verbosity specified by command line inputs.
    log_levels = sorted([level.value for level in LogLevels])
    cli_log_level = max(log_levels.index(LogLevels.WARNING) - verbosity, 0)

    # Log level is initial to the lowest level, then changed for each respective handler.
    for name in logging.root.manager.loggerDict:
        # Set initial log levels only for fluffless and additional modules provided,
        # avoiding clutter from 3rd party modules which use info and debug statements.
        for module in ("fluffless", *(modules or [])):
            if name.startswith(module):
                logging.getLogger(name).setLevel(log_levels[0])

    # Set up the console output handler using Rich for coloured display and detailed traceback.
    log_handler = CustomRichHandler(
        console=console,
        show_time=False,
        show_level=True,
        enable_link_path=False,
        omit_repeated_times=False,
        rich_tracebacks=True,
        level=log_levels[cli_log_level],
        markup=True,
    )
    log_handler.omit_print_level = omit_print_level
    logging.getLogger().addHandler(log_handler)

    def handle_exception(
        exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None,
    ) -> Any:
        """ Log uncaught exceptions using the log handler, using a custom exception hook. """
        logger = getLogger(__name__)

        # Keyboard interrupts are intentional user actions, and as such do not capture a full stack trace.
        if exc_type is KeyboardInterrupt:
            logger.print("Operation cancelled by user")
        else:
            logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


def getLogger(name: str | None = None) -> CustomLogger:  # noqa: N802 - Function name should be lowercase.
    """ Return the logger with the specified name, creating it if necessary. """
    return cast(CustomLogger, logging.getLogger(name))


# On import, set the default logger class to use the custom instance.
logging.setLoggerClass(CustomLogger)

# Overwrite the definition of print after initial class definition, to preserve docstrings and function signatures.
CustomLogger.print = functools.partialmethod(logging.Logger.log, LogLevels.PRINT)  # type: ignore[invalid-assignment]
