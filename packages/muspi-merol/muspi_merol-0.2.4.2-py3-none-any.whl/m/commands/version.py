from typer import Typer

from ..utils.console import print_version

app = Typer()


@app.command()
def version():
    """Print the version of `m` and Python and quit."""

    print_version()
