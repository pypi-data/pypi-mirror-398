import xml.etree.ElementTree as etree
from collections.abc import Sequence
from logging import Logger
from typing import Any, override

from l2m4m import LaTeX2MathMLExtension
from markdown import Markdown
from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from markdown.extensions.sane_lists import SaneListExtension
from markdown.extensions.smarty import SmartyExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown.treeprocessors import Treeprocessor
from pygments.formatters.html import HtmlFormatter
from pymdownx.betterem import BetterEmExtension
from pymdownx.blocks.admonition import AdmonitionExtension
from pymdownx.caret import InsertSupExtension
from pymdownx.escapeall import EscapeAllExtension
from pymdownx.inlinehilite import InlineHiliteExtension
from pymdownx.smartsymbols import SmartSymbolsExtension
from pymdownx.striphtml import StripHtmlExtension
from pymdownx.superfences import SuperFencesCodeExtension
from pymdownx.tilde import DeleteSubExtension

from zona.config import ZonaConfig
from zona.log import get_logger
from zona.metadata import Metadata


class ZonaImageTreeprocessor(Treeprocessor):
	"""Implement Zona's image caption rendering."""

	def __init__(self, md: Markdown):
		super().__init__()
		self.md: Markdown = md
		self.logger: Logger = get_logger()

	@override
	def run(self, root: etree.Element):
		for parent in root.iter():
			for idx, child in enumerate(list(parent)):
				if child.tag == "p" and len(child) == 1 and child[0].tag == "img":
					img = child[0]
					div = etree.Element("div", {"class": "image-container"})
					div.append(img)
					title = img.attrib.get("alt", "")
					if title:
						raw_caption = self.md.convert(title)
						caption_html = raw_caption.strip()
						if caption_html.startswith("<p>") and caption_html.endswith(
							"</p>"
						):
							caption_html = caption_html[3:-4]
						caption = etree.Element("small")
						caption.text = ""  # should be rendered
						caption_html_element = etree.fromstring(
							f"<span>{caption_html}</span>"
						)
						caption.append(caption_html_element)
						div.append(caption)
					parent[idx] = div


def get_formatter(config: ZonaConfig) -> HtmlFormatter[Any]:
	c = config.markdown.syntax_highlighting
	formatter: HtmlFormatter[Any] = HtmlFormatter(
		style=c.theme, nowrap=not c.wrap, nobackground=True
	)
	return formatter


def md_to_html(
	content: str,
	config: ZonaConfig | None,
	metadata: Metadata | None = None,
) -> str:
	extensions: Sequence[Any] = [
		BetterEmExtension(),
		SuperFencesCodeExtension(
			disable_indented_code_blocks=True,
			css_class="codehilite",
		),
		FootnoteExtension(),
		AttrListExtension(),
		DefListExtension(),
		TocExtension(
			anchorlink=True,
		),
		TableExtension(),
		AbbrExtension(),
		SmartyExtension(),
		InsertSupExtension(),
		DeleteSubExtension(),
		SmartSymbolsExtension(),
		SaneListExtension(),
		MarkdownInHtmlExtension(),
		EscapeAllExtension(hardbreak=True),
		AdmonitionExtension(
			types=[
				"note",
				"warning",
				"danger",
				"tip",
				"important",
				"aside",
				"info",
				"thought",
				"meta",
				"rant",
				"quote",
				"example",
			]
		),
		StripHtmlExtension(),
	]
	kwargs: dict[str, Any] = {
		"extensions": extensions,
		"tab_length": 2,
	}
	if metadata and metadata.math:
		kwargs["extensions"].append(LaTeX2MathMLExtension())
	if config:
		kwargs["extensions"].extend(
			[
				CodeHiliteExtension(
					linenums=False,
					noclasses=False,
					pygments_style=config.markdown.syntax_highlighting.theme,
				),
				InlineHiliteExtension(css_class="codehilite"),
			]
		)
		kwargs["tab_length"] = config.markdown.tab_length
	md = Markdown(**kwargs)
	md.treeprocessors.register(
		item=ZonaImageTreeprocessor(md),
		name="zona_images",
		priority=17,
	)
	return md.convert(content)


def get_style_defs(config: ZonaConfig) -> str:
	formatter = get_formatter(config)
	defs = formatter.get_style_defs(".codehilite")  # pyright: ignore[reportUnknownVariableType]
	assert isinstance(defs, str)
	return defs
