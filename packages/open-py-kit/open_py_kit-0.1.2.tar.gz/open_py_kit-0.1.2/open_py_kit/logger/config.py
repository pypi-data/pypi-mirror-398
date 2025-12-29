from dataclasses import dataclass, field
from typing import Dict, Optional
import os
from .levels import LEVEL_MAP


@dataclass
class LoggerConfig:
    log_level: str = "INFO"
    enable_console: bool = True
    console_json_format: bool = False
    enable_file: bool = False
    log_file_location: str = "/tmp/app.log"
    # Map of module name to log level string, e.g. {"router.GA": "DEBUG"}
    module_levels: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "LoggerConfig":
        """
        Creates a LoggerConfig from environment variables.
        """
        c = cls()
        c.log_level = os.getenv("LOG_LEVEL", "INFO")
        c.enable_console = os.getenv("LOGGER_ENABLE_CONSOLE", "true").lower() == "true"
        c.console_json_format = (
            os.getenv("LOGGER_CONSOLE_JSON_FORMAT", "false").lower() == "true"
        )
        c.enable_file = os.getenv("LOGGER_ENABLE_FILE", "false").lower() == "true"
        c.log_file_location = os.getenv("LOGGER_LOG_FILE_LOCATION", "/tmp/app.log")

        # Parse module levels from something like "router.GA=DEBUG:warehouse.REDSHIFT=DEBUG"
        module_levels_str = os.getenv("LOGGER_MODULE_LEVELS", "")
        if module_levels_str:
            pairs = module_levels_str.split(":")
            for pair in pairs:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    if v in LEVEL_MAP:
                        c.module_levels[k.strip()] = v.strip()

        return c

    def get_level_int(self, level_str: Optional[str] = None) -> int:
        l = level_str or self.log_level
        return LEVEL_MAP.get(l, LEVEL_MAP["INFO"])
