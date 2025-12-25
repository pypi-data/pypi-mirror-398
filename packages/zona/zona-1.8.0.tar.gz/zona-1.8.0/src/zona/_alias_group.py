import re
from typing import Any, override

from click.core import Context
from typer.core import TyperGroup


class AliasGroup(TyperGroup):
	"""
	Helper for defining command aliases like this:
	    @app.command("a | action | xyz")
	    https://github.com/fastapi/typer/issues/132#issuecomment-2417492805
	"""

	_CMD_SPLIT_P: re.Pattern[str] = re.compile(r" ?[,|] ?")

	@override
	def get_command(self, ctx: Context, cmd_name: str | Any):
		cmd_name = self._group_cmd_name(cmd_name)
		return super().get_command(ctx, cmd_name)

	def _group_cmd_name(self, default_name: str | Any):
		for cmd in self.commands.values():
			name = cmd.name
			if name and default_name in self._CMD_SPLIT_P.split(name):
				return name
		return default_name
