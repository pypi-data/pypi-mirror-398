"""Structured Logger configuration."""

from collections import OrderedDict
from dataclasses import dataclass
import logging
import os
import socket
import sys
import urllib.error
import urllib.request

import structlog


@dataclass
class ExternalLoggerConfig:
    """External logger configuration parameters."""

    def __init__(
        self, name: str, level: int = logging.CRITICAL, disabled=False, propagate=False
    ):
        """Construct an external logger configuration to configure external logging.

        Args:
            name: The name of the external logger
            level: The level to set for the logger
            disabled: Whether or not to disable logging
            propagate: Whether or not to propagate the log messages to the parent logger
        """
        self.name = name
        self.level = level
        self.disabled = disabled
        self.propagate = propagate


def get_logger(
    name: str, level: int | str | None = None
) -> structlog.stdlib.BoundLogger:
    """Creates a structlog logger with the specified name.

    Args:
        name (str): The logger name.
        level (int | str | None, optional): The logging level for this logger.
            If None, the root logger's level is used. Defaults to None.

    Returns:
        structlog.stdlib.BoundLogger: The structlog logger.
    """
    logger = structlog.get_logger(name)
    if level:
        # To set the level, we need to get the actual standard library logger instance.
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.setLevel(level)
    return logger


def _flatten_extra_processor(_, __, event_dict):
    """A structlog processor to flatten the 'extra' dictionary into the top level.

    Args:
        event_dict (structlog.typing.EventDict): The log event dictionary to be processed.

    Returns:
        structlog.typing.EventDict: The processed event dictionary with extra flattened.
    """
    if "extra" in event_dict:
        extra_data = event_dict.pop("extra")
        if isinstance(extra_data, dict):
            # Merge extra data into the main event_dict
            event_dict.update(extra_data)
    return event_dict


def _get_aws_metadata() -> dict:
    """A structlog processor to add AWS instance metadata to the log entry.
    This is an expensive call, so only call it when necessary.

    This function attempts to retrieve the instance-id, instance-type, and
    public-ipv4 from the AWS metadata service with a short timeout. If the
    information cannot be retrieved, 'unknown' is used as a fallback value.

    For more details, see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html

    Returns:
        dict: A dictionary with AWS metadata.
    """

    def _get_metadata(key: str, timeout: int = 1) -> str:
        """Helper to fetch a metadata key with a timeout."""
        try:
            # yes, a hard coded IPv4 is best practice
            url = f"http://169.254.169.245/latest/meta-data/{key}"
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except (urllib.error.URLError, socket.timeout):
            return "unknown"

    return {
        "aws_instance_id": _get_metadata("instance-id"),
        "aws_instance_type": _get_metadata("instance-type"),
        "aws_public_ipv4": _get_metadata("public-ipv4"),
    }


