from __future__ import annotations

from abc import ABC
from collections.abc import Iterator
from typing import Any, override


class Issue(ABC):
	def __init__(self, message: str):
		self.message: str = message
		self._name: str = "ISSUE"
		self.log_level: str = "debug"

	@override
	def __str__(self) -> str:
		return self.message

	@override
	def __repr__(self) -> str:
		return f"[{self._name}] {self.message}"

	def log(self):
		from zona.log import get_logger

		logger = get_logger()
		log_func = getattr(logger, self.log_level, logger.debug)
		log_func(self.message)


class WarningIssue(Issue):
	def __init__(self, message: str):
		super().__init__(message)
		self._name: str = "WARNING"
		self.log_level: str = "warning"


class ErrorIssue(Issue):
	def __init__(self, message: str):
		super().__init__(message)
		self._name: str = "ERROR"
		self.log_level: str = "error"


class IssueCollector:
	_type: type[Issue] = Issue

	def __init__(self):
		self._issues: list[Issue] = []

	def add(self, issue: Issue):
		self._issues.append(issue)
		issue.log()

	def log_all(self):
		for issue in self._issues:
			issue.log()

	def clear(self):
		self._issues.clear()

	def __call__(self, arg: str | Issue):
		if isinstance(arg, Issue):
			self.add(arg)
		else:
			self.add(self._type(arg))

	def __bool__(self):
		return bool(self._issues)

	def __len__(self):
		return len(self._issues)

	def __iter__(self) -> Iterator[Issue]:
		return iter(self._issues)

	def __getitem__(self, index: int) -> Issue:
		return self._issues[index]

	def __enter__(self):
		self.clear()
		return self

	def __exit__(self, *args: Any):
		if self:
			from zona.log import get_logger

			name = type(self).__name__
			get_logger().debug(
				f"{len(self)} {name.lower()}{'' if len(self) == 1 else 's'} total."
			)

	@override
	def __eq__(self, other: object) -> bool:
		if isinstance(other, IssueCollector):
			return self._issues == other._issues
		return False

	@override
	def __str__(self):
		return f"Warnings({len(self)} issue{'s' if len(self) != 1 else ''})"

	@override
	def __repr__(self):
		return f"<Warnings with {len(self)} issue{'s' if len(self) != 1 else ''}>"

	def __contains__(self, msg: Issue):
		return msg in self._issues

	def filter(self, type_: type[Issue]) -> list[Issue]:
		return [i for i in self._issues if isinstance(i, type_)]


class WarningCollector(IssueCollector):
	_type: type[Issue] = WarningIssue


class ErrorCollector(IssueCollector):
	_type: type[Issue] = ErrorIssue


# global instance
warnings = WarningCollector()
errors = ErrorCollector()
