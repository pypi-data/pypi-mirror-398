from sys import argv

from ..utils.cmd import get_runner
from ..utils.console import print_version
from ..utils.inject import restart_in_venv_if_needed

if len(arg := argv[1:]) == 1 and arg[0] in {"-v", "--version"}:
    print_version()
    exit()  # early exit


from ..config.load import load_config

config = load_config()

if len(argv) > 1:
    for alias, item in config["aliases"].items():
        if argv[1] == alias:
            get_runner(item)()
            # early exit

restart_in_venv_if_needed()
