from json import dumps
from pathlib import Path

from ..utils.helpers import UNSET, wrap_raw_config
from ..utils.merge import deep_merge
from ..utils.path import ensure_parents_exist, global_store, local_store
from .types import Config


def read_json_config(path: Path):
    if path.is_dir():
        path /= "config.json"
        if path.is_file():
            from json import loads

            return loads(path.read_bytes())

    return UNSET


def read_toml_config(path: Path):
    if path.is_dir():
        path /= "pyproject.toml"
        if path.is_file():
            from tomllib import loads

            return loads(path.read_text("utf-8")).get("tool", {}).get("m", {})

    return UNSET


def load_config():
    return wrap_raw_config(
        deep_merge(
            read_json_config(global_store),
            read_json_config(local_store),
            read_toml_config(Path.cwd()),
        )
    )


def write_json_config(path: Path, config: Config):
    path /= "config.json"
    ensure_parents_exist(path)
    path.write_text(dumps(config, indent=2, ensure_ascii=False), "utf-8")
