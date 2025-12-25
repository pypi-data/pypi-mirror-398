from pathlib import Path

from lxml.etree import ParserError
from lxml.html import fromstring, tostring

from zona.config import ZonaConfig
from zona.layout import Layout
from zona.links import resolve_link
from zona.models import Item


def apply_link_resolution(
	html_str: str,
	source: Path,
	config: ZonaConfig | None,
	layout: Layout,
	item_map: dict[Path, Item],
) -> str:
	try:
		tree = fromstring(html_str)
	except ParserError:
		return html_str
	for a in tree.iter("a"):
		href = a.get("href")
		if href:
			resolved = resolve_link(href, source, config, layout, item_map)
			a.set("href", resolved.href)
			if resolved.target:
				a.set("target", resolved.target)
	return tostring(tree, encoding="unicode", method="html")
