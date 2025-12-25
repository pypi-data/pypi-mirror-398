import logging
import os
import sys
from logging import StreamHandler, Formatter, Logger
from logging.handlers import TimedRotatingFileHandler

try:
    # colorama supports Windows coloring
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    _HAS_COLORAMA = True
except ImportError:
    _HAS_COLORAMA = False
    Fore = Style = None


class ColoredFormatter(Formatter):
    """
    Logging Formatter that adds color codes to log levels when printing to console.
    """
    LEVEL_COLORS = {
        logging.DEBUG:     (Fore.BLUE,    Style.BRIGHT),
        logging.INFO:      (Fore.GREEN,   None),
        logging.WARNING:   (Fore.YELLOW,  None),
        logging.ERROR:     (Fore.RED,     Style.BRIGHT),
        logging.CRITICAL:  (Fore.RED,     Style.BRIGHT),
    }

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if _HAS_COLORAMA:
            color, style = self.LEVEL_COLORS.get(record.levelno, (None, None))
            prefix = ''
            suffix = Style.RESET_ALL
            if style:
                prefix += style
            if color:
                prefix += color
            return f"{prefix}{message}{suffix}"
        return message


def setup_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.DEBUG,
    max_file_count: int = 7,
    when: str = 'midnight'
) -> Logger:
    """
    Configure and return a logger:
      - Console handler with colored output (if colorama installed)
      - Timed rotating file handler (daily rotation, keep max_file_count backups)

    :param name: Name for the logger and log file ("{name}.log").
    :param log_dir: Directory to store log files.
    :param level: Logging level.
    :param max_file_count: How many days of logs to keep.
    :param when: Rotation interval (see TimedRotatingFileHandler docs).
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    fmt = "%Y-%m-%d %H:%M:%S"
    datefmt = "%Y-%m-%d %H:%M:%S"
    pattern = f"%(levelname)-8s %(asctime)s %(name)s %(filename)s:%(lineno)d %(message)s"

    # Console handler
    stream = StreamHandler(sys.stdout)
    stream.setLevel(level)
    stream_fmt = ColoredFormatter(pattern, datefmt=datefmt)
    stream.setFormatter(stream_fmt)
    logger.addHandler(stream)

    # Timed rotating file handler
    logfile = os.path.join(log_dir, f"{name}.log")
    file_handler = TimedRotatingFileHandler(
        logfile,
        when=when,
        interval=1,
        backupCount=max_file_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_fmt = Formatter(pattern, datefmt=datefmt)
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger


def deactivate_logger(logger: Logger) -> None:
    """
    Remove all handlers and reset logger level to NOTSET.
    """
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.NOTSET)
