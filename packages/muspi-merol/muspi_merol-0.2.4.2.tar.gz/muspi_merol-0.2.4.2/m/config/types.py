from typing import NotRequired, TypedDict


class Alias(TypedDict):
    cmd: str
    shell: bool
    env: NotRequired[dict[str, str]]


class Config(TypedDict):
    aliases: dict[str, Alias | str]
