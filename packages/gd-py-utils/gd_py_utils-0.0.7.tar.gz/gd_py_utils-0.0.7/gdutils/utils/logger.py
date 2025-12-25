import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Union

# Define types for clearer signatures
LogHandler = logging.Handler


class SimpleFormatter(logging.Formatter):
    colors = {
        "reset": "\x1b[0m",
        logging.DEBUG: "\x1b[;1m",
        logging.INFO: "\x1b[32m",
        logging.WARNING: "\x1b[33m",
        logging.ERROR: "\x1b[31m",
        logging.CRITICAL: "\x1b[31;1m",
    }
    fonts = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARN",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRIT",
    }

    def __init__(self, origin: bool = True):
        fmt = self.set_fmt_(origin)
        super().__init__(fmt, style="{")

    @staticmethod
    def set_fmt_(origin: bool) -> str:
        s = "{color}[{levelname}]{reset}{space}"
        if origin:
            s += "[\x1b[;3m{name}{funcName}\x1b[0m] "
        s += "{message}"
        return s

    def get_update(self, record: logging.LogRecord) -> dict:
        func_name = ""
        if record.funcName != "<module>":
            func_name = f" ({record.funcName})"

        levelname = self.fonts.get(record.levelno, record.levelname)

        return {
            "funcName": func_name,
            "levelname": levelname,
            "color": self.colors.get(record.levelno, self.colors["reset"]),
            "space": " " * max(0, 6 - len(levelname)),
            "reset": self.colors["reset"],
        }

    def format(self, record: logging.LogRecord) -> str:
        # Create a copy to avoid side effects on other handlers
        # We explicitly copy only what we need or make a shallow copy
        record_copy = logging.makeLogRecord(record.__dict__)
        record_copy.__dict__.update(self.get_update(record_copy))
        return super().format(record_copy)


class HtmlFormatter(logging.Formatter):
    reset = "</font>"
    base_fmt = "{col}[%(levelname)s]{reset} [{origin}] %(message)s<br>"
    origin_fmt = "%(name)s (%(funcName)s)"

    FORMATS = {
        logging.DEBUG: '<font color="Grey">',
        logging.INFO: '<b><font color="Green">',
        logging.WARNING: '<font color="Orange">',
        logging.ERROR: '<font color="Red">',
        logging.CRITICAL: '<b><font color="Red">',
    }

    def __init__(self):
        super().__init__()
        self._formatters = {}
        for level, col in self.FORMATS.items():
            reset_tag = f"{self.reset}</b>" if "<b>" in col else self.reset
            log_fmt = self.base_fmt.format(
                col=col,
                reset=reset_tag,
                origin=self.origin_fmt,
            )
            self._formatters[level] = logging.Formatter(log_fmt)
        # Default formatter for unknown levels
        self._default_formatter = logging.Formatter(
            self.base_fmt.format(col="", reset=self.reset, origin=self.origin_fmt)
        )

    def format(self, record: logging.LogRecord) -> str:
        formatter = self._formatters.get(record.levelno, self._default_formatter)
        return formatter.format(record).replace("\n", "<br>")


class CSVFormatter(logging.Formatter):
    def __init__(self, formats: List[str] = None, sep: str = ", ", **kw):
        super().__init__(**kw)

        if formats is None:
            formats = ["asctime", "levelname", "funcName", "message"]

        fmt_list = [f"%({x})s" for x in formats]
        self.fmt = sep.join(fmt_list)
        self._formatter = logging.Formatter(self.fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        return self._formatter.format(record)


def get_logger(
    remove_handlers: bool = True,
    default: bool = True,
    handlers: Optional[List[logging.Handler]] = None,
    origin: bool = True,
    logfile: Optional[str] = None,
) -> logging.Logger:
    """
    Format the root logger to remove default handlers and add a default `StreamHandler` with custom formatter `SimpleFormatter`.

    Usage example, place this in your main module

    .. code:: python

        logging.basicConfig(level=logging.INFO)
        log = gd.get_logger()

    """
    logger = logging.getLogger()
    # Removed side effect: logging.getLogger("matplotlib").setLevel(logging.ERROR)

    if remove_handlers:
        for hdlr in list(logger.handlers):
            logger.removeHandler(hdlr)

    if default:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(SimpleFormatter(origin))
        logger.addHandler(console_handler)

    if handlers is not None:
        for x in handlers:
            logger.addHandler(x)

    if logfile:
        if str(logfile).endswith(".py"):
            logfile = logfile[:-3] + ".log"
        # 1MB max, 5 backups
        x = RotatingFileHandler(logfile, maxBytes=int(1e6), backupCount=5)
        x.setFormatter(CSVFormatter())
        logger.addHandler(x)

    return logger


def get_csv_logger(remove_handlers: bool = True, logfile: Optional[str] = None, **kw) -> logging.Logger:
    """
    Calls a treefile logger formatted for files output, no colors but timestamps

    .. code:: python

        logging.basicConfig(level=logging.INFO)
        log = get_csv_logger()

    """
    return get_logger(
        remove_handlers=remove_handlers,
        default=False,
        handlers=[stream_csv_handler(**kw)],
        logfile=logfile,
    )


def stream_csv_handler(**kwargs) -> logging.StreamHandler:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(CSVFormatter(**kwargs))
    return h


if __name__ == "__main__":

    def my_func():
        logging.basicConfig(level=logging.INFO)
        log = get_logger(default=False, handlers=[stream_csv_handler()])

        log.debug("This is a debug message")
        log.info("This is an info message")
        log.warning("This is a warning message")
        log.error("This is an error message")
        log.critical("This is a critical message")

    my_func()
