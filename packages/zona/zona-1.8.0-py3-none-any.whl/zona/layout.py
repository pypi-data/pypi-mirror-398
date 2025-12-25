from dataclasses import asdict, dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import typer
import yaml

from zona import log, util
from zona.config import ZonaConfig, find_config

logger = log.get_logger()


@dataclass
class Layout:
	root: Path
	content: Path
	templates: Path
	output: Path
	shared_templates: util.TempDir | None
	_validate: bool
	has_user_templates: bool = False

	def refresh(self):
		logger.debug("Refreshing layout...")
		if self.shared_templates and not self.shared_templates.removed:
			logger.debug("Removing stale templates tempdir...")
			self.shared_templates.remove()
		return self.__class__.from_input(
			root=self.root,
			output=self.output,
			validate=self._validate,
		)

	@classmethod
	def from_input(
		cls,
		root: Path,
		output: Path | None = None,
		validate: bool = True,
	) -> "Layout":
		layout = cls(
			root=root.resolve(),
			content=(root / "content").resolve(),
			templates=(root / "templates").resolve(),
			output=(root / "public").resolve() if not output else output,
			shared_templates=None,
			_validate=validate,
		)
		if validate:
			logger.debug("Validating site layout...")
			if not layout.content.is_dir():
				logger.error("Missing required content directory!")
				raise FileNotFoundError("Missing required content directory!")
			internal_templates = util.get_resource_dir("templates")
			user_templates = layout.templates
			if not user_templates.is_dir() or util.is_empty(user_templates):
				logger.debug("Using default template directory.")
				# use the included defaults
				layout.templates = internal_templates
			else:
				layout.has_user_templates = True
				seen: set[str] = set()
				temp = util.TempDir()
				logger.debug(f"Creating shared template directory at {temp}")
				for f in user_templates.iterdir():
					if f.is_file():
						util.copy_static_file(f, temp.path)
						seen.add(f.name)
				for f in internal_templates.iterdir():
					if f.is_file() and f.name not in seen:
						util.copy_static_file(f, temp.path)
				layout.shared_templates = temp
				layout.templates = temp.path

		return layout


def discover_root(cli_root: Path | None) -> Path:
	if cli_root:
		logger.debug("Using user provided site root.")
		root = cli_root
	else:
		logger.debug("Discovering site layout...")
		config = find_config(cli_root)
		if config:
			root = config.parent
		else:
			logger.debug("Using CWD as root.")
			root = Path.cwd()
	logger.debug(f"Determined {root} to be project root.")
	log.set_logger_prefix(logger, root)
	return root


def discover_layout(
	cli_root: Path | None = None, cli_output: Path | None = None
) -> Layout:
	root = discover_root(cli_root)
	return Layout.from_input(root, cli_output)


def initialize_site(root: Path | None = None):
	logger.info("Initializing site.")
	# initialize a new project
	if not root:
		logger.debug("No root provided; using CWD.")
		root = Path.cwd()
	root = root.absolute().resolve()
	config = find_config(root)
	if config is not None:
		ans = typer.confirm(
			text=(
				f"A config file already exists at {config}.\n"
				f"Delete it and restore defaults?"
			)
		)
		if ans:
			logger.debug("Unlinking config file.")
			config.unlink()
	# create requires layout
	logger.debug("Generating layout.")
	layout = Layout.from_input(root=root, validate=False)
	# load template resources
	logger.debug("Loading internal templates.")
	# only write the footer
	templates = [util.get_resource("templates/footer.md")]
	logger.debug("Loading internal static content.")
	static = util.get_resources("content")
	for dir, resources in [
		(layout.root, None),
		(layout.content, static),
		(layout.templates, templates),
	]:
		if not dir.is_dir():
			logger.debug(f"Creating {dir}.")
			dir.mkdir()
		if resources is not None:
			logger.debug("Writing resources.")
			for r in resources:
				dest = root / Path(r.name)
				util.ensure_parents(dest)
				logger.debug(f"Writing {dest}.")
				dest.write_text(r.contents)

	config_path = layout.root / "config.yml"
	logger.debug("Loading default configuation.")
	config = ZonaConfig()
	logger.debug(f"Writing default configuration to {config_path}.")
	config_dict = asdict(config)
	if "feed" in config_dict and "timezone" in config_dict["feed"]:
		tz: ZoneInfo = config_dict["feed"]["timezone"]
		config_dict["feed"]["timezone"] = tz.key
	with open(config_path, "w") as f:
		yaml.dump(
			config_dict,
			f,
			sort_keys=False,
			default_flow_style=False,
			indent=2,
		)
