import inspect
import io
import logging
import os
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

import fastapi
import Secweb
import Secweb.ContentSecurityPolicy
import starlette.types
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_babel import BabelMiddleware
from jinja2 import Environment, TemplateNotFound, select_autoescape
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.routing import _DefaultLifespan

from .api.model_rest_api import ModelRestApi
from .auth import Auth
from .backends.sqla.session import SQLASession
from .cli.commands.db import upgrade
from .cli.commands.translate import init_babel_cli
from .const import (
    BASE_APIS,
    DEFAULT_SECWEB_PARAMS,
    INTERNAL_LANG_FOLDER,
    ErrorCode,
    logger,
)
from .db import db
from .dependencies import (
    set_global_background_tasks,
    set_global_request,
    set_global_user,
)
from .globals import GlobalsMiddleware, g
from .middlewares import (
    ProfilerMiddleware,
    SecWebPatchDocsMiddleware,
    SecWebPatchReDocMiddleware,
)
from .security.sqla.apis import (
    AuthApi,
    InfoApi,
    PermissionsApi,
    PermissionViewApi,
    RolesApi,
    UsersApi,
    ViewsMenusApi,
)
from .security.sqla.models import Api, Permission, PermissionApi, Role
from .security.sqla.security_manager import SecurityManager
from .setting import Setting
from .utils import deep_merge, lazy, multiple_async_contexts, safe_call, smart_run
from .version import __version__

__all__ = ["FastAPIReactToolkit"]


