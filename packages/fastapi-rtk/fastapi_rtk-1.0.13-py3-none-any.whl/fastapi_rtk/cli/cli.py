import io
import typing
import zipfile
from pathlib import Path
from typing import Annotated, Union

import httpx
import typer

app = typer.Typer(rich_markup_mode="rich")
from .commands import path_callback, version_callback  # noqa: E402


@app.callback()
def callback(
    version: Annotated[
        Union[bool, None],
        typer.Option(
            "--version", help="Show the version and exit.", callback=version_callback
        ),
    ] = None,
    path: Annotated[
        Union[Path, None],
        typer.Option(
            help="A path to a Python file or package directory (with [blue]__init__.py[/blue] files) containing a [bold]FastAPI[/bold] app. If not provided, a default set of paths will be tried.",
            callback=path_callback,
        ),
    ] = None,
) -> None:
    """
    FastAPI RTK CLI - The [bold]fastapi-rtk[/bold] command line app. 😎

    Manage your [bold]FastAPI React Toolkit[/bold] projects.
    """


@app.command()
def create_app(
    directory: typing.Annotated[
        str,
        typer.Option(
            ...,
            help="The directory where the new FastAPI RTK application will be created.",
        ),
    ] = ".",
):
    """
    Create a new FastAPI RTK application with a predefined structure from https://codeberg.org/datatactics/fastapi-rtk-skeleton.

    This command sets up the necessary files and directories for a FastAPI RTK project,
    allowing you to get started quickly with development.
    """
    with httpx.Client() as client:
        url = "https://codeberg.org/datatactics/fastapi-rtk-skeleton/archive/main.zip"
        response = client.get(url)
        response.raise_for_status()

        # Unzip the content into the specified directory
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Get all members (files/folders) in the zip
            members = zip_ref.namelist()

            # Find the top-level directory name
            top_level_dir = members[0].split("/")[0] + "/"

            # Extract each file, stripping the top-level directory
            for member in members:
                # Skip the top-level directory itself
                if member == top_level_dir:
                    continue

                # Get the path without the top-level directory
                target_path = member[len(top_level_dir) :]

                # Skip if empty (this was the root folder)
                if not target_path:
                    continue

                # Get the source file
                source = zip_ref.open(member)
                target_file = Path(directory) / target_path

                # Create directories if needed
                if member.endswith("/"):
                    target_file.mkdir(parents=True, exist_ok=True)
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_file, "wb") as f:
                        f.write(source.read())

            typer.echo(f"FastAPI RTK application skeleton created in {directory}")


def main():
    app()
