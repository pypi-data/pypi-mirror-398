from typing import cast

from .helpers import UNSET, Unset


def deep_merge[T: (list, dict, str, bool, int, float, None)](*values: T | Unset) -> T | Unset:
    it = iter(values)

    result: T | Unset = UNSET

    for i in it:
        if i is UNSET:
            continue

        if result is UNSET:
            result = i.copy() if isinstance(i, list | dict) else i
            continue

        if isinstance(i, list):
            cast(list, result).extend(i)
        elif isinstance(i, dict):
            r: dict = result  # type: ignore
            for k, v in i.items():
                if k in r:
                    r_k = r[k]
                    if isinstance(r_k, list) and isinstance(v, list):
                        r[k] = r_k + v
                    elif isinstance(r_k, dict) and isinstance(v, dict):
                        r[k] = r_k | v
                    else:
                        r[k] = v
                else:
                    r[k] = v
        else:
            result = i

    return result
