import logging

# Define constants for log levels
LEVEL_DEBUG = logging.DEBUG
LEVEL_INFO = logging.INFO
LEVEL_WARN = logging.WARNING
LEVEL_ERROR = logging.ERROR
LEVEL_FATAL = logging.CRITICAL

# Map string levels to logging constants
LEVEL_MAP = {
    "DEBUG": LEVEL_DEBUG,
    "INFO": LEVEL_INFO,
    "WARN": LEVEL_WARN,
    "ERROR": LEVEL_ERROR,
    "FATAL": LEVEL_FATAL,
}
