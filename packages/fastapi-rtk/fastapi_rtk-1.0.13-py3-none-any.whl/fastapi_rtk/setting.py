import typing

from .const import (
    DEFAULT_ADMIN_ROLE,
    DEFAULT_API_MAX_PAGE_SIZE,
    DEFAULT_LANG_FOLDER,
    DEFAULT_LANGUAGES,
    DEFAULT_PROFILER_FOLDER,
    DEFAULT_PUBLIC_ROLE,
    DEFAULT_STATIC_FOLDER,
    DEFAULT_TEMPLATE_FOLDER,
    DEFAULT_TRANSLATIONS_KEY,
    AuthType,
    logger,
)
from .exceptions import FastAPIReactToolkitException
from .globals import g

if typing.TYPE_CHECKING:
    from .bases.file_manager import AbstractFileManager, AbstractImageManager


__all__ = ["Setting"]

logger = logger.getChild("setting")


class _Setting:
    """
    A static class to have an overview of the settings of the FastAPI React Toolkit application. It is designed to be used as a static class and as a single source of truth for the settings.

    This `Setting` is useful for documentation purposes, as it provides a clear overview of the settings available in the application. It is not intended to be used as a configuration manager or to modify the settings at runtime.
    """

    """
    --------------------------------------------------------------------------------------------------------
        GENERAL SETTINGS
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def APP_NAME(self) -> str:
        return g.config.get("APP_NAME", "FastAPI React Toolkit")

    @property
    def APP_SUMMARY(self) -> str | None:
        return g.config.get("APP_SUMMARY")

    @property
    def APP_DESCRIPTION(self) -> str | None:
        return g.config.get("APP_DESCRIPTION")

    @property
    def APP_VERSION(self) -> str | None:
        return g.config.get("APP_VERSION")

    @property
    def APP_OPENAPI_URL(self) -> str | None:
        return g.config.get("APP_OPENAPI_URL")

    @property
    def ROLES(self) -> dict[str, list[list[str] | tuple[str, str]]]:
        return g.config.get("ROLES") or g.config.get("FAB_ROLES", {})

    @property
    def API_MAX_PAGE_SIZE(self) -> int:
        return g.config.get(
            "API_MAX_PAGE_SIZE",
            g.config.get("FAB_API_MAX_PAGE_SIZE", DEFAULT_API_MAX_PAGE_SIZE),
        )

    @property
    def TEXT_FILTER_SEPARATOR(self) -> str:
        return g.config.get("TEXT_FILTER_SEPARATOR", ";")

    @property
    def DEBUG(self) -> bool:
        return g.config.get("DEBUG", False)

    @property
    def BASE_PATH(self) -> str | None:
        return g.config.get("BASE_PATH")

    @property
    def TEMPLATE_CONTEXT(self) -> dict[str, typing.Any]:
        return g.config.get("TEMPLATE_CONTEXT", {})

    @property
    def FAB_REACT_CONFIG(self) -> dict[str, typing.Any]:
        return g.config.get("FAB_REACT_CONFIG", {})

    @property
    def STATIC_FOLDER(self) -> str:
        return g.config.get("STATIC_FOLDER", DEFAULT_STATIC_FOLDER)

    @property
    def TEMPLATE_FOLDER(self) -> str:
        return g.config.get("TEMPLATE_FOLDER", DEFAULT_TEMPLATE_FOLDER)

    @property
    def UPLOAD_FOLDER(self) -> str | None:
        return g.config.get("UPLOAD_FOLDER")

    @property
    def IMG_UPLOAD_FOLDER(self) -> str | None:
        return g.config.get("IMG_UPLOAD_FOLDER")

    @property
    def LANG_FOLDER(self) -> str:
        return g.config.get("LANG_FOLDER", DEFAULT_LANG_FOLDER)

    @property
    def FILE_MANAGER(self) -> "AbstractFileManager | None":
        """
        The file manager to use for file uploads.
        """
        return g.config.get("FILE_MANAGER")

    @property
    def IMAGE_MANAGER(self) -> "AbstractImageManager | None":
        """
        The image manager to use for image uploads.
        """
        return g.config.get("IMAGE_MANAGER")

    @property
    def FILE_ALLOWED_EXTENSIONS(self) -> list[str] | None:
        return g.config.get("FILE_ALLOWED_EXTENSIONS")

    @property
    def IMG_ALLOWED_EXTENSIONS(self) -> list[str]:
        return g.config.get(
            "IMG_ALLOWED_EXTENSIONS", ["gif", "jpg", "jpeg", "png", "tiff"]
        )

    @property
    def LANGUAGES(self) -> str:
        """
        Languages to use for translations, separated by commas.
        """
        return g.config.get("LANGUAGES", DEFAULT_LANGUAGES)

    @property
    def TRANSLATIONS(self) -> dict[str, dict[str, str]] | None:
        """
        Translations to be sent to the frontend.
        """
        return g.config.get("TRANSLATIONS")

    @property
    def TRANSLATIONS_KEY(self) -> str:
        """
        The key to use for the translations in the `FAB_REACT_CONFIG`.
        """
        return g.config.get("TRANSLATIONS_KEY", DEFAULT_TRANSLATIONS_KEY)

    @property
    def BABEL_OPTIONS(self) -> dict[str, typing.Any]:
        """
        Babel options to pass to the `fastapi_babel.BabelConfigs` class.
        """
        return g.config.get("BABEL_OPTIONS", {})

    """
    --------------------------------------------------------------------------------------------------------
        GENERAL SETTINGS - SecWeb
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def SECWEB_ENABLED(self) -> bool:
        return g.config.get("SECWEB_ENABLED", False)

    @property
    def SECWEB_PARAMS(self) -> dict[str, typing.Any]:
        return g.config.get("SECWEB_PARAMS", {})

    @property
    def SECWEB_PATCH_DOCS(self) -> bool:
        return g.config.get("SECWEB_PATCH_DOCS", True)

    @property
    def SECWEB_PATCH_REDOC(self) -> bool:
        return g.config.get("SECWEB_PATCH_REDOC", True)

    """
    --------------------------------------------------------------------------------------------------------
        GENERAL SETTINGS - Database
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str | None:
        """
        SQLAlchemy database URI.
        """
        return g.config.get("SQLALCHEMY_DATABASE_URI")

    @property
    def SQLALCHEMY_BINDS(self) -> dict[str, str] | None:
        """
        SQLAlchemy binds.
        """
        return g.config.get("SQLALCHEMY_BINDS")

    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> dict[str, typing.Any]:
        """
        SQLAlchemy engine options.
        """
        return g.config.get("SQLALCHEMY_ENGINE_OPTIONS", {})

    @property
    def SQLALCHEMY_ENGINE_OPTIONS_BINDS(self) -> dict[str, typing.Any]:
        """
        SQLAlchemy engine options for binds.
        """
        return g.config.get("SQLALCHEMY_ENGINE_OPTIONS_BINDS", {})

    """
    --------------------------------------------------------------------------------------------------------
        GENERAL SETTINGS - Auth
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def AUTH_LOGIN_COOKIE(self) -> bool:
        return g.config.get("AUTH_LOGIN_COOKIE", True)

    @property
    def AUTH_LOGIN_JWT(self) -> bool | None:
        return g.config.get("AUTH_LOGIN_JWT")

    @property
    def AUTH_USER_REGISTRATION(self) -> bool | None:
        return g.config.get("AUTH_USER_REGISTRATION")

    @property
    def AUTH_USER_REGISTRATION_ROLE(self) -> list[str] | str | None:
        return g.config.get("AUTH_USER_REGISTRATION_ROLE")

    @property
    def AUTH_USER_RESET_PASSWORD(self) -> bool | None:
        return g.config.get("AUTH_USER_RESET_PASSWORD")

    @property
    def AUTH_USER_VERIFY(self) -> bool | None:
        return g.config.get("AUTH_USER_VERIFY")

    @property
    def AUTH_ROLE_ADMIN(self) -> typing.Optional[str]:
        return g.config.get("AUTH_ROLE_ADMIN", DEFAULT_ADMIN_ROLE)

    @property
    def AUTH_ROLE_PUBLIC(self) -> typing.Optional[str]:
        return g.config.get("AUTH_ROLE_PUBLIC", DEFAULT_PUBLIC_ROLE)

    """
    --------------------------------------------------------------------------------------------------------
        GENERAL SETTINGS - Auth - OAuth
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def AUTH_ROLES_MAPPING(self) -> dict[str, list[str]]:
        return g.config.get("AUTH_ROLES_MAPPING", {})

    @property
    def AUTH_ROLES_SYNC_AT_LOGIN(self) -> bool:
        return g.config.get("AUTH_ROLES_SYNC_AT_LOGIN", False)

    @property
    def OAUTH_CLIENTS(self) -> list[dict[str, typing.Any]]:
        return g.config.get("OAUTH_CLIENTS", g.config.get("OAUTH_PROVIDERS", []))

    @property
    def OAUTH_REDIRECT_URI(self) -> str | None:
        return g.config.get("OAUTH_REDIRECT_URI")

    """
    --------------------------------------------------------------------------------------------------------
        GENERAL SETTINGS - Auth - LDAP
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def AUTH_TYPE(self) -> str | None:
        auth_type = g.config.get("AUTH_TYPE")
        if auth_type == AuthType.LDAP:
            if not self.AUTH_LDAP_SERVER:
                raise FastAPIReactToolkitException(
                    f"AUTH_LDAP_SERVER must be set if AUTH_TYPE is {AuthType.LDAP}"
                )
        return auth_type

    @property
    def AUTH_LDAP_SERVER(self) -> str | None:
        return g.config.get("AUTH_LDAP_SERVER")

    @property
    def AUTH_LDAP_SEARCH(self) -> str | None:
        return g.config.get("AUTH_LDAP_SEARCH")

    @property
    def AUTH_LDAP_SEARCH_FILTER(self) -> str | None:
        return g.config.get("AUTH_LDAP_SEARCH_FILTER")

    @property
    def AUTH_LDAP_APPEND_DOMAIN(self) -> str | None:
        return g.config.get("AUTH_LDAP_APPEND_DOMAIN")

    @property
    def AUTH_LDAP_USERNAME_FORMAT(self) -> str | None:
        return g.config.get("AUTH_LDAP_USERNAME_FORMAT")

    @property
    def AUTH_LDAP_UID_FIELD(self) -> str:
        return g.config.get("AUTH_LDAP_UID_FIELD", "uid")

    @property
    def AUTH_LDAP_GROUP_FIELD(self) -> str:
        return g.config.get("AUTH_LDAP_GROUP_FIELD", "memberOf")

    @property
    def AUTH_LDAP_FIRSTNAME_FIELD(self) -> str:
        return g.config.get("AUTH_LDAP_FIRSTNAME_FIELD", "givenName")

    @property
    def AUTH_LDAP_LASTNAME_FIELD(self) -> str:
        return g.config.get("AUTH_LDAP_LASTNAME_FIELD", "sn")

    @property
    def AUTH_LDAP_EMAIL_FIELD(self) -> str:
        return g.config.get("AUTH_LDAP_EMAIL_FIELD", "mail")

    @property
    def AUTH_LDAP_BIND_USER(self) -> str | None:
        user = g.config.get("AUTH_LDAP_BIND_USER")
        if user is not None:
            if self.AUTH_LDAP_SEARCH is None:
                raise FastAPIReactToolkitException(
                    "AUTH_LDAP_SEARCH must be set if AUTH_LDAP_BIND_USER is set"
                )
        return user

    @property
    def AUTH_LDAP_BIND_PASSWORD(self) -> str | None:
        return g.config.get("AUTH_LDAP_BIND_PASSWORD")

    @property
    def AUTH_LDAP_USE_TLS(self) -> bool:
        return g.config.get("AUTH_LDAP_USE_TLS", False)

    @property
    def AUTH_LDAP_ALLOW_SELF_SIGNED(self) -> bool:
        return g.config.get("AUTH_LDAP_ALLOW_SELF_SIGNED", False)

    @property
    def AUTH_LDAP_TLS_DEMAND(self) -> bool:
        return g.config.get("AUTH_LDAP_TLS_DEMAND", False)

    @property
    def AUTH_LDAP_TLS_KEYFILE(self) -> str | None:
        return g.config.get("AUTH_LDAP_TLS_KEYFILE")

    @property
    def AUTH_LDAP_TLS_CERTFILE(self) -> str | None:
        return g.config.get("AUTH_LDAP_TLS_CERTFILE")

    @property
    def AUTH_LDAP_TLS_CACERTDIR(self) -> str | None:
        return g.config.get("AUTH_LDAP_TLS_CACERTDIR")

    @property
    def AUTH_LDAP_TLS_CACERTFILE(self) -> str | None:
        return g.config.get("AUTH_LDAP_TLS_CACERTFILE")

    """
    --------------------------------------------------------------------------------------------------------
        CONFIG
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def CONFIG_ENABLE_DEEP_MERGE(self) -> bool:
        return g.config.get("CONFIG_ENABLE_DEEP_MERGE")

    @property
    def CONFIG_DEEP_MERGE_WHITELIST(self) -> list[str] | tuple[str] | None:
        return g.config.get("CONFIG_DEEP_MERGE_WHITELIST")

    """
    --------------------------------------------------------------------------------------------------------
        PROMETHEUS
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def INSTRUMENTATOR_CONFIG(self) -> dict[str, typing.Any]:
        """
        Instrumentator configuration.
        """
        return g.config.get("INSTRUMENTATOR_CONFIG", {})

    @property
    def INSTRUMENTATOR_INSTRUMENT_CONFIG(self) -> dict[str, typing.Any]:
        """
        Instrumentator instrument configuration.
        """
        return g.config.get("INSTRUMENTATOR_INSTRUMENT_CONFIG", {})

    @property
    def INSTRUMENTATOR_EXPOSE_CONFIG(self) -> dict[str, typing.Any]:
        """
        Instrumentator expose configuration.
        """
        return g.config.get("INSTRUMENTATOR_EXPOSE_CONFIG", {})

    """
    --------------------------------------------------------------------------------------------------------
        PyInstrument (Profiler)
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def PROFILER_ENABLED(self) -> bool:
        """
        Whether the profiler is enabled.
        """
        return g.config.get("PROFILER_ENABLED", False)

    @property
    def PROFILER_TYPE(self) -> str:
        """
        The profiler type.
        """
        return g.config.get("PROFILER_TYPE", "html")

    @property
    def PROFILER_RENDERER(self) -> str:
        """
        The profiler renderer.
        """
        return g.config.get("PROFILER_RENDERER", "HTMLRenderer")

    @property
    def PROFILER_FOLDER(self) -> str:
        """
        The folder to store profiler files.
        """
        return g.config.get("PROFILER_FOLDER", DEFAULT_PROFILER_FOLDER)

    """
    --------------------------------------------------------------------------------------------------------
        AUTH SETTINGS - `g.auth`
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def PASSWORD_HELPER(self):
        return g.config.get("PASSWORD_HELPER")

    @property
    def COOKIE_CONFIG(self):
        return g.config.get("COOKIE_CONFIG")

    @property
    def BEARER_CONFIG(self):
        return g.config.get("BEARER_CONFIG")

    @property
    def COOKIE_STRATEGY_CONFIG(self):
        return g.config.get("COOKIE_STRATEGY_CONFIG")

    @property
    def BEARER_STRATEGY_CONFIG(self):
        return g.config.get("BEARER_STRATEGY_CONFIG")

    @property
    def SECRET_KEY(self):
        return g.config.get("SECRET_KEY")

    @property
    def USER_MANAGER(self):
        return g.config.get("USER_MANAGER")

    @property
    def COOKIE_TRANSPORT(self):
        return g.config.get("COOKIE_TRANSPORT")

    @property
    def BEARER_TRANSPORT(self):
        return g.config.get("BEARER_TRANSPORT")

    @property
    def COOKIE_BACKEND(self):
        return g.config.get("COOKIE_BACKEND")

    @property
    def BEARER_BACKEND(self):
        return g.config.get("BEARER_BACKEND")

    @property
    def AUTHENTICATOR(self):
        return g.config.get("AUTHENTICATOR")

    @property
    def FASTAPI_USERS(self):
        return g.config.get("FASTAPI_USERS")

    @property
    def STRATEGY_BACKEND(self):
        return g.config.get("STRATEGY_BACKEND")

    """
    --------------------------------------------------------------------------------------------------------
        AUTH SETTINGS - `g.auth.cookie_config`
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def COOKIE_NAME(self):
        return g.config.get("COOKIE_NAME")

    @property
    def COOKIE_MAX_AGE(self):
        return g.config.get("COOKIE_MAX_AGE")

    @property
    def COOKIE_PATH(self):
        return g.config.get("COOKIE_PATH")

    @property
    def COOKIE_DOMAIN(self):
        return g.config.get("COOKIE_DOMAIN")

    @property
    def COOKIE_SECURE(self):
        return g.config.get("COOKIE_SECURE")

    @property
    def COOKIE_HTTPONLY(self):
        return g.config.get("COOKIE_HTTPONLY")

    @property
    def COOKIE_SAMESITE(self):
        return g.config.get("COOKIE_SAMESITE")

    """
    --------------------------------------------------------------------------------------------------------
        AUTH SETTINGS - `g.auth.bearer_config`
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def BEARER_TOKEN_URL(self):
        return g.config.get("BEARER_TOKEN_URL")

    """
    --------------------------------------------------------------------------------------------------------
        AUTH SETTINGS - `g.auth.cookie_strategy_config`
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def COOKIE_LIFETIME_SECONDS(self):
        return g.config.get("COOKIE_LIFETIME_SECONDS")

    @property
    def COOKIE_TOKEN_AUDIENCE(self):
        """
        ONLY WHEN STRATEGY_BACKEND = "JWT"
        """
        return g.config.get("COOKIE_TOKEN_AUDIENCE")

    @property
    def COOKIE_ALGORITHM(self):
        """
        ONLY WHEN STRATEGY_BACKEND = "JWT"
        """
        return g.config.get("COOKIE_ALGORITHM")

    """
    --------------------------------------------------------------------------------------------------------
        AUTH SETTINGS - `g.auth.bearer_strategy_config`
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def BEARER_LIFETIME_SECONDS(self):
        return g.config.get("BEARER_LIFETIME_SECONDS")

    @property
    def BEARER_TOKEN_AUDIENCE(self):
        """
        ONLY WHEN STRATEGY_BACKEND = "JWT"
        """
        return g.config.get("BEARER_TOKEN_AUDIENCE")

    @property
    def BEARER_ALGORITHM(self):
        """
        ONLY WHEN STRATEGY_BACKEND = "JWT"
        """
        return g.config.get("BEARER_ALGORITHM")

    """
    --------------------------------------------------------------------------------------------------------
        DEPRECATED SETTINGS
    --------------------------------------------------------------------------------------------------------
    """

    @property
    def GREMLIN_CONNECTION(self) -> tuple[str, str] | None:
        """
        The Gremlin URL and graph object.
        """
        return g.config.get("GREMLIN_CONNECTION", g.config.get("GREMLIN_URL"))

    @property
    def GREMLIN_CONNECTION_OPTIONS(self) -> dict[str, typing.Any]:
        """
        The Gremlin connection options.

        See `gremlin_python.driver.driver_remote_connection.DriverRemoteConnection` for more details.
        """
        return g.config.get("GREMLIN_CONNECTION_OPTIONS", {})

    @property
    def JANUSGRAPH_RESERVED_LETTERS(self) -> list[str]:
        return g.config.get("JANUSGRAPH_RESERVED_LETTERS", ["-"])


Setting = _Setting()
"""
Single source of truth for the configuration of the FastAPI React Toolkit.
"""
