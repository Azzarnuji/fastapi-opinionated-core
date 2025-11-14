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

_last_log_time = time.time()


# ======================================================
#  Custom Logger (tambah delta)
# ======================================================
class CustomLogger(logging.getLoggerClass()):
    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1
    ):
        global _last_log_time
        now = time.time()
        delta_ms = (now - _last_log_time) * 1000
        _last_log_time = now

        extra = extra or {}
        if "delta" not in extra:
            extra["delta"] = round(delta_ms, 3)

        super()._log(
            level,
            msg,
            args,
            exc_info,
            extra,
            stack_info,
            stacklevel + 1
        )


# ======================================================
#  Custom Formatter (namespace fallback)
# ======================================================
class CustomFormatter(logging.Formatter):
    def format(self, record):
        pid = os.getpid()
        now = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")

        # --- namespace support ---
        namespace = getattr(record, "ns", None)
        if not namespace:
            namespace = f"{record.filename}:{record.lineno}"

        log_color = COLORS.get(record.levelname, RESET)

        return (
            f"\033[37m[{pid}]{RESET} - "
            f"\033[37m{now}{RESET}  "
            f"{log_color}{record.levelname}{RESET} "
            f"\033[32m[{namespace}]{RESET} "
            f"{log_color}{record.getMessage()}{RESET}"
        )


# ======================================================
#  Setup Logging
# ======================================================
def setup_logging():
    logging.setLoggerClass(CustomLogger)

    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers = [handler]

    # Override default loggers
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


# ======================================================
#  Helper untuk namespace logger
# ======================================================
def ns_logger(namespace: str):
    """
    ns_logger("SocketPlugin").info("Hello")
    -> INFO [SocketPlugin] Hello
    """

    class NSProxy:
        def info(self, msg, *a, **k):
            return logger.info(msg, *a, extra={"ns": namespace}, **k)

        def warning(self, msg, *a, **k):
            return logger.warning(msg, *a, extra={"ns": namespace}, **k)

        def error(self, msg, *a, **k):
            return logger.error(msg, *a, extra={"ns": namespace}, **k)

        def debug(self, msg, *a, **k):
            return logger.debug(msg, *a, extra={"ns": namespace}, **k)

    return NSProxy()
