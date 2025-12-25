import os
from typing import Annotated, Union

import alembic
import alembic.command
import alembic.config
import typer

from ...cli import app
from ...decorators import ensure_fastapi_rtk_tables_exist
from .. import version_callback


class Config(alembic.config.Config):
    def __init__(self, *args, **kwargs):
        self.template_directory = kwargs.pop("template_directory", None)
        super().__init__(*args, **kwargs)

    def get_template_directory(self):
        if self.template_directory:
            return self.template_directory
        package_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(package_dir, "templates")


db_app = typer.Typer(rich_markup_mode="rich")
app.add_typer(db_app, name="db")


@db_app.callback()
@ensure_fastapi_rtk_tables_exist
def callback(
    version: Annotated[
        Union[bool, None],
        typer.Option(
            "--version", help="Show the version and exit.", callback=version_callback
        ),
    ] = None,
) -> None:
    """
    FastAPI RTK Database CLI - The [bold]fastapi-rtk db[/bold] command line app. 😎

    Manage your [bold]FastAPI React Toolkit[/bold] databases easily with init, migrate, upgrade, with the power of Alembic.
    """


@db_app.command()
def list_templates():
    """List available templates."""
    config = Config()
    config.print_stdout("Available templates:\n")
    for tempname in sorted(os.listdir(config.get_template_directory())):
        with open(
            os.path.join(config.get_template_directory(), tempname, "README")
        ) as readme:
            synopsis = next(readme).strip()
        config.print_stdout("%s - %s", tempname, synopsis)


@db_app.command()
def init(
    directory: Annotated[
        Union[str, None],
        typer.Option(
            help="A path to a directory where the migration scripts will be stored."
        ),
    ] = "migrations",
    multidb: Annotated[
        bool,
        typer.Option(
            help="Whether multiple databases are being used.",
        ),
    ] = False,
    template: Annotated[
        Union[str, None],
        typer.Option(
            help="Template to use when creating the migration scripts.",
        ),
    ] = "fastapi",
    package: Annotated[
        bool,
        typer.Option(
            help="Whether to include a `__init__.py` file in the migration directory.",
        ),
    ] = False,
):
    """Creates a new migration repository"""
    template_directory = None
    if "/" in template or "\\" in template:
        template_directory, template = os.path.split(template)
    config = Config(template_directory=template_directory)
    config.set_main_option("script_location", directory)
    config.config_file_name = os.path.join(directory, "alembic.ini")
    # TODO: Fix this
    # config = current_app.extensions["migrate"].migrate.call_configure_callbacks(config)
    if multidb and template == "fastapi":
        template = "fastapi-multidb"
    alembic.command.init(config, directory, template=template, package=package)


@db_app.command()
def revision(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    message: Annotated[
        str, typer.Option(help="String message to apply to the revision.")
    ] = "",
    autogenerate: Annotated[
        bool,
        typer.Option(
            help="Whether or not to autogenerate the script from the database."
        ),
    ] = False,
    sql: Annotated[
        bool,
        typer.Option(
            help="Whether to dump the script out as a SQL string; when specified, the script is dumped to stdout."
        ),
    ] = False,
    head: Annotated[
        str,
        typer.Option(help="Head revision to build the new revision upon as a parent."),
    ] = "head",
    splice: Annotated[
        bool,
        typer.Option(
            help="Whether or not the new revision should be made into a new head of its own; is required when the given ``head`` is not itself a head"
        ),
    ] = False,
    branch_label: Annotated[
        Union[str, None],
        typer.Option(
            help="String label to apply to the branch.",
        ),
    ] = None,
    version_path: Annotated[
        Union[str, None],
        typer.Option(
            help="String symbol identifying a specific version path from the configuration.",
        ),
    ] = None,
    rev_id: Annotated[
        Union[str, None],
        typer.Option(
            help="Optional revision identifier to use instead of having one generated.",
        ),
    ] = None,
):
    """Create a new revision file."""
    opts = ["autogenerate"] if autogenerate else None
    config = Config()
    config.set_main_option("script_location", directory)
    config.cmd_opts = opts
    # config = current_app.extensions["migrate"].migrate.get_config(directory, opts=opts)
    alembic.command.revision(
        config,
        message,
        autogenerate=autogenerate,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id,
    )


@db_app.command()
def migrate(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    message: Annotated[
        str, typer.Option(help="String message to apply to the revision.")
    ] = "",
    sql: Annotated[
        bool,
        typer.Option(
            help="Whether to dump the script out as a SQL string; when specified, the script is dumped to stdout."
        ),
    ] = False,
    head: Annotated[
        str,
        typer.Option(help="Head revision to build the new revision upon as a parent."),
    ] = "head",
    splice: Annotated[
        bool,
        typer.Option(
            help="Whether or not the new revision should be made into a new head of its own; is required when the given ``head`` is not itself a head"
        ),
    ] = False,
    branch_label: Annotated[
        Union[str, None],
        typer.Option(
            help="String label to apply to the branch.",
        ),
    ] = None,
    version_path: Annotated[
        Union[str, None],
        typer.Option(
            help="String symbol identifying a specific version path from the configuration.",
        ),
    ] = None,
    rev_id: Annotated[
        Union[str, None],
        typer.Option(
            help="Optional revision identifier to use instead of having one generated.",
        ),
    ] = None,
):
    """Alias for `revision` command with --autogenerate."""
    return revision(
        directory=directory,
        message=message,
        autogenerate=True,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id,
    )


