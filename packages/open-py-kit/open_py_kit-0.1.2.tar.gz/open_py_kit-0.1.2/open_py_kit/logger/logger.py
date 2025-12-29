import logging
import json
from typing import Any, Optional, Dict, Tuple
from .interface import Logger
from .field import Field, expand_fields
from .config import LoggerConfig


class KitLogger(Logger):
    def __init__(
        self,
        logger: logging.Logger,
        config: LoggerConfig,
        name: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        self._logger = logger
        self._config = config
        self._name = name
        self._context = context or {}

    def is_debug_level(self) -> bool:
        return self._logger.isEnabledFor(logging.DEBUG)

    def _log(self, level: int, msg: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]):
        extra = kwargs.get("extra", {})
        # Merge context into extra
        if self._context:
            extra.update(self._context)

        # Merge structured fields from kwargs into extra
        # This assumes we are using python-json-logger or similar that looks at `extra`
        # OR we can manually format them into the message if using standard text logging
        # For now, we put them in extra so JSON formatter picks them up.

        structured_data = {
            k: v
            for k, v in kwargs.items()
            if k != "extra" and k != "exc_info" and k != "stack_info"
        }
        if structured_data:
            extra.update(structured_data)

        kwargs["extra"] = extra

        # Cleanup kwargs that were moved to extra to avoid TypeErrors in logger.log
        for k in list(structured_data.keys()):
            del kwargs[k]

        self._logger.log(level, msg, *args, **kwargs)

    # Standard levels matching Go's fmt.Print style (space separated)
    def debug(self, *args: Any) -> None:
        if self.is_debug_level():
            msg = " ".join(map(str, args))
            self._log(logging.DEBUG, msg, (), {})

    def info(self, *args: Any) -> None:
        if self._logger.isEnabledFor(logging.INFO):
            msg = " ".join(map(str, args))
            self._log(logging.INFO, msg, (), {})

    def warn(self, *args: Any) -> None:
        if self._logger.isEnabledFor(logging.WARNING):
            msg = " ".join(map(str, args))
            self._log(logging.WARNING, msg, (), {})

    def error(self, *args: Any) -> None:
        if self._logger.isEnabledFor(logging.ERROR):
            msg = " ".join(map(str, args))
            self._log(logging.ERROR, msg, (), {})

    def fatal(self, *args: Any) -> None:
        # Critical + Stack Trace (Go's Fatal usually exits, but library loggers shouldn't exit the app directly unless designed to)
        # Go implementation: Logs error + stacktrace.
        msg = " ".join(map(str, args))
        self._log(logging.CRITICAL, msg, (), {"stack_info": True})

    # Formatted levels
    def debugf(self, format: str, *args: Any) -> None:
        if self.is_debug_level():
            self._log(logging.DEBUG, format % args, (), {})

    def infof(self, format: str, *args: Any) -> None:
        if self._logger.isEnabledFor(logging.INFO):
            self._log(logging.INFO, format % args, (), {})

    def warnf(self, format: str, *args: Any) -> None:
        if self._logger.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, format % args, (), {})

    def errorf(self, format: str, *args: Any) -> None:
        if self._logger.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, format % args, (), {})

    def fatalf(self, format: str, *args: Any) -> None:
        self._log(logging.CRITICAL, format % args, (), {"stack_info": True})

    # Structured (Sugared) levels
    def debugw(self, msg: str, **kwargs: Any) -> None:
        if self.is_debug_level():
            self._log(logging.DEBUG, msg, (), kwargs)

    def infow(self, msg: str, **kwargs: Any) -> None:
        if self._logger.isEnabledFor(logging.INFO):
            self._log(logging.INFO, msg, (), kwargs)

    def warnw(self, msg: str, **kwargs: Any) -> None:
        if self._logger.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, msg, (), kwargs)

    def errorw(self, msg: str, **kwargs: Any) -> None:
        if self._logger.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, msg, (), kwargs)

    def fatalw(self, msg: str, **kwargs: Any) -> None:
        kwargs["stack_info"] = True
        self._log(logging.CRITICAL, msg, (), kwargs)

    # Structured (Typed) levels
    def debugn(self, msg: str, *fields: Field) -> None:
        if self.is_debug_level():
            self.debugw(msg, **expand_fields(fields))

    def infon(self, msg: str, *fields: Field) -> None:
        self.infow(msg, **expand_fields(fields))

    def warnn(self, msg: str, *fields: Field) -> None:
        self.warnw(msg, **expand_fields(fields))

    def errorn(self, msg: str, *fields: Field) -> None:
        self.errorw(msg, **expand_fields(fields))

    def fataln(self, msg: str, *fields: Field) -> None:
        self.fatalw(msg, **expand_fields(fields))

    # Context methods
    def child(self, name: str) -> "Logger":
        if not name:
            return self
        new_name = f"{self._name}.{name}" if self._name else name

        # Get new logger instance from logging framework to allow granular level control
        child_logger_impl = logging.getLogger(new_name)

        # Apply config-based level if defined
        if new_name in self._config.module_levels:
            level_str = self._config.module_levels[new_name]
            child_logger_impl.setLevel(self._config.get_level_int(level_str))
        else:
            child_logger_impl.setLevel(self._logger.level)

        return KitLogger(
            child_logger_impl, self._config, new_name, self._context.copy()
        )

    def with_fields(self, **kwargs: Any) -> "Logger":
        new_context = self._context.copy()
        new_context.update(kwargs)
        return KitLogger(self._logger, self._config, self._name, new_context)

    def withn(self, *fields: Field) -> "Logger":
        return self.with_fields(**expand_fields(fields))
