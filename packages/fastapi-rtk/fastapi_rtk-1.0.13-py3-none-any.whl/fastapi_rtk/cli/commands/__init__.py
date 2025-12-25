# Import every modules in this directory
import importlib
import pathlib
import pkgutil

import typer

from ...globals import g
from ...version import __version__


def version_callback(value: bool) -> None:
    if value:
        print(f"FastAPI-RTK CLI version: [green]{__version__}[/green]")
        raise typer.Exit()


def path_callback(value: pathlib.Path | None) -> None:
    g.path = value


for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    importlib.import_module(f"{__name__}.{module_name}")