@db_app.command()
def edit(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    revision: Annotated[
        str, typer.Option(help="Revision identifier to edit.")
    ] = "current",
):
    """Edit the revision."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.edit(config, revision)


@db_app.command()
def merge(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    revisions: Annotated[str, typer.Option(help="Revisions to merge.")] = "",
    message: Annotated[
        Union[str, None], typer.Option(help="String message to apply to the revision.")
    ] = None,
    branch_label: Annotated[
        Union[str, None],
        typer.Option(
            help="String label to apply to the branch.",
        ),
    ] = None,
    rev_id: Annotated[
        Union[str, None],
        typer.Option(
            help="Optional revision identifier to use instead of having one generated.",
        ),
    ] = None,
):
    """Merge two revisions together."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.merge(
        config,
        revisions,
        message=message,
        branch_label=branch_label,
        rev_id=rev_id,
    )


@db_app.command()
def upgrade(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    revision: Annotated[
        str, typer.Option(help="Target revision to upgrade to.")
    ] = "head",
    sql: Annotated[
        bool,
        typer.Option(
            help="Whether to dump the script out as a SQL string; when specified, the script is dumped to stdout."
        ),
    ] = False,
    tag: Annotated[
        Union[str, None],
        typer.Option(
            help="Arbitrary 'tag' name to apply to the migration.",
        ),
    ] = None,
):
    """Upgrade to a later version."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.upgrade(config, revision, sql=sql, tag=tag)


@db_app.command()
def downgrade(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    revision: Annotated[
        str, typer.Option(help="Target revision to downgrade to.")
    ] = "-1",
    sql: Annotated[
        bool,
        typer.Option(
            help="Whether to dump the script out as a SQL string; when specified, the script is dumped to stdout."
        ),
    ] = False,
    tag: Annotated[
        Union[str, None],
        typer.Option(
            help="Arbitrary 'tag' name to apply to the migration.",
        ),
    ] = None,
):
    """Downgrade to a previous version."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.downgrade(config, revision, sql=sql, tag=tag)


@db_app.command()
def show(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    revision: Annotated[str, typer.Option(help="Target revision to show.")] = "head",
):
    """Show the revision."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.show(config, revision)


@db_app.command()
def history(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    rev_range: Annotated[
        str, typer.Option(help="Range of revisions to include in the history.")
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            help="Show the full revision message.",
        ),
    ] = False,
    indicate_current: Annotated[
        bool,
        typer.Option(
            help="Indicate the current revision.",
        ),
    ] = False,
):
    """List changeset scripts in chronological order."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.history(
        config, rev_range, verbose=verbose, indicate_current=indicate_current
    )


@db_app.command()
def heads(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    verbose: Annotated[
        bool,
        typer.Option(
            help="Show the full revision message.",
        ),
    ] = False,
    resolve_dependencies: Annotated[
        bool,
        typer.Option(
            help="Treat dependency version as down revisions.",
        ),
    ] = False,
):
    """Show current available heads in the script directory."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.heads(
        config, verbose=verbose, resolve_dependencies=resolve_dependencies
    )


@db_app.command()
def branches(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    verbose: Annotated[
        bool,
        typer.Option(
            help="Show the full revision message.",
        ),
    ] = False,
):
    """Show current branch points in the script directory."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.branches(config, verbose=verbose)


@db_app.command()
def current(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    verbose: Annotated[
        bool,
        typer.Option(
            help="Show the full revision message.",
        ),
    ] = False,
):
    """Display the current revision for each database."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.current(config, verbose=verbose)


@db_app.command()
def stamp(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
    revision: Annotated[str, typer.Option(help="Target revision to stamp.")] = "head",
    sql: Annotated[
        bool,
        typer.Option(
            help="Whether to dump the script out as a SQL string; when specified, the script is dumped to stdout."
        ),
    ] = False,
    tag: Annotated[
        Union[str, None],
        typer.Option(
            help="Arbitrary 'tag' name to apply to the migration.",
        ),
    ] = None,
    purge: Annotated[
        bool,
        typer.Option(
            help="Remove all database tables and then stamp.",
        ),
    ] = False,
):
    """Stamp the revision table with the given revision."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.stamp(config, revision, sql=sql, tag=tag, purge=purge)


@db_app.command()
def check(
    directory: Annotated[
        Union[str, None], typer.Option(help="Path to migration scripts directory.")
    ] = "migrations",
):
    """Check the current revision."""
    config = Config()
    config.set_main_option("script_location", directory)
    alembic.command.check(config)