def _order_event_dict(
    _logger: structlog.typing.WrappedLogger,
    _method_name: str,
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    """A structlog processor to reorder the event dictionary.

    This processor ensures that certain important keys ("timestamp", "job_id",
    "level", "event") appear at the beginning of the log entry, making the
    logs more readable and consistent. The specified keys are ordered first,
    and any other keys in the event dictionary are appended afterwards in the
    order they were originally.

    Args:
        event_dict (structlog.typing.EventDict): The log event dictionary to be reordered.

    Returns:
        collections.OrderedDict: The event dictionary with keys reordered.
    """
    key_order = ["timestamp", "jobId", "level", "event"]
    # Use OrderedDict to preserve the order of the remaining keys.
    ordered_event_dict = OrderedDict()
    for key in key_order:
        if key in event_dict:
            ordered_event_dict[key] = event_dict.pop(key)

    # Add the rest of the items, which will now be at the end.
    ordered_event_dict.update(event_dict.items())

    return ordered_event_dict


def _secret_redaction_processor(_, __, event_dict):
    """A structlog processor to redact sensitive information in log entries.

    Args:
        event_dict (structlog.typing.EventDict): The log event dictionary to be processed.

    Returns:
        structlog.typing.EventDict: The processed event dictionary.
    """
    sensitive_keys = ["password", "api_key", "token", "SecretString"]

    def redact_dict(data):
        """Recursively redact sensitive keys in nested dictionaries.

        Args:
            data (dict): The dictionary to redact sensitive keys.

        Returns:
            dict: The redacted dictionary.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key in sensitive_keys:
                    data[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    redact_dict(value)
        return data

    # Redact top-level sensitive keys
    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "[REDACTED]"

    # Check for nested dictionaries and redact them
    for key, value in event_dict.items():
        if isinstance(value, dict):
            redact_dict(value)

    return event_dict


def initialize_logger(
    initial_context: dict | None = None,
    external_logger_configurations: list[ExternalLoggerConfig] | None = None,
    handlers: list[logging.Handler] | None = None,
) -> None:
    """Configures logging for the application using structlog.

    This function sets up `structlog` to produce structured JSON logs. It
    configures a chain of processors to enrich log entries with contextual
    information such as timestamps, host details, and log levels. The standard
    Python `logging` module is configured to act as the sink, directing the
    formatted JSON logs to standard output in JSONL format.

    The processor chain includes:
    - Merging context variables.
    - Filtering by log level.
    - Adding logger name and log level.
    - `add_host_info`: Custom processor to add hostname and IP.
    - `TimeStamper`: Adds an ISO formatted timestamp.
    - `PositionalArgumentsFormatter`: Formats positional arguments into the message.
    - Exception and stack info renderers.
    - `UnicodeDecoder`: Decodes unicode characters.
    - `order_event_dict`: Custom processor to ensure a consistent key order.
    - `JSONRenderer`: Renders the final log entry as a JSON string.

    Args:
        initial_context (dict, optional): A dictionary of key-value pairs to
            bind to the context at the start of the application. These values
            will be included in every log message. Defaults to None.
        external_logger_configurations (list[ExternalLoggerConfig], optional): A list of configuration
        handlers (list[logging.Handler], optional): A list of handlers to send log records to.
    """
    # Configure standard logging to be the sink for structlog.
    # The format="%(message)s" is important because structlog will format the log record
    # into a JSON string and pass it as the 'message'.
    formatter = logging.Formatter("%(message)s")

    # Create a handler for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    # Get the root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.addHandler(stdout_handler)
    for handler in handlers or []:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    root_logger.setLevel(_level())

    # configure external loggers
    if external_logger_configurations:
        for config in external_logger_configurations:
            logger = logging.getLogger(config.name)
            logger.setLevel(config.level)
            logger.disabled = config.disabled
            logger.propagate = config.propagate

    # Configure structlog to produce JSON logs.
    structlog.configure(
        processors=[
            # Merge contextvars into the event dictionary.
            structlog.contextvars.merge_contextvars,
            # Filter logs by level.
            structlog.stdlib.filter_by_level,
            # Add logger name and log level to the event dict.
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            # Add a timestamp in ISO format.
            structlog.processors.TimeStamper(fmt="iso"),
            # Render positional arguments into the message.
            structlog.stdlib.PositionalArgumentsFormatter(),
            # If the log record contains an exception, render it.
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _flatten_extra_processor,
            _secret_redaction_processor,
            # Decode unicode characters.
            structlog.processors.UnicodeDecoder(),
            # partial sort of key values.
            _order_event_dict,
            # Render the final event dict as JSON.
            structlog.processors.JSONRenderer(),
        ],
        # Use a standard library logger factory.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Use a wrapper class to provide standard logging methods.
        wrapper_class=structlog.stdlib.BoundLogger,
        # Cache the logger on first use.
        cache_logger_on_first_use=True,
    )

    # Gather static context information at startup.
    static_context = {}
    static_context.update(_get_aws_metadata())

    # Merge with any context provided at startup.
    if initial_context:
        static_context.update(initial_context)

    # Bind the initial context if it's provided.
    # This context will be included in all logs.
    if initial_context:
        structlog.contextvars.bind_contextvars(**static_context)


def _level() -> str:
    """Get the log level for the logger.

    The log level is determined by the `LOG_LEVEL` environment variable.
    If the environment variable is not set, it defaults to "ERROR".

    Returns:
        str: The log level as a string (e.g., "DEBUG", "INFO", "ERROR").
    """
    return os.getenv("LOG_LEVEL", "INFO").upper()
