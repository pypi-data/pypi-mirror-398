import logging

import structlog

NOTSET = logging.NOTSET
CRITICAL = logging.CRITICAL
DEBUG = logging.DEBUG
ERROR = logging.ERROR
INFO = logging.INFO
WARNING = logging.WARNING


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""

    return structlog.getLogger(name)


def set_level(level: int | str):
    """Set the global log level."""

    if isinstance(level, int) or level in logging._nameToLevel:
        logging.getLogger().setLevel(level)
    else:
        logging.getLogger(__name__).warning("Ignoring invalid log level '%s'", level)


def configure_logging(level: str | int | None = None, json_format: bool = False):
    """Configure and initialize the logging system."""
    # Stop the uvicorn logger from propagating to avoid duplicate logging.
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.propagate = False

    log_level = (
        getattr(logging, level.upper(), INFO) if isinstance(level, str) else level
    )

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_format:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level or INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
