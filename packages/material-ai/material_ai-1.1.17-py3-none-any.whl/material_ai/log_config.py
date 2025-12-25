from pythonjsonlogger import json as jsonlogger
from datetime import datetime
import logging
import sys
from typing import Optional


def setup_structured_logging(
    app_name: str | None = None,
    enable_json_formatter: bool = False,
    log_level: int = logging.INFO,
) -> None:
    """
    Configures logging for the application to support structured and traditional log outputs.

    Handles setup for logging and provides optional JSON formatting for
    logs. Targets logs to `stdout` and integrates optional app-name-based filtering. Suitable for
    environments like GKE or Cloud Run if structured logging is required. Ensures compatibility
    with otel logs collector if enabled.

    Args:
        app_name: The name of the application used for filtering logs. Defaults to None.
        enable_json_formatter: Configures logging with JSON formatting for structured logs.
                               Recommended for cloud environments. Defaults to False.
        log_level: Sets the logging verbosity level. Compatible with `logging` level constants.
                   Defaults to `logging.INFO`.

    Returns:
        None
    """
    app_name_filter = AppNameFilter(app_name)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.addFilter(app_name_filter)

    json_formatter = JsonFormatter(
        "%(name)s %(asctime)s %(levelname)s %(appname)s %(message)s",
        rename_fields={
            "levelname": "severity",
            "asctime": "timestamp",
        },
    )

    if enable_json_formatter:
        stream_handler.setFormatter(json_formatter)

    handlers = [stream_handler]
    logging.basicConfig(
        level=log_level,
        format="%(name)s %(levelname)s %(message)s",
        handlers=handlers,
    )

    if log_level == logging.DEBUG:
        # This is way too chatty at log level debug, so regardless of our settings, set to INFO
        logging.getLogger("httpcore").setLevel(logging.INFO)


class AppNameFilter(logging.Filter):
    """
    A logging filter that adds an application name to log records.

    This class extends the logging.Filter to include a specific application
    name (`appname`) in each log record. Useful for distinguishing logs
    from different applications or components when aggregating logs.
    """

    def __init__(self, appname: str, *args, **kwargs):
        self.appname = appname
        super().__init__(*args, **kwargs)

    def filter(self, record: logging.LogRecord) -> bool:
        record.appname = self.appname
        return True


class JsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom formatter for JSON logging.

    This class extends functionality of `jsonlogger.JsonFormatter`
    to include a timestamp in RFC 3339 format with microsecond precision.
    It customizes log records for specific formatting requirements,
    particularly focusing on time formatting.

    Attributes:
        None
    """

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None):
        # Format the timestamp as RFC 3339 with microsecond precision
        isoformat = datetime.fromtimestamp(record.created).isoformat()
        return f"{isoformat}Z"
