import logging
import os
import time
from datetime import datetime

RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[37m",
    "INFO": "\033[36m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[41m",
}

# global last log time
_last_log_time = time.time()

class CustomLogger(logging.getLoggerClass()):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
        global _last_log_time
        now = time.time()
        delta_ms = (now - _last_log_time) * 1000
        _last_log_time = now

        if extra is None:
            extra = {}
        if "delta" not in extra:
            extra["delta"] = round(delta_ms, 3)

        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel + 1)


class CustomFormatter(logging.Formatter):
    def format(self, record):
        pid = os.getpid()
        now = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
        filename_line = f"{record.filename}:{record.lineno}"
        log_color = COLORS.get(record.levelname, RESET)

        return (
            f"\033[37m[{pid}]{RESET} - "
            f"\033[37m{now}{RESET}  "
            f"{log_color}{record.levelname}{RESET} "
            f"\033[32m[{filename_line}]{RESET} "
            f"{log_color}{record.getMessage()}{RESET}"
        )


def setup_logging():
    logging.setLoggerClass(CustomLogger)
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

    # Override uvicorn loggers supaya warna + delta
    for name, level in {
        "uvicorn": logging.INFO,
        "uvicorn.access": logging.INFO,
        "uvicorn.error": logging.ERROR,
        "uvicorn.warning": logging.WARNING,
        "arq.worker": logging.INFO,
        "arq.connections": logging.INFO,
    }.items():
        log = logging.getLogger(name)
        log.setLevel(level)
        log.handlers = [handler]
        log.propagate = False

    return logging.getLogger("App")


logger = setup_logging()
