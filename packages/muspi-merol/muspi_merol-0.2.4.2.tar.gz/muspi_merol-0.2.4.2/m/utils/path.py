from pathlib import Path

local_store = Path(__file__, "../../.store").resolve()  # in the namespace package root
global_store = Path.home() / ".m"  # in the user's home directory


def ensure_parents_exist(path: Path):
    for parent in path.parents:
        if parent.is_dir():
            break
        elif parent.is_file():
            raise FileExistsError(f"{parent} is a file, not a directory")

        parent.mkdir(exist_ok=True)
