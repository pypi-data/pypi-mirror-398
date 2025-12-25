import logging
from _typeshed import Incomplete
from gllm_core.constants import LogMode as LogMode
from pythonjsonlogger.core import LogRecord
from pythonjsonlogger.json import JsonFormatter
from rich.logging import RichHandler

DEFAULT_DATE_FORMAT: str
TEXT_COLOR_MAP: Incomplete
LOG_FORMAT_KEY: str
RICH_CLOSE_TAG: str
JSON_LOG_FIELDS: Incomplete
JSON_ERROR_FIELDS_MAP: Incomplete

class TextRichHandler(RichHandler):
    """Custom RichHandler that applies specific colors and log format."""
    def emit(self, record: logging.LogRecord) -> None:
        """Emits a log record with custom coloring.

        Args:
            record (logging.LogRecord): The log record to emit.
        """

class SimpleRichHandler(logging.StreamHandler):
    """Custom StreamHandler that utilizes Rich only to apply colors, without columns or Rich formatting.

    Attributes:
        console (Console): The Rich Console object to use for printing.
    """
    console: Incomplete
    def __init__(self, *args, **kwargs) -> None:
        """Initializes a new instance of the SimpleRichHandler class."""
    def emit(self, record: logging.LogRecord) -> None:
        """Emits a log record with simple Rich coloring.

        Args:
            record (logging.LogRecord): The log record to emit.
        """

class AppJSONFormatter(JsonFormatter):
    """JSON formatter that groups error-related fields under an 'error' key.

    This formatter renames the following fields when present:
    1. exc_info -> error.message
    2. stack_info -> error.stacktrace
    3. error_code -> error.code
    """
    def process_log_record(self, log_record: LogRecord) -> LogRecord:
        """Process log record to group and rename error-related fields.

        Args:
            log_record (LogRecord): The original log record.

        Returns:
            LogRecord: The processed log record.
        """

LOG_FORMAT_HANDLER_MAP: Incomplete
LOG_FORMAT_MAP: Incomplete

class LoggerManager:
    '''A singleton class to manage logging configuration.

    This class ensures that the root logger is initialized only once and is used across the application.

    Basic usage:
        The `LoggerManager` can be used to get a logger instance as follows:
        ```python
        logger = LoggerManager().get_logger()
        logger.info("This is an info message")
        ```

    Set logging configuration:
        The `LoggerManager` also provides capabilities to set the logging configuration:
        ```python
        manager = LoggerManager()
        manager.set_level(logging.DEBUG)
        manager.set_log_format(custom_log_format)
        manager.set_date_format(custom_date_format)
        ```

    Add custom handlers:
        The `LoggerManager` also provides capabilities to add custom handlers to the root logger:
        ```python
        manager = LoggerManager()
        handler = logging.FileHandler("app.log")
        manager.add_handler(handler)
        ```

    Extra error information:
        When logging errors, extra error information can be added as follows:
        ```python
        logger.error("I am dead!", extra={"error_code": "ERR_CONN_REFUSED"})
        ```

    Logging modes:
        The `LoggerManager` supports three logging modes:

        1. Text: Logs in a human-readable format with RichHandler column-based formatting.
            Used when the `LOG_FORMAT` environment variable is set to "text".
            Output example:
            ```log
            2025-10-08T09:26:16 DEBUG    [LoggerName] This is a debug message.
            2025-10-08T09:26:17 INFO     [LoggerName] This is an info message.
            2025-10-08T09:26:18 WARNING  [LoggerName] This is a warning message.
            2025-10-08T09:26:19 ERROR    [LoggerName] This is an error message.
            2025-10-08T09:26:20 CRITICAL [LoggerName] This is a critical message.
            ```

        2. Simple: Logs in a human-readable format with Rich colors but without columns-based formatting.
            Used when the `LOG_FORMAT` environment variable is set to "simple".
            Output example:
            ```log
            [2025-10-08T09:26:16.123 LoggerName DEBUG] This is a debug message.
            [2025-10-08T09:26:17.456 LoggerName INFO] This is an info message.
            [2025-10-08T09:26:18.789 LoggerName WARNING] This is a warning message.
            [2025-10-08T09:26:19.012 LoggerName ERROR] This is an error message.
            [2025-10-08T09:26:20.345 LoggerName CRITICAL] This is a critical message.
            ```

        3. JSON: Logs in a JSON format, recommended for easy parsing due to the structured nature of the log records.
            Used when the `LOG_FORMAT` environment variable is set to "json".
            Output example:
            ```log
            {"timestamp": "2025-10-08T11:23:43+0700", "name": "LoggerName", "level": "DEBUG", "message": "..."}
            {"timestamp": "2025-10-08T11:23:44+0700", "name": "LoggerName", "level": "INFO", "message": "..."}
            {"timestamp": "2025-10-08T11:23:45+0700", "name": "LoggerName", "level": "WARNING", "message": "..."}
            {"timestamp": "2025-10-08T11:23:46+0700", "name": "LoggerName", "level": "ERROR", "message": "..."}
            {"timestamp": "2025-10-08T11:23:47+0700", "name": "LoggerName", "level": "CRITICAL", "message": "..."}
            ```

        When the `LOG_FORMAT` environment is not set, the `LoggerManager` defaults to "text" mode.
    '''
    def __new__(cls) -> LoggerManager:
        """Initialize the singleton instance.

        Returns:
            LoggerManager: The singleton instance.
        """
    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Get a logger instance.

        This method returns a logger instance that is a child of the root logger. If name is not provided,
        the root logger will be returned instead.

        Args:
            name (str | None, optional): The name of the child logger. If None, the root logger will be returned.
                Defaults to None.

        Returns:
            logging.Logger: Configured logger instance.
        """
    def set_level(self, level: int) -> None:
        """Set logging level for all loggers in the hierarchy.

        Args:
            level (int): The logging level to set (e.g., logging.INFO, logging.DEBUG).
        """
    def set_log_format(self, log_format: str) -> None:
        """Set logging format for all loggers in the hierarchy.

        Args:
            log_format (str): The log format to set.
        """
    def set_date_format(self, date_format: str) -> None:
        """Set date format for all loggers in the hierarchy.

        Args:
            date_format (str): The date format to set.
        """
    def add_handler(self, handler: logging.Handler) -> None:
        """Add a custom handler to the root logger.

        Args:
            handler (logging.Handler): The handler to add to the root logger.
        """
