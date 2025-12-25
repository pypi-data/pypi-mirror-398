from dataclasses import dataclass
from datetime import date, datetime, time, tzinfo
from pathlib import Path

import frontmatter
from dacite.config import Config
from dacite.core import from_dict
from dacite.exceptions import DaciteError
from dateutil import parser as date_parser
from yaml import YAMLError

import zona.util
from zona.config import ZonaConfig


@dataclass
class Metadata:
	title: str
	date: datetime
	description: str
	subtitle: str | None = None
	show_title: bool = True
	show_date: bool = True
	show_nav: bool = True
	style: str | None = "/static/style.css"
	header: bool = True
	footer: bool = True
	template: str | None = None
	post: bool | None = None
	draft: bool = False
	ignore: bool = False
	math: bool = True


def ensure_timezone(dt: datetime, tz: tzinfo) -> datetime:
	if dt.tzinfo is None or dt.utcoffset() is None:
		dt = dt.replace(tzinfo=tz)
	return dt


# TODO: migrate to using datetime, where user can optionall specify
# a time as well. if only date is given, default to time.min
def parse_date(raw_date: str | datetime | date | object, tz: tzinfo) -> datetime:
	if isinstance(raw_date, datetime):
		return ensure_timezone(raw_date, tz)
	elif isinstance(raw_date, date):
		return datetime.combine(raw_date, time.min, tzinfo=tz)
	assert isinstance(raw_date, str)
	dt = date_parser.parse(raw_date)
	return ensure_timezone(dt, tz)


def parse_metadata(path: Path, config: ZonaConfig) -> tuple[Metadata, str]:
	"""
	Parses a file and returns parsed Metadata and its content. Defaults
	are applied for missing fields. If there is no metadata, a Metadata
	with default values is returned.

	Raises:
	    ValueError: If the metadata block is malformed in any way.
	"""
	try:
		post = frontmatter.load(str(path))
	except YAMLError as e:
		raise ValueError(f"YAML frontmatter error in {path}: {e}")
	raw_meta = post.metadata or {}
	defaults = {
		"title": zona.util.filename_to_title(path),
		"date": datetime.fromtimestamp(path.stat().st_ctime),
		"description": config.blog.defaults.description,
	}
	meta = {**defaults, **raw_meta}
	meta["date"] = parse_date(meta.get("date"), config.feed.timezone)
	try:
		metadata = from_dict(
			data_class=Metadata,
			data=meta,
			config=Config(check_types=True, strict=True),
		)
	except DaciteError as e:
		raise ValueError(f"Malformed metadata in {path}: {e}")
	return metadata, post.content
