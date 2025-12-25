import os
from typing import Annotated, Union

import fastapi_babel
import typer

from ...const import INTERNAL_LANG_FOLDER
from ...lang import __all__
from ...lang.babel import FastAPIRTKBabelCLI, FastAPIRTKBabelConfigs
from ...setting import Setting
from ..cli import app
from ..decorators import check_existing_app_silent
from ..utils import merge_pot_files
from . import version_callback

translate_app = typer.Typer(rich_markup_mode="rich")
app.add_typer(translate_app, name="translate")

DEFAULT_EXTRACT_KEYWORDS = f"{' '.join(__all__)} lazy_gettext"

RootPathType = Annotated[
    str | None,
    typer.Option(
        help="Path to the root directory of the Babel. If not provided, `LANG_FOLDER` setting will be used. If `BABEL_OPTIONS` contains `ROOT_DIR`, it will be used instead."
    ),
]

BabelCfgType = Annotated[
    str | None,
    typer.Option(
        help="Path to the Babel configuration file. If not provided, it will check for `babel.cfg` in the root directory first, then use the default from `fastapi_rtk` library."
    ),
]

ExtractDirType = Annotated[
    str,
    typer.Option(
        help="Directory to extract translations from. Defaults to the current directory."
    ),
]

KeywordsType = Annotated[
    str,
    typer.Option(
        help="Additional keywords to extract translations for separated by space."
    ),
]

LocalesType = Annotated[
    str | None,
    typer.Option(
        help="Locales to initialize, separated by commas. If not provided, `LANGUAGES` setting will be used."
    ),
]

MergeWithInternalType = Annotated[
    bool,
    typer.Option(
        help="Merge translations with internal translations from `fastapi_rtk` library."
    ),
]


@translate_app.callback()
@check_existing_app_silent
def callback(
    version: Annotated[
        Union[bool, None],
        typer.Option(
            "--version", help="Show the version and exit.", callback=version_callback
        ),
    ] = None,
) -> None:
    """
    FastAPI RTK Translate CLI - The [bold]fastapi-rtk translate[/bold] command line app. 😎

    Manage your [bold]FastAPI React Toolkit[/bold] translations easily with this CLI.
    """


@translate_app.command()
def extract(
    root_path: RootPathType = None,
    babel_cfg: BabelCfgType = None,
    extract_dir: ExtractDirType = ".",
    keywords: KeywordsType = DEFAULT_EXTRACT_KEYWORDS,
):
    """
    Extract translations from the source code.
    """
    babel_cli = init_babel_cli(root_path=root_path, babel_cfg=babel_cfg)
    typer.echo(f"Extracting translations with additional keywords: {keywords}")
    babel_cli.extract(extract_dir, keywords)


@translate_app.command()
def init(
    root_path: RootPathType = None,
    babel_cfg: BabelCfgType = None,
    locales: LocalesType = None,
    merge_with_internal: MergeWithInternalType = True,
):
    """
    Initialize translations for the specified locales. If the locale files do not exist, it will create them based on the domain file (messages.pot). If the domain file does not exist, it will run the `extract` command first.
    """
    babel_cli = init_babel_cli(root_path=root_path, babel_cfg=babel_cfg)

    # Check for the domain file
    domain_file = babel_cli.babel.config.BABEL_MESSAGE_POT_FILE
    if not os.path.exists(domain_file):
        typer.echo(
            f"Domain file {domain_file} does not exist. running `extract` command"
        )
        extract_dir = babel_cli.babel.config.ROOT_DIR
        # If the extract_dir does not contain any .py files, we will run the extract command on the parent directory
        if not any(f.endswith(".py") for f in os.listdir(extract_dir)):
            extract_dir = os.path.join(extract_dir, "..")

        extract(
            root_path=root_path,
            babel_cfg=babel_cfg,
            extract_dir=extract_dir,
            merge_with_internal=merge_with_internal,
        )

    if locales is None:
        locales = Setting.LANGUAGES
        typer.echo(
            f"No locales provided. Using `LANGUAGES` setting: {locales}. If you want to specify locales, use the `--locales` option."
        )

    for local in locales.split(","):
        local = local.strip()
        # Check whether the locale directory exists
        locale_dir = os.path.join(
            babel_cli.babel.config.BABEL_TRANSLATION_DIRECTORY, local
        )
        if os.path.exists(locale_dir):
            typer.echo(
                f"Locale directory {locale_dir} already exists. Skipping initialization for {local}."
            )
            continue

        typer.echo(f"Initializing translations for locale: {local}")
        babel_cli.init(local)


