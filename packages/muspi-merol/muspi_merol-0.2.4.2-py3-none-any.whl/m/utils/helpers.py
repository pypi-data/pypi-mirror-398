from ..config.types import Config


class Unset:
    def __bool__(self):
        return False

    def __getitem__(self, _):
        return self

    def get(self, _, default=None):
        return default

    def items(self):
        return iter(())

    def __repr__(self):
        return "UNSET"


UNSET = Unset()


def _wrap(value):
    if isinstance(value, list):
        return ListWrapper(value)
    if isinstance(value, dict):
        return DictWrapper(value)
    return value


class ListWrapper(list):
    def __getitem__(self, index):  # type: ignore
        try:
            return _wrap(super().__getitem__(index))
        except IndexError:
            return UNSET


class DictWrapper(dict):
    def __getitem__(self, key):
        try:
            return _wrap(super().__getitem__(key))
        except KeyError:
            return UNSET


def wrap_raw_config(data: dict | Unset) -> Config:
    return DictWrapper(data if isinstance(data, dict) else {})  # type: ignore
