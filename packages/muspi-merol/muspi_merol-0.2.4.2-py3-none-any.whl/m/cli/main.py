from typer import Typer

from ..utils.register import get_commands
from . import config

app = Typer(
    help="CLI utilities for personal use",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


# load other commands

for sub_app in get_commands():
    if sub_app.info.name:
        app.add_typer(sub_app)
    else:
        app.registered_commands.extend(sub_app.registered_commands)


# load aliases

for alias, item in config["aliases"].items():
    app.command(name=alias, help=f"[dim]alias of[/] {item if isinstance(item, str) else item['cmd']!r}")(lambda: 0)  # fake
