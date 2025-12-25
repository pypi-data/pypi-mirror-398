from datetime import datetime
from pathlib import Path
from typing import Literal

from jinja2 import (
	Environment,
	FileSystemLoader,
	pass_context,
	select_autoescape,
)
from jinja2.environment import Template
from jinja2.runtime import Context

from zona import util
from zona.config import ZonaConfig
from zona.layout import discover_root
from zona.log import get_logger
from zona.markdown import md_to_html
from zona.models import Item, ReadTime

logger = get_logger()


@pass_context
def format_time(context: Context, value: str) -> str:
	rt: ReadTime = context.get("readtime")
	minutes = rt.minutes
	seconds = rt.seconds
	return value.format_map({"minutes": minutes, "seconds": seconds})


def get_header(template_dir: Path) -> str | None:
	md_header = template_dir / "header.md"
	html_header = template_dir / "header.html"
	if md_header.exists():
		return md_to_html(md_header.read_text(), None)
	elif html_header.exists():
		return html_header.read_text()


def get_template_map() -> util.TemplateMap:
	"""Returns a mapping of template names to ZonaResource tuples."""
	map = {
		str(r).removeprefix("templates/").removesuffix(".html"): r
		for r in util.get_resources("templates")
	}
	return map


def _get_templates(
	cli_root: Path | None,
) -> tuple[Path, list[util.ZonaResource]]:
	root = discover_root(cli_root)
	resources = util.get_resources("templates")
	return root, resources


def write_named_templates(names: list[str], cli_root: Path | None, force: bool = False):
	"""Writes a list of template names to the user directory.
	Raises FileExistsError for existing files if force == False."""
	root = discover_root(cli_root)
	map = get_template_map()
	for name in names:
		if name not in map:
			raise KeyError(f"{name} is not a valid template name.")
		map[name].write_with_root(root, force=force)


def write_all_templates(cli_root: Path | None, force: bool = False):
	"""Write all internal templates to the user directory.
	Raises FileExistsError for existing files if force == False."""
	root, resources = _get_templates(cli_root)
	for r in resources:
		r.write_with_root(root, force=force)


def list_templates() -> str:
	return "\n".join(get_template_map().keys())


# TODO: add a recent posts element that can be included elsewhere?
class Templater:
	def __init__(
		self,
		config: ZonaConfig,
		template_dir: Path,
		post_list: list[Item],
	):
		logger.debug("Initializing Templater.")
		# build temporary template dir
		self.env: Environment = Environment(
			loader=FileSystemLoader(template_dir),
			autoescape=select_autoescape(["html", "xml"]),
		)
		self.env.filters["format_time"] = format_time  # pyright: ignore[reportArgumentType]
		self.config: ZonaConfig = config
		self.template_dir: Path = template_dir
		self.post_list: list[Item] = post_list
		self.build_time: str = datetime.now(self.config.build.time.timezone).strftime(
			self.config.build.time.format
		)

		def render_footer() -> str:
			footer_name: str = self.config.build.footer_name
			template: Template = self.env.get_template(footer_name)
			rendered: str = template.render(build_time=self.build_time)
			if footer_name.endswith(".md"):
				return md_to_html(rendered, None)
			else:
				return rendered

		self.footer: str = render_footer()

	def render_header(self):
		template = self.env.get_template("header.html")
		return template.render(site_map=self.config.sitemap)

	def render_item(self, item: Item, content: str) -> str:
		logger.debug(f"Rendering {item.source}...")
		env = self.env
		meta = item.metadata
		assert meta is not None
		if meta.template is None:
			if item.post:
				template_name = "page.html"
			else:
				template_name = "basic.html"
		else:
			template_name = (
				meta.template
				if meta.template.endswith(".html")
				else meta.template + ".html"
			)
		template = env.get_template(template_name)
		header: str | Literal[False] = self.render_header() if meta.header else False
		return template.render(
			content=content,
			url=item.url,
			metadata=meta,
			header=header,
			readtime=item.readtime,
			footer=self.footer if meta.footer else False,
			is_post=item.post,
			newer=util.normalize_url(item.newer.url) if item.newer else None,
			older=util.normalize_url(item.older.url) if item.older else None,
			post_list=self.post_list,
			build_time=self.build_time,
		)
