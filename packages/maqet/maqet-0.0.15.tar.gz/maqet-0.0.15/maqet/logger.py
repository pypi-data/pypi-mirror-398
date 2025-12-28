"""
Advanced logging setup for MAQET with configurable verbosity and file output.

Provides colored console output, file logging, and verbosity level control.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for different log levels."""

    # Bold colors for severe levels
    RED_BOLD = "\x1b[31;1m"
    YELLOW_BOLD = "\x1b[33;1m"
    CYAN_BOLD = "\x1b[36;1m"

    # Dim/regular colors for info levels
    GREY_DIM = "\x1b[90m"  # Dim grey for debug
    WHITE = "\x1b[97m"  # Bright white for info

    # Reset
    RESET = "\x1b[0m"

    MESSAGE_FORMAT = " %(message)s "

    FORMATS = {
        logging.DEBUG: GREY_DIM
        + "D"
        + RESET
        + GREY_DIM
        + MESSAGE_FORMAT
        + RESET,
        logging.INFO: WHITE + "I" + RESET + WHITE + MESSAGE_FORMAT + RESET,
        logging.WARNING: CYAN_BOLD + "W" + RESET + MESSAGE_FORMAT,
        logging.ERROR: YELLOW_BOLD + "E" + RESET + MESSAGE_FORMAT,
        logging.CRITICAL: RED_BOLD + "C" + RESET + MESSAGE_FORMAT,
    }

    def format(self, record):
        """Format log record with appropriate color."""
        log_fmt = self.FORMATS.get(record.levelno, self.MESSAGE_FORMAT)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class MaqetLogger:
    """MAQET logging manager with configurable verbosity and file output.

    Features:
    - Colored console output for improved readability
    - Rotating file logs (10MB max, 5 backups = 60MB total)
    - Configurable verbosity levels (ERROR/WARNING/INFO/DEBUG)
    """

    def __init__(self, name: str = "maqet"):
        """
        Initialize the logger.

        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Setup console handler with colored formatting
        self._setup_console_handler()

        # File handler will be added when configure_file_logging is called
        self._file_handler: Optional[logging.FileHandler] = None

    def _setup_console_handler(self):
        """Setup colored console output handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        console_handler.setLevel(logging.ERROR)  # Default console level
        self.logger.addHandler(console_handler)

    def set_verbosity(self, verbosity_level: int):
        """
        Set logging verbosity level.

        Args:
            verbosity_level: 0=ERROR, 1=WARNING, 2=INFO, 3+=DEBUG
        """
        level_map = {
            0: logging.ERROR,    # 40 - No -v flags (default, errors only)
            1: logging.WARNING,  # 30 - -v (shows warnings + errors)
            2: logging.INFO,     # 20 - -vv
            3: logging.DEBUG,    # 10 - -vvv or more
        }

        # Cap at DEBUG level for anything >= 3
        if verbosity_level >= 3:
            level = logging.DEBUG
        else:
            level = level_map.get(verbosity_level, logging.ERROR)

        # Update console handler level
        for handler in self.logger.handlers:
            if (
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
            ):
                handler.setLevel(level)
                break

    def configure_file_logging(
        self, log_file: Optional[Path] = None, mode: str = "w"
    ):
        """
        Configure file logging output with rotation.

        Uses RotatingFileHandler to prevent unbounded log growth:
        - Maximum file size: 10MB
        - Backup count: 5 files
        - Total maximum size: 60MB (current + 5 backups)

        Args:
            log_file: Path to log file. If None, uses 'maqet.log' in current directory
            mode: File open mode ('w' for overwrite, 'a' for append) - ignored for rotating handler
        """
        from logging.handlers import RotatingFileHandler

        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            self._file_handler = None

        if log_file is None:
            log_file = Path("maqet.log")

        # Create log file parent directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup rotating file handler with 10MB max size and 5 backups
        max_bytes = 10 * 1024 * 1024  # 10MB
        backup_count = 5  # Keep 5 old log files

        self._file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        self._file_handler.setLevel(
            logging.DEBUG
        )  # Always log everything to file

        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self._file_handler.setFormatter(file_formatter)

        self.logger.addHandler(self._file_handler)

    def get_logger(self) -> logging.Logger:
        """Get the underlying logger instance."""
        return self.logger


# Global logger instance
_maqet_logger = MaqetLogger()
LOG = _maqet_logger.get_logger()


def set_verbosity(level: int):
    """Set global logging verbosity level."""
    _maqet_logger.set_verbosity(level)


def configure_file_logging(log_file: Optional[Path] = None, mode: str = "w"):
    """Configure global file logging."""
    _maqet_logger.configure_file_logging(log_file, mode)
