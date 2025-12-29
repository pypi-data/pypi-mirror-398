from typing import Any
from .interface import Logger
from .field import Field


class NopLogger(Logger):
    def is_debug_level(self) -> bool:
        return False

    def debug(self, *args: Any) -> None:
        pass

    def debugf(self, format: str, *args: Any) -> None:
        pass

    def debugw(self, msg: str, **kwargs: Any) -> None:
        pass

    def debugn(self, msg: str, *fields: Field) -> None:
        pass

    def info(self, *args: Any) -> None:
        pass

    def infof(self, format: str, *args: Any) -> None:
        pass

    def infow(self, msg: str, **kwargs: Any) -> None:
        pass

    def infon(self, msg: str, *fields: Field) -> None:
        pass

    def warn(self, *args: Any) -> None:
        pass

    def warnf(self, format: str, *args: Any) -> None:
        pass

    def warnw(self, msg: str, **kwargs: Any) -> None:
        pass

    def warnn(self, msg: str, *fields: Field) -> None:
        pass

    def error(self, *args: Any) -> None:
        pass

    def errorf(self, format: str, *args: Any) -> None:
        pass

    def errorw(self, msg: str, **kwargs: Any) -> None:
        pass

    def errorn(self, msg: str, *fields: Field) -> None:
        pass

    def fatal(self, *args: Any) -> None:
        pass

    def fatalf(self, format: str, *args: Any) -> None:
        pass

    def fatalw(self, msg: str, **kwargs: Any) -> None:
        pass

    def fataln(self, msg: str, *fields: Field) -> None:
        pass

    def child(self, name: str) -> "Logger":
        return self

    def with_fields(self, **kwargs: Any) -> "Logger":
        return self

    def withn(self, *fields: Field) -> "Logger":
        return self
