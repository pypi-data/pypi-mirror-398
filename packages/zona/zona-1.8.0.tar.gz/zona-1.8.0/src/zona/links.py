from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urldefrag

from zona import util
from zona.config import ZonaConfig
from zona.issues import warnings
from zona.layout import Layout
from zona.lazy_regex import email, likely_external
from zona.log import get_logger
from zona.models import Item

logger = get_logger()


@dataclass
class ZonaLink:
	href: str = ""
	target: str | None = None


def handle_external_link(
	link: ZonaLink,
	config: ZonaConfig | None,
	source: Path,
):
	if config and config.markdown.links.external_new_tab:
		logger.trace(f"Likely external link: {link.href} in file {source}")
		link.target = "_blank"
		return link
	else:
		return link


def resolve_link(
	href: str,
	source: Path,
	config: ZonaConfig | None,
	layout: Layout,
	item_map: dict[Path, Item],
) -> ZonaLink:
	"""Attempts to resolve an internal link."""
	link = ZonaLink(href)
	source = source.resolve()
	href_ = href
	resolved = Path()
	if href.startswith(("https://", "http://")):
		return handle_external_link(link, config, source)
	# strip anchor from href
	href, frag = urldefrag(href)
	if frag and not href:
		link.href = f"#{frag}"
		logger.trace(f"Resolved self-anchor found in {source}: {link.href}")
		return link

	cur = Path(href)
	# resolve relative to content root
	if href.startswith("/"):
		resolved = (layout.content / cur.relative_to("/")).resolve()
	# treat as relative link and try to resolve
	else:
		resolved = (source.parent / cur).resolve()
	# check if link is real
	real = False
	for suffix in {".md", ".html"}:
		if resolved.with_suffix(suffix).exists():
			real = True
			resolved = resolved.with_suffix(suffix)
			break
	if not real:
		if not bool(likely_external().match(href)):
			# check if matching email
			m = email().match(href)
			if m:
				if not m.group(1):
					warnings(
						f"Link {href} is likely an email, but is missing the mailto: prefix"
					)
			else:
				warnings(
					f"Link {link.href} in file {source} points to a file that doesn't exist"
				)
		link = handle_external_link(link, config, source)
		return link

	# only substitute if link points to actual file
	# that isn't the self file
	item = item_map.get(resolved)
	if item:
		href = util.normalize_url(item.url)
		# don't sub if it's already correct
		if href_ != href:
			link.href = f"{href}#{frag}" if frag else href
			logger.debug(f"Link in file {source}: {href_} resolved to {link.href}")
	else:
		# TODO: fix incorrect warning for links /foobar
		# where content/foobar.md exists
		warnings(
			f"File {source}: resolved path {resolved} from link {href_} exists but not found in item map"
		)
	return link