class FastAPIReactToolkit:
    """
    The main class for the `FastAPIReactToolkit` library.

    This class provides a set of methods to initialize a FastAPI application, add APIs, manage permissions and roles,
    and initialize the database with permissions, APIs, roles, and their relationships.

    Args:
        app (FastAPI | None, optional): The FastAPI application instance. If set, the `initialize` method will be called with this instance. Defaults to None.
        create_tables (bool, optional): Whether to create tables in the database. Not needed if you use a migration system like Alembic. Defaults to False.
        upgrade_db (bool, optional): Whether to upgrade the database automatically with the `upgrade` command. Same as running `fastapi-rtk db upgrade`. Defaults to False.
        cleanup (bool, optional): Whether to clean up old permissions and roles in the database using `SecurityManager.cleanup()`. Defaults to False.
        auth (Auth | None, optional): The authentication configuration. Set this if you want to customize the authentication system. See the `Auth` class for more details. Defaults to None.
        exclude_apis (list[BASE_APIS] | None, optional): List of security APIs to be excluded when initializing the FastAPI application. Defaults to None.
        global_user_dependency (bool, optional): Whether to add the `set_global_user` dependency to the FastAPI application. This allows you to access the current user with the `g.user` object. Defaults to True.
        global_background_tasks (bool, optional): Whether to add the `set_global_background_tasks` dependency to the FastAPI application. This allows you to access the background tasks with the `g.background_tasks` object. Defaults to True.
        instrumentator (Instrumentator | None, optional): The instrumentator to use for monitoring the FastAPI application. Defaults to `Instrumentator(**Setting.INSTRUMENTATOR_CONFIG)`.
        on_startup (Callable[[FastAPI], None]  |  Awaitable[Callable[[FastAPI], None]]  |  None, optional): Function to call when the app is starting up. Can either be a regular function or an async function. If the function takes a `FastAPI` instance as an argument, it will be passed to the function. Defaults to None.
        on_shutdown (Callable[[FastAPI], None]  |  Awaitable[Callable[[FastAPI], None]]  |  None, optional): Function to call when the app is shutting down. Can either be a regular function or an async function. If the function takes a `FastAPI` instance as an argument, it will be passed to the function. Defaults to None.
        debug (bool, optional): Whether to log debug messages. Defaults to False.

    ## Example:

    ```python
    import logging

    from fastapi import FastAPI, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi_rtk import FastAPIReactToolkit, User
    from fastapi_rtk.manager import UserManager

    from .base_data import add_base_data

    logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    logging.getLogger().setLevel(logging.INFO)


    class CustomUserManager(UserManager):
        async def on_after_login(
            self,
            user: User,
            request: Request | None = None,
            response: Response | None = None,
        ) -> None:
            await super().on_after_login(user, request, response)
            print("User logged in: ", user)


    async def on_startup(app: FastAPI):
        await add_base_data()
        print("base data added")
        pass


    app = FastAPI(docs_url="/openapi/v1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:6006"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    toolkit = FastAPIReactToolkit(
        auth={
            "user_manager": CustomUserManager,
            # "password_helper": FABPasswordHelper(),  #! Add this line to use old password hash
        },
        create_tables=True,
        on_startup=on_startup,
    )
    toolkit.config.from_pyfile("./app/config.py")
    toolkit.initialize(app)

    from .apis import *
    ```
    """

    app: FastAPI = None

    # Database configuration
    create_tables: bool = False
    upgrade_db = False
    cleanup = False

    # Application configuration
    exclude_apis: list[BASE_APIS] = None
    global_user_dependency = True
    global_background_tasks = True
    global_request = True
    instrumentator: Instrumentator = None
    on_startup: (
        Callable[[FastAPI], None] | Awaitable[Callable[[FastAPI], None]] | None
    ) = None
    on_shutdown: (
        Callable[[FastAPI], None] | Awaitable[Callable[[FastAPI], None]] | None
    ) = None

    # Public attributes
    apis: list[ModelRestApi] = None
    initialized = False
    sm: SecurityManager = None
    security: SecurityManager = lazy(lambda self: self.sm)
    """
    Old attribute for `sm`, kept for backward compatibility.
    """
    started = False
    """
    Indicates whether the application has been started.
    """

    # Private attributes
    _mounted = False

    def __init__(
        self,
        app: FastAPI | None = None,
        *,
        # Database configuration
        create_tables: bool = False,
        upgrade_db: bool = False,
        cleanup: bool = False,
        # Application configuration
        auth: Auth | None = None,
        exclude_apis: list[BASE_APIS] | None = None,
        global_user_dependency: bool = True,
        global_background_tasks: bool = True,
        global_request: bool = True,
        instrumentator: Instrumentator | None = None,
        on_startup: (
            Callable[[FastAPI], None] | Awaitable[Callable[[FastAPI], None]] | None
        ) = None,
        on_shutdown: (
            Callable[[FastAPI], None] | Awaitable[Callable[[FastAPI], None]] | None
        ) = None,
        lifespans: starlette.types.Lifespan[fastapi.applications.AppType]
        | list[starlette.types.Lifespan[fastapi.applications.AppType]]
        | None = None,
        debug: bool = False,
    ):
        """
        Initializes the FastAPIReactToolkit with the given parameters.

        Args:
            app (FastAPI | None, optional): The FastAPI application instance. If set, the `initialize` method will be called with this instance. Defaults to None.
            create_tables (bool, optional): Whether to create tables in the database. Not needed if you use a migration system like Alembic. Defaults to False.
            upgrade_db (bool, optional): Whether to upgrade the database automatically with the `upgrade` command. Same as running `fastapi-rtk db upgrade`. Defaults to False.
            cleanup (bool, optional): Whether to clean up old permissions and roles in the database using `SecurityManager.cleanup()`. Defaults to False.
            auth (Auth | None, optional): The authentication configuration. Set this if you want to customize the authentication system. See the `Auth` class for more details. Defaults to None.
            exclude_apis (list[BASE_APIS] | None, optional): List of security APIs to be excluded when initializing the FastAPI application. Defaults to None.
            global_user_dependency (bool, optional): Whether to add the `set_global_user` dependency to the FastAPI application. This allows you to access the current user with the `g.user` object. Defaults to True.
            global_background_tasks (bool, optional): Whether to add the `set_global_background_tasks` dependency to the FastAPI application. This allows you to access the background tasks with the `g.background_tasks` object. Defaults to True.
            global_request (bool, optional): Whether to add the `set_global_request` dependency to the FastAPI application. This allows you to access the current request with the `g.request` object. Defaults to True.
            instrumentator (Instrumentator | None, optional): The instrumentator to use for monitoring the FastAPI application. Defaults to `Instrumentator(**Setting.INSTRUMENTATOR_CONFIG)`.
            on_startup (Callable[[FastAPI], None]  |  Awaitable[Callable[[FastAPI], None]]  |  None, optional): Function to call when the app is starting up. Can either be a regular function or an async function. If the function takes a `FastAPI` instance as an argument, it will be passed to the function. Defaults to None.
            on_shutdown (Callable[[FastAPI], None]  |  Awaitable[Callable[[FastAPI], None]]  |  None, optional): Function to call when the app is shutting down. Can either be a regular function or an async function. If the function takes a `FastAPI` instance as an argument, it will be passed to the function. Defaults to None.
            lifespans (starlette.types.Lifespan[fastapi.applications.AppType]  |  list[starlette.types.Lifespan[fastapi.applications.AppType]]  |  None, optional): Lifespan or list of lifespans to combine with the main lifespan. Defaults to None.
            debug (bool, optional): Whether to log debug messages. Defaults to False.
        """
        g.current_app = self
        self.apis = []
        self.sm = SecurityManager(self)

        # Database configuration
        self.create_tables = create_tables
        self.upgrade_db = upgrade_db
        self.cleanup = cleanup

        self.exclude_apis = exclude_apis or []
        self.global_user_dependency = global_user_dependency
        self.global_background_tasks = global_background_tasks
        self.global_request = global_request
        self.instrumentator = instrumentator
        self.on_startup = on_startup
        self.on_shutdown = on_shutdown
        self.lifespans = (
            lifespans
            if isinstance(lifespans, list)
            else [lifespans]
            if lifespans
            else []
        )

        if auth:
            for key, value in auth.items():
                setattr(g.auth, key, value)

        if app:
            self.initialize(app)

        if debug:
            logger.setLevel(logging.DEBUG)

    def initialize(self, app: FastAPI) -> None:
        """
        Initializes the FastAPI application.

        Args:
            app (FastAPI): The FastAPI application instance.

        Returns:
            None
        """
        if self.initialized:
            return

        self.initialized = True
        self.app = app

        # Read config once
        self._init_config()

        # Add SecWeb
        if Setting.SECWEB_ENABLED:
            Secweb.SecWeb(
                app, **deep_merge(DEFAULT_SECWEB_PARAMS, Setting.SECWEB_PARAMS)
            )

            if Setting.SECWEB_PATCH_DOCS:
                self.app.add_middleware(SecWebPatchDocsMiddleware, fastapi=app)

            if Setting.SECWEB_PATCH_REDOC:
                self.app.add_middleware(SecWebPatchReDocMiddleware)

        # Initialize the database connection
        self.connect_to_database()

        # Initialize the lifespan
        self._init_lifespan()

        # Add the ProfilerMiddleware
        if Setting.PROFILER_ENABLED:
            try:
                import pyinstrument  # type: ignore
            except ImportError:
                raise RuntimeError(
                    "Profiler is enabled but pyinstrument is not installed, please install pyinstrument to use the profiler"
                )
            g.pyinstrument = pyinstrument
            self.app.add_middleware(ProfilerMiddleware)
            logger.info("PROFILER ENABLED")

        # Add the GlobalsMiddleware
        self.app.add_middleware(GlobalsMiddleware)
        if self.global_user_dependency:
            self.app.router.dependencies.append(Depends(set_global_user()))
        if self.global_background_tasks:
            self.app.router.dependencies.append(Depends(set_global_background_tasks))
        if self.global_request:
            self.app.router.dependencies.append(Depends(set_global_request))

        # Add the language middleware
        try:
            babel_cli = init_babel_cli(create_root_path_if_not_exists=False, log=False)
        except FileNotFoundError:
            # If the user does not have a lang folder, then use the internal one
            babel_cli = init_babel_cli(root_path=INTERNAL_LANG_FOLDER, log=False)
        self.app.add_middleware(BabelMiddleware, babel_configs=babel_cli.babel.config)

        # Initialize the instrumentator
        if not self.instrumentator:
            self.instrumentator = Instrumentator(**Setting.INSTRUMENTATOR_CONFIG)
        self.instrumentator.instrument(
            app=self.app, **Setting.INSTRUMENTATOR_INSTRUMENT_CONFIG
        )

        # Add the APIs
        self._init_basic_apis()

    def add_api(self, api: ModelRestApi | type[ModelRestApi]):
        """
        Adds the specified API to the FastAPI application.

        Parameters:
        - api (ModelRestApi | type[ModelRestApi]): The API to add to the FastAPI application.

        Returns:
        - None

        Raises:
        - ValueError: If the API is added after the `mount()` method is called.
        """
        if self._mounted:
            raise ValueError(
                "API Mounted after mount() was called, please add APIs before calling mount()"
            )

        api = api if isinstance(api, ModelRestApi) else api()
        previous_api = next(
            (a for a in self.apis if a.resource_name == api.resource_name), None
        )
        if previous_api:
            logger.warning(
                f"API {api.resource_name} already exists, replacing with new API"
            )
            self.apis.remove(previous_api)
        self.apis.append(api)
        api.toolkit = self

    def total_permissions(self) -> list[str]:
        """
        Returns the total list of permissions required by all APIs.

        Returns:
        - list[str]: The total list of permissions.
        """
        permissions = []
        for api in self.apis:
            permissions.extend(getattr(api, "permissions", []))
        return list(set(permissions))

    def connect_to_database(self):
        """
        Connects to the database using the configured SQLAlchemy database URI.

        This method initializes the database session maker with the SQLAlchemy
        database URI specified in the configuration.

        Raises:
            ValueError: If the `SQLALCHEMY_DATABASE_URI` is not set in the configuration.
        """
        uri = Setting.SQLALCHEMY_DATABASE_URI
        if not uri:
            logger.warning(
                "SQLALCHEMY_DATABASE_URI is not set in the configuration, skipping database connection, any database related operation will fail"
            )
            return

        binds = Setting.SQLALCHEMY_BINDS
        db.init_db(uri, binds)
        logger.info("Connected to database")
        logger.info(f"URI: {db._engine.url}")
        if db._engine_binds:
            logger.info("BINDS =========================")
            for bind, engine in db._engine_binds.items():
                logger.info(f"{bind}: {engine.url}")
            logger.info("BINDS =========================")

    async def init_database(self):
        """
        Initializes the database by inserting permissions, APIs, roles, and their relationships.

        The initialization process is as follows:
        1. Inserts permissions into the database.
        2. Inserts APIs into the database.
        3. Inserts roles into the database.
        4. Inserts the relationship between permissions and APIs into the database.
        5. Inserts the relationship between permissions, APIs, and roles into the database.

        Returns:
            None
        """
        if not db._engine:
            logger.warning(
                "Database not connected, skipping database initialization, any database related operation will fail"
            )
            return

        async with db.session() as session:
            logger.info("INITIALIZING DATABASE")
            permissions = await self._insert_permissions(session)
            apis = await self._insert_apis(session)
            roles = await self._insert_roles(session)
            assert permissions is not None, "Permissions should not be None"
            assert apis is not None, "APIs should not be None"
            permission_apis = await self._associate_permission_with_api(
                session, permissions, apis
            )
            assert roles is not None, "Roles should not be None"
            assert permission_apis is not None, "PermissionApis should not be None"
            await self._associate_role_with_permission_api(
                session, roles, permission_apis
            )
            if self.cleanup:
                await self.sm.cleanup()
            logger.info("DATABASE INITIALIZED")

    async def _insert_permissions(self, session: SQLASession):
        permissions = self.total_permissions() + [
            x[1] for x in self.sm.get_api_permission_tuples_from_builtin_roles()
        ]
        permissions = list(dict.fromkeys(permissions))
        return await self.sm.create_permissions(permissions, session=session)

    async def _insert_apis(self, session: SQLASession):
        apis = [api.__class__.__name__ for api in self.apis] + [
            x[0] for x in self.sm.get_api_permission_tuples_from_builtin_roles()
        ]
        apis = list(dict.fromkeys(apis))
        return await self.sm.create_apis(apis, session=session)

    async def _insert_roles(self, session: SQLASession):
        roles = self.sm.get_roles_from_builtin_roles()
        if g.admin_role and g.admin_role not in roles:
            roles.append(g.admin_role)
        if g.public_role and g.public_role not in roles:
            roles.append(g.public_role)
        return await self.sm.create_roles(roles, session=session)

    async def _associate_permission_with_api(
        self,
        session: SQLASession,
        permissions: list[Permission],
        apis: list[Api],
    ):
        permission_map = {permission.name: permission for permission in permissions}
        api_map = {api.name: api for api in apis}
        permission_api_tuples = list[tuple[Permission, Api]]()
        added_permission_api = set[tuple[str, str]]()

        for api in self.apis:
            api_permissions = api.permissions
            if not api_permissions:
                continue

            for permission_name in api_permissions:
                if (permission_name, api.__class__.__name__) in added_permission_api:
                    continue
                permission = permission_map[permission_name]
                api_obj = api_map[api.__class__.__name__]
                permission_api_tuples.append((permission, api_obj))
                added_permission_api.add((permission.name, api_obj.name))

        for (
            api_name,
            perm_name,
        ) in self.sm.get_api_permission_tuples_from_builtin_roles():
            if (perm_name, api_name) in added_permission_api:
                continue
            permission = permission_map[perm_name]
            api_obj = api_map[api_name]
            permission_api_tuples.append((permission, api_obj))
            added_permission_api.add((permission.name, api_obj.name))

        return await self.sm.associate_list_of_permission_with_api(
            permission_api_tuples, session=session
        )

    async def _associate_role_with_permission_api(
        self,
        session: SQLASession,
        roles: list[Role],
        permission_apis: list[PermissionApi],
    ):
        role_map = {role.name: role for role in roles}
        permission_api_map = {
            (pa.permission.name, pa.api.name): pa for pa in permission_apis
        }
        permission_apis_to_exclude_from_admin = list[PermissionApi]()
        role_permission_api_tuples = list[tuple[Role, PermissionApi]]()

        for (
            role_name,
            role_api_permissions,
        ) in self.sm.get_role_and_api_permission_tuples_from_builtin_roles():
            for api_name, permission_name in role_api_permissions:
                role = role_map[role_name]
                permission_api = permission_api_map[(permission_name, api_name)]
                role_permission_api_tuples.append((role, permission_api))
                if "|" in permission_name and role_name != g.public_role:
                    # Exclude multi-tenant permissions from admin role if not explicitly set
                    permission_apis_to_exclude_from_admin.append(permission_api)

        if g.admin_role:
            admin_role = role_map[g.admin_role]
            for permission_api in [
                pa
                for pa in permission_apis
                if pa not in permission_apis_to_exclude_from_admin
            ]:
                role_permission_api_tuples.append((admin_role, permission_api))

        await self.sm.associate_list_of_role_with_permission_api(
            role_permission_api_tuples, session=session
        )

    def _mount_static_folder(self):
        """
        Mounts the static folder specified in the configuration.

        Returns:
            None
        """
        # If the folder does not exist, create it
        os.makedirs(Setting.STATIC_FOLDER, exist_ok=True)

        static_folder = Setting.STATIC_FOLDER
        self.app.mount("/static", StaticFiles(directory=static_folder), name="static")

    def _mount_template_folder(self):
        """
        Mounts the template folder specified in the configuration.

        Returns:
            None
        """
        # If the folder does not exist, create it
        os.makedirs(Setting.TEMPLATE_FOLDER, exist_ok=True)

        templates = Jinja2Templates(directory=Setting.TEMPLATE_FOLDER)

        @self.app.get("/{full_path:path}", response_class=HTMLResponse)
        def index(request: Request):
            try:
                nonce = Secweb.ContentSecurityPolicy.Nonce_Processor()
                return templates.TemplateResponse(
                    request=request,
                    name="index.html",
                    context={
                        "base_path": (
                            Setting.BASE_PATH or request.scope["root_path"]
                        ).rstrip("/")
                        + "/",
                        "nonce": nonce,
                        "csp_nonce": lambda: nonce,
                        "app_name": Setting.APP_NAME,
                        **Setting.TEMPLATE_CONTEXT,
                    },
                )
            except TemplateNotFound:
                raise HTTPException(
                    fastapi.status.HTTP_404_NOT_FOUND, ErrorCode.PAGE_NOT_FOUND
                )

    """
    -----------------------------------------
         INIT FUNCTIONS
    -----------------------------------------
    """

    def _init_config(self):
        """
        Initializes the configuration for the FastAPI application.

        This method reads the configuration values from the `g.config` dictionary and sets the corresponding attributes
        of the FastAPI application.
        """
        if self.app:
            self.app.title = Setting.APP_NAME
            self.app.summary = Setting.APP_SUMMARY or self.app.summary
            self.app.description = Setting.APP_DESCRIPTION or self.app.description
            self.app.version = Setting.APP_VERSION or __version__
            self.app.openapi_url = Setting.APP_OPENAPI_URL or self.app.openapi_url
            self.app.root_path = Setting.BASE_PATH or self.app.root_path

        if Setting.DEBUG:
            logger.setLevel(logging.DEBUG)

    def _init_lifespan(self):
        if g.is_migrate:
            return

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Integrate the router for each API
            for api in self.apis:
                api.integrate_router(app)

            # Add the endpoint for the metrics
            self.instrumentator.expose(app, **Setting.INSTRUMENTATOR_EXPOSE_CONFIG)

            await db.init_fastapi_rtk_tables()

            if self.upgrade_db:
                await smart_run(upgrade)

            if self.create_tables and db._engine:
                await db.create_all()

            # Creating permission, apis, roles, and connecting them
            await self.init_database()

            # On startup
            if self.on_startup:
                parameter_length = len(
                    inspect.signature(self.on_startup).parameters.values()
                )
                if parameter_length > 0:
                    await safe_call(self.on_startup(app))
                else:
                    await safe_call(self.on_startup())

            for api in self.apis:
                await safe_call(api.on_startup())
                if hasattr(api, "datamodel"):
                    await safe_call(api.datamodel.on_startup())

            yield

            # On shutdown
            for api in self.apis:
                await safe_call(api.on_shutdown())
                if hasattr(api, "datamodel"):
                    await safe_call(api.datamodel.on_shutdown())

            if self.on_shutdown:
                parameter_length = len(
                    inspect.signature(self.on_shutdown).parameters.values()
                )
                if parameter_length > 0:
                    await safe_call(self.on_shutdown(app))
                else:
                    await safe_call(self.on_shutdown())

            # Run when the app is shutting down
            await db.close()

        @asynccontextmanager
        async def mount_lifespan(app: FastAPI):
            # Mount the js manifest, static, and template folders
            self._init_js_manifest()
            self._mount_static_folder()
            self._mount_template_folder()
            self._mounted = True
            self.started = True
            yield

        # Combine with other lifespans
        @asynccontextmanager
        async def combined_lifespan(app: FastAPI):
            async with multiple_async_contexts(
                [
                    lifespan(app)
                    for lifespan in [lifespan] + self.lifespans + [mount_lifespan]
                ]
            ):
                yield

        # Check whether lifespan is already set
        if not isinstance(self.app.router.lifespan_context, _DefaultLifespan):
            raise ValueError(
                "Lifespan already set, please do not set lifespan directly in the FastAPI app"
            )

        self.app.router.lifespan_context = combined_lifespan

    def _init_basic_apis(self):
        apis = [
            AuthApi,
            InfoApi,
            PermissionsApi,
            PermissionViewApi,
            RolesApi,
            UsersApi,
            ViewsMenusApi,
        ]
        for api in apis:
            if api.__name__ in self.exclude_apis:
                continue
            self.add_api(api)

    def _init_js_manifest(self):
        @self.app.get("/server-config.js", response_class=StreamingResponse)
        def js_manifest():
            env = Environment(autoescape=select_autoescape(["html", "xml"]))
            template_string = "window.fab_react_config = {{ react_vars |tojson }}"
            template = env.from_string(template_string)
            react_vars = Setting.FAB_REACT_CONFIG
            if Setting.TRANSLATIONS:
                react_vars[Setting.TRANSLATIONS_KEY] = deep_merge(
                    react_vars.get(Setting.TRANSLATIONS_KEY, {}), Setting.TRANSLATIONS
                )
            rendered_string = template.render(react_vars=react_vars)
            content = rendered_string.encode("utf-8")
            scriptfile = io.BytesIO(content)
            return StreamingResponse(
                scriptfile,
                media_type="application/javascript",
            )

    """
    -----------------------------------------
         PROPERTY FUNCTIONS
    -----------------------------------------
    """

    @property
    def config(self):
        return g.config
