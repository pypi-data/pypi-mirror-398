import logging
import sys
from typing import Optional, Dict
from pythonjsonlogger import jsonlogger
from .logger import KitLogger
from .config import LoggerConfig
from .interface import Logger
from .levels import LEVEL_MAP


class LoggerFactory:
    def __init__(self, config: LoggerConfig):
        self.config = config
        self._setup_root_logger()

    def _setup_root_logger(self):
        root = logging.getLogger()
        root.setLevel(self.config.get_level_int())

        # Clear existing handlers
        if root.handlers:
            for handler in root.handlers:
                root.removeHandler(handler)

        handlers = []

        # Console Handler
        if self.config.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            if self.config.console_json_format:
                formatter = jsonlogger.JsonFormatter(
                    "%(asctime)s %(levelname)s %(name)s %(message)s"
                )
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)

        # File Handler
        if self.config.enable_file:
            file_handler = logging.FileHandler(self.config.log_file_location)
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        for h in handlers:
            root.addHandler(h)

        # Apply module specific levels
        for module, level_str in self.config.module_levels.items():
            logging.getLogger(module).setLevel(self.config.get_level_int(level_str))

    def new_logger(self) -> Logger:
        """
        Creates a new root logger wrapper.
        """
        # We wrap the python root logger or a specifically named one?
        # In Go, it wraps zaps root.
        # Here we usually want a named logger for the application
        return KitLogger(logging.getLogger("root"), self.config, "root")


# Global Default Factory
DefaultFactory = LoggerFactory(LoggerConfig())


def NewFactory(config: LoggerConfig) -> LoggerFactory:
    global DefaultFactory
    DefaultFactory = LoggerFactory(config)
    return DefaultFactory


def NewLogger(config: Optional[LoggerConfig] = None) -> Logger:
    if config:
        return NewFactory(config).new_logger()
    return DefaultFactory.new_logger()