@translate_app.command()
def update(
    root_path: RootPathType = None,
    babel_cfg: BabelCfgType = None,
    locales: LocalesType = None,
    merge_with_internal: MergeWithInternalType = True,
):
    """
    Update translations from the domain (messages.pot) file to the locale files. If the locale files do not exist, `init` command will be run for the locale.
    """
    babel = init_babel_cli(root_path=root_path, babel_cfg=babel_cfg)

    if locales is None:
        locales = Setting.LANGUAGES
        typer.echo(
            f"No locales provided. Using `LANGUAGES` setting: {locales}. If you want to specify locales, use the `--locales` option."
        )

    for local in locales.split(","):
        local = local.strip()
        locale_dir = os.path.join(babel.babel.config.BABEL_TRANSLATION_DIRECTORY, local)
        if not os.path.exists(locale_dir):
            typer.echo(
                f"Locale directory {locale_dir} does not exist. running `init` command for {local}."
            )
            init(
                root_path=root_path,
                babel_cfg=babel_cfg,
                locales=local,
                merge_with_internal=merge_with_internal,
            )

    typer.echo(f"Updating translations for locales: {locales}")
    babel.update()

    if not merge_with_internal:
        typer.echo(
            "Skipping merging with internal translations. If you want to merge with internal translations, use the `--merge-with-internal` option."
        )
        return

    for local in locales.split(","):
        # Combine the locale with the internal translations
        local = local.strip()
        locale_dir = os.path.join(babel.babel.config.BABEL_TRANSLATION_DIRECTORY, local)

        internal_locale_dir = os.path.join(INTERNAL_LANG_FOLDER, "translations", local)
        po_file = os.path.join(
            locale_dir,
            "LC_MESSAGES",
            babel.babel.config.BABEL_DOMAIN.replace(".pot", "") + ".po",
        )
        internal_po_file = os.path.join(
            internal_locale_dir,
            "LC_MESSAGES",
            babel.babel.config.BABEL_DOMAIN.replace(".pot", "") + ".po",
        )
        merge_pot_files(pot_files=[po_file, internal_po_file], output_path=po_file)


@translate_app.command()
def compile(root_path: RootPathType = None, babel_cfg: BabelCfgType = None):
    """
    Compile the translations. This will create the .mo files from the .po files.
    """
    babel = init_babel_cli(root_path=root_path, babel_cfg=babel_cfg)
    typer.echo("Compiling translations.")
    babel.compile()


@translate_app.command()
def build(
    root_path: RootPathType = None,
    babel_cfg: BabelCfgType = None,
    extract_dir: ExtractDirType = ".",
    keywords: KeywordsType = DEFAULT_EXTRACT_KEYWORDS,
    locales: LocalesType = None,
    merge_with_internal: MergeWithInternalType = True,
):
    """
    Build the translations by extracting, updating, and compiling them in one step. This keeps the translations up-to-date and ready for use in your FastAPI application.
    """
    extract(
        root_path=root_path,
        babel_cfg=babel_cfg,
        extract_dir=extract_dir,
        keywords=keywords,
    )
    update(
        root_path=root_path,
        babel_cfg=babel_cfg,
        locales=locales,
        merge_with_internal=merge_with_internal,
    )
    compile(root_path=root_path, babel_cfg=babel_cfg)


def init_babel_cli(
    root_path: RootPathType = None,
    babel_cfg: BabelCfgType = None,
    *,
    create_root_path_if_not_exists=True,
    log=True,
):
    """
    Initialize Babel CLI with the provided root path and Babel configuration file.

    Args:
        root_path (RootPathType): Path to the root directory of the Babel. If not provided, `LANG_FOLDER` setting will be used. If `BABEL_OPTIONS` contains `ROOT_DIR`, it will be used instead.
        babel_cfg (BabelCfgType): Path to the Babel configuration file. If not provided, it will check for `babel.cfg` in the root directory first, then use the default from `fastapi_rtk` library.
        create_if_not_exists (bool): Whether to create the root path if it does not exist. Defaults to True.
        log (bool): Whether to log the actions taken. Defaults to True.

    Raises:
        FileNotFoundError: If the root path does not exist and `create_root_path_if_not_exists` is False.

    Returns:
        FastAPIRTKBabelCLI: An instance of the FastAPIRTKBabelCLI class initialized with the Babel configurations.
    """
    if root_path is None and "ROOT_DIR" not in Setting.BABEL_OPTIONS:
        root_path = Setting.LANG_FOLDER
        log and typer.echo(
            f"No root directory provided. Using `LANG_FOLDER` setting: {root_path}"
        )
    if babel_cfg is None and "BABEL_CONFIG_FILE" not in Setting.BABEL_OPTIONS:
        file_exists = os.path.exists(os.path.join(root_path, "babel.cfg"))
        if not file_exists:
            babel_cfg = os.path.join(INTERNAL_LANG_FOLDER, "babel.cfg")
            log and typer.echo(
                f"No Babel configuration file provided. Using default from {babel_cfg}"
            )

    # Ensure root_path exists
    if not os.path.exists(root_path):
        log and typer.echo(f"Root path {root_path} does not exist.")
        if create_root_path_if_not_exists:
            log and typer.echo(f"Creating necessary directories at {root_path}.")
            os.makedirs(root_path, exist_ok=True)
        else:
            raise FileNotFoundError(f"Root path {root_path} does not exist.")

    kwargs = {
        "ROOT_DIR": root_path,
        "BABEL_DEFAULT_LOCALE": "en",
        "BABEL_TRANSLATION_DIRECTORY": "translations",
    } | Setting.BABEL_OPTIONS
    if babel_cfg is not None:
        kwargs["BABEL_CONFIG_FILE"] = babel_cfg

    return FastAPIRTKBabelCLI(
        fastapi_babel.Babel(configs=FastAPIRTKBabelConfigs(**kwargs))
    )
