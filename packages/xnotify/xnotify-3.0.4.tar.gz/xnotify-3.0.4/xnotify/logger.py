"""Logging utilities for xnotify."""

import logging
import sys
from pathlib import Path
from typing import Optional
import os

def setup_logger(*args, **kwargs):
    try:
        from richcolorlog import setup_logging  # type: ignore
        if str(os.getenv('DEBUG', '0')).lower() in ['1', 'true', 'ok', 'yes']:
            print("Using richcolorlog for enhanced logging.")
            LOG_LEVEL = os.getenv("LOG_LEVEL", 'DEBUG').upper()
            kwargs.update({'level': LOG_LEVEL})
        else:
            LOG_LEVEL = os.getenv("LOG_LEVEL", 'ERROR').upper()
            kwargs.update({'level': LOG_LEVEL})

        exceptions = kwargs.pop('exceptions', ['requests'])
        if 'requests' in exceptions and LOG_LEVEL == 'DEBUG':
            exceptions.remove('requests')
        kwargs.update({'exceptions': exceptions})
        return setup_logging(*args, **kwargs)

    except:
        if str(os.getenv('DEBUG', '0')).lower() in ['1', 'true', 'ok', 'yes']:
            LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", 'DEBUG').upper())
        else:
            LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", 'ERROR').upper())
        exceptions = kwargs.pop('exceptions', ['requests'])
        if 'requests' in exceptions and LOG_LEVEL == 'DEBUG':
            exceptions.remove('requests')
        for exc in exceptions:
            logging.getLogger(exc).setLevel(LOG_LEVEL)

        CUSTOM_LOG_LEVELS = {
            # Syslog RFC5424 severity (0 = highest severity)
            # We map to the top of the Python logging range (10–60)
            "EMERGENCY": 60,   # System unusable
            "ALERT":     55,   # Immediate action required
            "CRITICAL":  logging.CRITICAL,  # 50
            "ERROR":     logging.ERROR,     # 40
            "WARNING":   logging.WARNING,   # 30
            "NOTICE":    25,   # Normal but significant condition
            "INFO":      logging.INFO,      # 20
            "DEBUG":     logging.DEBUG,     # 10

            # Custom level tambahan
            "SUCCESS":   22,   # Operation successful
            "FATAL":     65,   # Hard failure beyond CRITICAL
        }

        # ============================================================
        # 2. LEVEL REGISTRATION TO LOGGING
        # ============================================================

        def register_custom_levels():
            for level_name, level_value in CUSTOM_LOG_LEVELS.items():
                # Register for Python logging
                logging.addLevelName(level_value, level_name)

                # Tambah method ke logging.Logger
                def log_for(level):
                    def _log_method(self, message, *args, **kwargs):
                        if self.isEnabledFor(level):
                            self._log(level, message, args, **kwargs)
                    return _log_method

                # buat method lowercase: logger.emergency(), logger.notice(), dll
                setattr(logging.Logger, level_name.lower(), log_for(level_value))


        register_custom_levels()

        # ============================================================
        # 3. FORMATTER DETAIL & PROFESSIONAL
        # ============================================================

        DEFAULT_FORMAT = (
            "[%(asctime)s] "
            "%(levelname)-10s "
            "%(name)s: "
            "%(message)s"
        )

        DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


        def get_default_handler():
            handler = logging.StreamHandler()
            formatter = logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
            handler.setFormatter(formatter)
            return handler


        # ============================================================
        # 4. FUNCTION TO GET THE LOGGER THAT IS READY
        # ============================================================

        def get_logger(name="default", level=LOG_LEVEL):
            logger = logging.getLogger(name)
            logger.setLevel(level)

            if not logger.handlers:  # Hindari duplicate handler
                logger.addHandler(get_default_handler())

            return logger

        return get_logger(*args, **kwargs)

def setup_logger_custom(
    name: str = 'xnotify',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure logger.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        format_string: Optional custom format string
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Default format
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = 'xnotify') -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        record.levelname = f"{log_color}{record.levelname}{reset}"
        return super().format(record)


def setup_colored_logger(
    name: str = 'xnotify',
    level: str = 'INFO',
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger with colored console output.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file path for logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()
    
    # Colored console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)
    
    # File handler (without colors)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def tracebacklog(logger, e: Optional[BaseException] = None):
    if str(os.getenv('TRACEBACK', '0')).lower() in ('1', 'true', 'yes', 'ok'):
        logger.exception(e)