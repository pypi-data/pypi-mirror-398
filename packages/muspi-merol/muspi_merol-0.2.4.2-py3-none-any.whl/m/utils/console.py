from rich.console import Console

console = Console(highlight=False)


def print_version():
    from platform import python_implementation, python_version

    from ..version import __version__

    console.print(f"\n [r] m [/] {__version__}", end=" ", style="violet")
    console.print(python_implementation(), python_version(), style="dim", end="\n\n")
