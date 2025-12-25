import shutil
import time
from datetime import date
from pathlib import Path

import readtime
import typer
from feedgen.feed import FeedGenerator
from rich import print

from zona import markdown as zmd
from zona import util
from zona.config import ZonaConfig
from zona.html import apply_link_resolution
from zona.issues import errors, warnings
from zona.layout import Layout, discover_layout
from zona.log import get_logger
from zona.metadata import parse_metadata
from zona.models import Item, ItemType, ReadTime
from zona.templates import Templater

logger = get_logger()


class ZonaBuilder:
	def __init__(
		self,
		cli_root: Path | None = None,
		cli_output: Path | None = None,
		draft: bool = False,
		strict: bool = False,
	):
		logger.debug("Initializing Builder...")
		self.layout: Layout = discover_layout(cli_root, cli_output)
		self.config: ZonaConfig = ZonaConfig.from_file(self.layout.root / "config.yml")
		if draft:
			self.config.build.include_drafts = True
		self.items: list[Item] = []
		self.item_map: dict[Path, Item] = {}
		self.fresh: bool = True
		self.post_list: list[Item] = []
		self.building: bool = False
		self.strict: bool = strict

	def __bool__(self) -> bool:
		return self.building

	def _discover(self):
		layout = self.layout
		items: list[Item] = []

		base = layout.root / layout.content
		logger.debug(f"Discovering content in {base}.")
		for path in base.rglob("*"):
			item = self._item_from_path(path)
			if item:
				items.append(item)
		self.items = items

	def generate_feed(self) -> bytes:
		post_list = self._get_post_list()
		config = self.config.feed
		logger.debug("Processing RSS config.")
		if config.link.endswith("/"):
			config.link = config.link[:-2]
		fg = FeedGenerator()
		fg.id(config.link)
		fg.title(config.title)
		author = {
			"name": config.author.name,
			"email": config.author.email,
		}
		fg.author(author)
		fg.link(
			href=f"{config.link}/{config.path}",
			rel="self",
			type="application/rss+xml",
		)
		fg.language(config.language)
		fg.description(config.description)

		logger.debug("Generating RSS entries for posts...")
		for post in post_list:
			assert post.metadata
			fe = fg.add_entry()  # pyright: ignore[reportUnknownVariableType]
			fe.id(f"{config.link}{util.normalize_url(post.url)}")  # pyright: ignore[reportUnknownMemberType]
			fe.link(  # pyright: ignore[reportUnknownMemberType]
				href=f"{config.link}{util.normalize_url(post.url)}"
			)
			fe.title(post.metadata.title)  # pyright: ignore[reportUnknownMemberType]
			fe.author(author)  # pyright: ignore[reportUnknownMemberType]
			desc = post.metadata.description
			fe.description(desc)  # pyright: ignore[reportUnknownMemberType]
			date = post.metadata.date
			fe.pubDate(date)  # pyright: ignore[reportUnknownMemberType]
		out: bytes = fg.rss_str(pretty=True)
		assert isinstance(out, bytes)
		return out

	def _get_post_list(self) -> list[Item]:
		if not self.post_list:
			# sort according to date
			# descending order
			logger.debug("Generating post list...")
			self.post_list = sorted(
				[item for item in self.items if item.post],
				key=lambda item: item.metadata.date if item.metadata else date.min,
				reverse=True,
			)
		return self.post_list

	def _process_html(self, html: str, source: Path) -> str:
		logger.debug(f"Post-processing {source}")
		out = apply_link_resolution(
			html_str=html,
			source=source,
			config=self.config,
			layout=self.layout,
			item_map=self.item_map,
		)
		return out

	def _item_from_path(self, path: Path) -> Item | None:
		base = self.layout.root / self.layout.content
		path = path.resolve()
		if not path.is_file():
			return None
		if not path.is_relative_to(base):
			return None
		if util.should_ignore(path, patterns=self.config.ignore, base=base):
			return None
		destination = self.layout.output / path.relative_to(base)
		item = Item(
			source=path,
			destination=destination,
			url=str(destination.relative_to(self.layout.output)),
		)
		if path.name.endswith(".md") and not path.is_relative_to(
			self.layout.root / "content" / "static"
		):
			logger.debug(f"Pre-processing {path}.")
			item.metadata, item.content = parse_metadata(path, config=self.config)
			if item.metadata.ignore or (
				item.metadata.draft and not self.config.build.include_drafts
			):
				return None
			if item.metadata.post:
				item.post = True
			elif item.metadata.post is None:
				blog_dir = base / Path(self.config.blog.dir)
				if item.source.is_relative_to(blog_dir):
					item.post = True
			item.type = ItemType.MARKDOWN
			item.copy = False
			name = destination.stem
			if name == "index":
				item.destination = item.destination.with_suffix(".html")
			else:
				relative = path.relative_to(base).with_suffix("")
				name = relative.stem
				item.destination = (
					self.layout.output / relative.parent / name / "index.html"
				)
			rel_url = item.destination.parent.relative_to(self.layout.output)
			item.url = "" if rel_url == Path(".") else rel_url.as_posix()
		return item

	def _link_posts(self, post_list: list[Item]) -> None:
		posts = len(post_list)
		logger.debug("Linking posts chronologically...")
		for i, item in enumerate(post_list):
			older = post_list[i + 1] if i + 1 < posts else None
			newer = post_list[i - 1] if i > 0 else None
			item.older = older
			item.newer = newer

	def _render_markdown_items(
		self,
		items: list[Item],
		templater: Templater,
	) -> None:
		for item in items:
			if item.type != ItemType.MARKDOWN:
				continue
			assert item.content is not None
			raw_html = zmd.md_to_html(
				config=self.config,
				content=item.content,
				metadata=item.metadata,
			)
			res = readtime.of_markdown(item.content)
			min, sec = res.minutes, res.seconds
			item.readtime = ReadTime(minutes=min, seconds=sec)
			html = self._process_html(raw_html, item.source)
			rendered = templater.render_item(item, html)
			util.ensure_parents(item.destination)
			item.destination.write_text(rendered, encoding="utf-8")

	def _build(self):
		post_list = self._get_post_list()
		self._link_posts(post_list)

		templater = Templater(
			config=self.config,
			template_dir=self.layout.templates,
			post_list=post_list,
		)
		logger.debug("Building item path: Item map.")
		self.item_map = {item.source.resolve(): item for item in self.items}

		# write code highlighting stylesheet
		if self.config.markdown.syntax_highlighting.enabled:
			pygments_style = zmd.get_style_defs(self.config)
			pygments_path = self.layout.output / "static" / "pygments.css"
			util.ensure_parents(pygments_path)
			pygments_path.write_text(pygments_style)
		markdown_items: list[Item] = []
		for item in self.item_map.values():
			if item.type == ItemType.MARKDOWN:
				markdown_items.append(item)
			elif item.copy:
				util.copy_static_file(item.source, item.destination)
		self._render_markdown_items(markdown_items, templater)

	def rebuild(
		self,
		changed: set[Path],
		deleted: set[Path],
		added: set[Path],
	):
		if self.fresh:
			self.build(self.strict)
			return

		self.building = True
		with warnings, errors:
			start_time = time.time()
			logger.info("Rebuilding...")
			post_list_dirty = False
			render_all_markdown = False

			for path in deleted:
				resolved = path.resolve()
				item = self.item_map.pop(resolved, None)
				if item:
					if item.post:
						post_list_dirty = True
					if item.destination.exists():
						item.destination.unlink()

			items_to_render: list[Item] = []
			for path in changed | added:
				resolved = path.resolve()
				old_item = self.item_map.get(resolved)
				new_item = self._item_from_path(path)
				if new_item is None:
					if old_item:
						self.item_map.pop(resolved, None)
						if old_item.post:
							post_list_dirty = True
						if old_item.destination.exists():
							old_item.destination.unlink()
					continue

				if old_item:
					if old_item.post or new_item.post:
						if old_item.post != new_item.post:
							post_list_dirty = True
						elif old_item.metadata != new_item.metadata:
							post_list_dirty = True
				else:
					if new_item.post:
						post_list_dirty = True
				self.item_map[resolved] = new_item

				if new_item.type == ItemType.MARKDOWN:
					items_to_render.append(new_item)
				else:
					if new_item.copy:
						util.copy_static_file(new_item.source, new_item.destination)

			self.items = list(self.item_map.values())

			if post_list_dirty:
				self.post_list.clear()
				post_list = self._get_post_list()
				self._link_posts(post_list)
				render_all_markdown = True
			else:
				post_list = self._get_post_list()

			if render_all_markdown:
				items_to_render = [
					item
					for item in self.item_map.values()
					if item.type == ItemType.MARKDOWN
				]

			if items_to_render:
				templater = Templater(
					config=self.config,
					template_dir=self.layout.templates,
					post_list=post_list,
				)
				self._render_markdown_items(items_to_render, templater)

			if self.config.feed.enabled and post_list_dirty:
				logger.info("Generating RSS feed...")
				rss = self.generate_feed()
				path = self.layout.output / self.config.feed.path
				util.ensure_parents(path)
				logger.debug(f"Writing RSS feed to {path}...")
				path.write_bytes(rss)

			end_time = time.time()
			duration = (end_time - start_time) * 1000

		print(f"Rebuild took {duration:.1f}ms.")
		if warnings or errors:
			print(
				f"{'Failed due to' if self.strict else 'Generated'} {len(warnings)} warning(s) and {len(errors)} error(s)."
			)
			if self.strict or errors:
				raise typer.Exit(1)
		self.building = False

	def build(self, strict: bool = False, _fake_wait: bool = False):
		if strict:
			self.strict = True
		if _fake_wait:
			from time import sleep

			sleep(3)
		if not self.fresh:
			# remove stale post list
			self.post_list.clear()
		self.building = True
		with warnings, errors:
			start_time = time.time()
			logger.info("Initiating build process...")
			# clean output if applicable
			if self.config.build.clean_output_dir and self.layout.output.is_dir():
				logger.debug(
					f"Found stale output in {self.layout.output}, cleaning up..."
				)
				# only remove output dir's children
				# to avoid breaking live preview
				for child in self.layout.output.iterdir():
					if child.is_file() or child.is_symlink():
						child.unlink()
					elif child.is_dir():
						shutil.rmtree(child)
			if not self.fresh:
				self.layout = self.layout.refresh()
			logger.info("Discovering site content...")
			self._discover()
			logger.info("Building site...")
			self._build()
			if self.config.feed.enabled:
				logger.info("Generating RSS feed...")
				rss = self.generate_feed()
				path = self.layout.output / self.config.feed.path
				util.ensure_parents(path)
				logger.debug(f"Writing RSS feed to {path}...")
				path.write_bytes(rss)
			end_time = time.time()
			duration = (end_time - start_time) * 1000

		print(f"{'Build' if self.fresh else 'Rebuild'} took {duration:.1f}ms.")
		if warnings or errors:
			print(
				f"{'Failed due to' if self.strict else 'Generated'} {len(warnings)} warning(s) and {len(errors)} error(s)."
			)
			if self.strict or errors:
				raise typer.Exit(1)
		self.fresh = False
		self.building = False
