import logging
import logging.config

_TRACE_INSTALLED = False
_DEFAULT_CONFIG = {
    "version": 1,
    "formatters": {
        "brief": {
            "format": ("%(asctime)s [%(name)s][%(levelname)s] %(message)s")
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "ERROR",
        "handlers": ["console"],
    },
    "loggers": {
        "mima": {"level": "TRACE"},
    },
}


def install_trace_logger():
    global _TRACE_INSTALLED
    if _TRACE_INSTALLED:
        return
    level = logging.TRACE = logging.DEBUG - 5

    def log_logger(self, message, *args, **kwargs):
        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    logging.getLoggerClass().trace = log_logger

    def log_root(msg, *args, **kwargs):
        logging.log(level, msg, *args, **kwargs)

    logging.addLevelName(level, "TRACE")
    logging.trace = log_root
    _TRACE_INSTALLED = True


def configure_logging(config=_DEFAULT_CONFIG):
    logging.config.dictConfig(config)
