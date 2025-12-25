from __future__ import annotations

from dataclasses import dataclass, field
from datetime import tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from dacite import Config as DaciteConfig
from dacite import from_dict

from zona.log import get_logger

logger = get_logger()


def find_config(start: Path | None = None) -> Path | None:
	logger.debug("Searching for config file...")
	current = (start or Path.cwd()).resolve()

	for parent in [current, *current.parents]:
		candidate = parent / "config.yml"
		if candidate.is_file():
			logger.debug(f"Config file {candidate} found.")
			return candidate
	logger.debug("Couldn't find config file.")
	return None


SitemapConfig = dict[str, str]


@dataclass
class PostDefaultsConfig:
	description: str = "A blog post"


@dataclass
class BlogConfig:
	dir: str = "blog"
	defaults: PostDefaultsConfig = field(default_factory=PostDefaultsConfig)


@dataclass
class HighlightingConfig:
	enabled: bool = True
	theme: str = "ashen"
	wrap: bool = False


@dataclass
class LinksConfig:
	external_new_tab: bool = True


@dataclass
class MarkdownConfig:
	image_labels: bool = True
	tab_length: int = 2
	syntax_highlighting: HighlightingConfig = field(default_factory=HighlightingConfig)
	links: LinksConfig = field(default_factory=LinksConfig)


@dataclass
class TimeConfig:
	timezone: tzinfo = field(default_factory=lambda: ZoneInfo("UTC"))
	format: str = r"%Y-%m-%d %H:%M %Z"


@dataclass
class BuildConfig:
	clean_output_dir: bool = True
	include_drafts: bool = False
	footer_name: str = "footer.md"
	time: TimeConfig = field(default_factory=TimeConfig)


@dataclass
class ReloadConfig:
	enabled: bool = True
	scroll_tolerance: int = 100


@dataclass
class ServerConfig:
	reload: ReloadConfig = field(default_factory=ReloadConfig)


@dataclass
class AuthorConfig:
	name: str = "John Doe"
	email: str = "john@doe.net"


@dataclass
class FeedConfig:
	enabled: bool = True
	timezone: tzinfo = field(default_factory=lambda: ZoneInfo("UTC"))
	path: str = "rss.xml"
	link: str = "https://example.com"
	title: str = "Zona Website"
	description: str = "My zona website."
	language: str = "en"
	author: AuthorConfig = field(default_factory=AuthorConfig)


IGNORELIST = [".marksman.toml"]


def parse_timezone(s: Any) -> tzinfo:
	if isinstance(s, str):
		return ZoneInfo(s)
	else:
		raise TypeError(f"Expected {str}, got {type(s)} for config key timezone")


@dataclass
class ZonaConfig:
	base_url: str = "/"
	feed: FeedConfig = field(default_factory=FeedConfig)
	# dictionary where key is name, value is url
	sitemap: SitemapConfig = field(default_factory=lambda: {"Home": "/"})
	# list of globs relative to content that should be ignored
	ignore: list[str] = field(default_factory=lambda: IGNORELIST)
	markdown: MarkdownConfig = field(default_factory=MarkdownConfig)
	build: BuildConfig = field(default_factory=BuildConfig)
	blog: BlogConfig = field(default_factory=BlogConfig)
	server: ServerConfig = field(default_factory=ServerConfig)

	@classmethod
	def from_file(cls, path: Path) -> ZonaConfig:
		with open(path, "r") as f:
			raw = yaml.safe_load(f)
		config: ZonaConfig = from_dict(
			data_class=cls,
			data=raw,
			config=DaciteConfig(type_hooks={tzinfo: parse_timezone}),
		)
		return config
