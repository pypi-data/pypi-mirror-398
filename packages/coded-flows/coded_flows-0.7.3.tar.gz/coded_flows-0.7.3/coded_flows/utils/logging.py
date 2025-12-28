import logging
import sys
from typing import Optional


class _ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels and process names.
    Uses ANSI escape codes with modern flat UI color palette for terminal output.
    """

    # Modern flat UI color palette (256-color ANSI codes)
    COLORS = {
        "DEBUG": "\033[38;5;117m",  # Soft Blue (#87D7FF)
        "INFO": "\033[38;5;78m",  # Emerald Green (#5FD787)
        "WARNING": "\033[38;5;214m",  # Sunflower Orange (#FFAF00)
        "ERROR": "\033[38;5;203m",  # Alizarin Red (#FF5F5F)
        "CRITICAL": "\033[38;5;200m",  # Pomegranate (#FF00D7)
    }

    # Color for process/logger name - Modern purple/indigo
    NAME_COLOR = "\033[38;5;141m"  # Amethyst Purple (#AF87FF)

    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_colors: bool = True,
    ):
        """
        Initialize the colored formatter.

        Args:
            fmt: Log message format string
            datefmt: Date format string
            use_colors: Whether to use colors (disable for file logging)
        """
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        if self.use_colors:
            # Save original values
            levelname_original = record.levelname
            name_original = record.name
            msg_original = record.msg

            # Pad the levelname to 8 characters BEFORE adding color codes
            # This ensures consistent width regardless of color codes
            padded_levelname = f"{record.levelname:<8}"

            # Get the color for this log level
            level_color = self.COLORS.get(record.levelname, "")

            # Add color to the padded levelname
            record.levelname = f"{self.BOLD}{level_color}{padded_levelname}{self.RESET}"

            # Pad the name to 20 characters BEFORE adding color codes
            padded_name = f"{record.name:<20}"

            # Add color to the padded name
            record.name = f"{self.BOLD}{self.NAME_COLOR}{padded_name}{self.RESET}"

            # Color the message with the same color as the level (lighter, no bold)
            if isinstance(record.msg, str):
                record.msg = f"{level_color}{record.msg}{self.RESET}"

            # Format the message
            formatted = super().format(record)

            # Restore original values
            record.levelname = levelname_original
            record.name = name_original
            record.msg = msg_original

            return formatted
        else:
            return super().format(record)


class CodedFlowsLogger:
    """
    Standard logger class with colored console output and optional file logging.
    Provides industry-standard formatting with aligned columns for consistent display.
    """

    # Default format with fixed widths for aligned display
    # Note: We pad levelname and name in the formatter, not here
    DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        name: str = "App",
        level: int = logging.INFO,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None,
        log_file: Optional[str] = None,
        file_level: Optional[int] = None,
    ):
        """
        Initialize the standard logger.

        Args:
            name: Display name for the logger (e.g., "My Brick", "Data Processor")
            level: Console logging level (default: INFO)
            log_format: Custom format string (optional)
            date_format: Custom date format string (optional)
            log_file: Path to log file (optional)
            file_level: File logging level (optional, defaults to DEBUG)
        """
        # Use the provided name as the logger name (for display)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Set to DEBUG, handlers will filter

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Use provided formats or defaults
        fmt = log_format or self.DEFAULT_FORMAT
        datefmt = date_format or self.DEFAULT_DATE_FORMAT

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = _ColoredFormatter(fmt, datefmt, use_colors=True)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Optional file handler without colors
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(file_level or logging.DEBUG)
            file_formatter = _ColoredFormatter(fmt, datefmt, use_colors=False)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger

    # Convenience methods that delegate to the logger
    def debug(self, msg, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log an info message."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log an error message."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(msg, *args, **kwargs)
