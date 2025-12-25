import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, cast, override

from rich.logging import RichHandler

_LOGGER_NAME = "zona"
TRACE_LEVEL = 5


class ZonaLogger(logging.Logger):
	def trace(
		self,
		msg: object,
		*args: object,
		exc_info: Any = None,
		stack_info: bool = False,
		stacklevel: int = 1,
		extra: Mapping[str, object] | None = None,
	) -> None:
		if self.isEnabledFor(TRACE_LEVEL):
			self._log(
				TRACE_LEVEL,
				msg,
				args,
				exc_info,
				extra,
				stack_info,
				stacklevel,
			)


logging.addLevelName(level=TRACE_LEVEL, levelName="TRACE")
logging.setLoggerClass(ZonaLogger)
# addLoggingLevel("TRACE", logging.DEBUG - 5)


class PathStrippingFormatter(logging.Formatter):
	def __init__(
		self,
		fmt: str | None = None,
		datefmt: str | None = None,
		style: Literal["%", "{", "$"] = "%",
		validate: bool = True,
		prefix: Path | None = None,
		*,
		defaults: Mapping[str, Any] | None = None,
	) -> None:
		super().__init__(fmt, datefmt, style, validate, defaults=defaults)
		self.prefix: str | None = str(prefix.absolute()) if prefix else None

	def set_prefix(self, prefix: Path):
		if not self.prefix:
			self.prefix = str(prefix.absolute())

	@override
	def format(self, record: logging.LogRecord) -> str:
		msg = super().format(record)
		if self.prefix:
			msg = msg.replace(self.prefix + os.sep, "")
		return msg


def setup_logging(
	level: str = "INFO",
	fmt: str | None = "%(message)s",
):
	logger = logging.getLogger(_LOGGER_NAME)
	logger.setLevel(level.upper())

	logger.propagate = False

	if not logger.handlers:
		handler = RichHandler(
			rich_tracebacks=True,
			show_path=False,
			show_time=False,
			# level=5,
		)
		# handler.setLevel(TRACE_LEVEL)
		handler.setLevel(level.upper())
		formatter = PathStrippingFormatter(prefix=None, fmt=fmt)
		handler.setFormatter(formatter)
		logger.addHandler(handler)


def set_logger_prefix(logger: logging.Logger, prefix: Path) -> logging.Logger:
	for handler in logger.handlers:
		formatter = getattr(handler, "formatter", None)
		if isinstance(formatter, PathStrippingFormatter):
			formatter.set_prefix(prefix)
	return logger


def get_logger(name: str = _LOGGER_NAME) -> ZonaLogger:
	return cast(ZonaLogger, logging.getLogger(name))
