from ast import literal_eval
from contextlib import suppress

from m.utils.console import console
from rich import print_json
from typer import Exit, Typer, launch
from typer.params import Argument, Option

from ..config.load import load_config, read_json_config, write_json_config
from ..utils.helpers import UNSET, wrap_raw_config
from ..utils.path import global_store, local_store

app = Typer()


@app.command(help="Manage configuration.")
def config(
    item: str = Argument("", help="The item to retrieve from the config. Leave empty to retrieve the entire config."),
    value: str = Argument("", help="The value to set the item to. Leave empty to retrieve the item."),
    globally: bool = Option(False, "--global", "-g", help="Persistent config in User's home directory instead of this python venv.", show_default=False),
    open_config_file: bool = Option(False, "--open", "-o", help="Open the config file in the default editor."),
):
    store = global_store if globally else local_store
    if open_config_file:
        code = launch(path := str(store / "config.json"))
        if code:
            console.print(f"\n :warning: Failed to open {path}", style="red", end="\n\n")
        raise Exit(code)
    config = wrap_raw_config(read_json_config(store)) if value or globally else load_config()  # merge unless the value is set or global config is requested

    match (item, value):
        case ("", ""):
            print_json(data=dict(config))
        case (item, ""):
            for item in item.split("."):
                if isinstance(config, dict):
                    config = config[item]
                elif isinstance(config, list):
                    config = config[int(item)]
                else:
                    break

            if config is not UNSET:
                print_json(data=config)

        case (item, value):
            new_config: dict = dict(config) if isinstance(config, dict) else {}

            obj = new_config
            parts = item.split(".")
            for part in parts[:-1]:
                if isinstance(obj, dict):
                    obj = obj.setdefault(part, {})
                elif isinstance(obj, list):
                    obj = obj[int(part)]
                else:
                    raise ValueError(f"Invalid config path: {item} on {part}: {obj}")

            with suppress(TypeError, ValueError, SyntaxError):
                value = literal_eval(value)

            if not isinstance(obj, dict):
                console.print(f"Mutating on `{obj}` is not supported yet.", style="red")
                raise Exit(1)

            obj[parts[-1]] = value

            write_json_config(store, new_config)  # type: ignore
