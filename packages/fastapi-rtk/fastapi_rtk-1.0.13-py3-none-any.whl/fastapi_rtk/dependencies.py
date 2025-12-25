import fastapi
import sqlalchemy
from fastapi import Depends, HTTPException

from .api.base_api import BaseApi
from .const import PERMISSION_PREFIX, ErrorCode, logger
from .db import db
from .globals import g
from .security.sqla.models import Api, Permission, PermissionApi, Role, User
from .utils import smart_run

__all__ = [
    "set_global_user",
    "current_permissions",
    "has_access_dependency",
]


def set_global_user():
    """
    A dependency for FastAPI that will set the current user to the global variable `g.user`.

    Usage:
    ```python
    async def get_info(
            *,
            session: AsyncSession | Session = Depends(get_async_session),
            none: None = Depends(set_global_user()),
        ):
    ...more code
    """

    async def set_global_user_dependency(
        user: User | None = Depends(
            g.auth.fastapi_users.current_user(active=True, default_to_none=True)
        ),
    ):
        g.user = user

    return set_global_user_dependency


def check_g_user():
    """
    A dependency for FastAPI that will check if the current user is set to the global variable `g.user`.

    Usage:
    ```python
    async def get_info(
            *,
            session: AsyncSession | Session = Depends(get_async_session),
            none: None = Depends(check_g_user()),
        ):
    ...more code
    """

    async def check_g_user_dependency():
        if not g.user:
            raise HTTPException(
                fastapi.status.HTTP_401_UNAUTHORIZED,
                ErrorCode.GET_USER_MISSING_TOKEN_OR_INACTIVE_USER,
            )

    return check_g_user_dependency


def current_permissions(api: BaseApi):
    """
    A dependency for FastAPI that will return all permissions of the current user for the specified API.

    Because it will implicitly check whether the user is authenticated, it can return `401 Unauthorized` or `403 Forbidden`.

    Args:
        api (BaseApi): The API to be checked.

    Usage:
    ```python
    async def get_info(
            *,
            permissions: List[str] = Depends(current_permissions(self)),
            session: AsyncSession | Session = Depends(get_async_session),
        ):
    ...more code
    ```
    """

    async def current_permissions_depedency(_=Depends(_ensure_roles)):
        sm = g.current_app.sm
        api_name = api.__class__.__name__
        permissions = set[str]()
        db_role_ids = list[int]()

        # Retrieve permissions from built-in roles
        for role in g.user.roles:
            if role.name not in sm.builtin_roles:
                db_role_ids.append(role.id)
                continue

            api_permission_tuples = sm.get_api_permission_tuples_from_builtin_roles(
                role.name
            )
            for multi_apis_str, multi_perms_str in api_permission_tuples:
                api_names = multi_apis_str.split("|")
                perm_names = multi_perms_str.split("|")
                if api_name in api_names:
                    permissions.update(perm_names)

        if db_role_ids:
            query = (
                sqlalchemy.select(Permission)
                .join(PermissionApi)
                .join(PermissionApi.roles)
                .join(Api)
                .where(Api.name == api_name, Role.id.in_(db_role_ids))
            )
            if api.base_permissions:
                query = query.where(Permission.name.in_(api.base_permissions))

            permissions_in_db = await smart_run(db.current_session.scalars, query)
            permissions.update(perm.name for perm in permissions_in_db.all())

        if api.base_permissions:
            permissions = permissions.intersection(set(api.base_permissions))

        return list(permissions)

    return current_permissions_depedency


def has_access_dependency(
    api: BaseApi,
    permission: str,
):
    """
    A dependency for FastAPI to check whether current user has access to the specified API and permission.

    Because it will implicitly check whether the user is authenticated, it can return `401 Unauthorized` or `403 Forbidden`.

    Usage:
    ```python
    @self.router.get(
            "/_info",
            response_model=self.info_return_schema,
            dependencies=[Depends(has_access(self, "info"))],
        )
    ...more code
    ```

    Args:
        api (BaseApi): The API to be checked.
        permission (str): The permission to check.
    """
    permission = f"{PERMISSION_PREFIX}{permission}"

    async def check_permission():
        _ensure_roles(ErrorCode.PERMISSION_DENIED)
        sm = g.current_app.sm

        # First, check built-in roles (avoiding unnecessary DB queries)
        # This also covers the case for API and permission name with pipes
        if any(
            sm.has_access_in_builtin_roles(
                role.name, api.__class__.__name__, permission
            )
            for role in g.user.roles
        ):
            logger.debug(
                f"User {g.user} has access to {api.__class__.__name__} with permission {permission} via built-in roles."
            )
            return

        db_role_ids = [
            role.id for role in g.user.roles if role.name not in sm.builtin_roles
        ]
        if not db_role_ids:
            raise HTTPException(
                fastapi.status.HTTP_403_FORBIDDEN, ErrorCode.PERMISSION_DENIED
            )

        api_name = api.__class__.__name__
        stmt = (
            sqlalchemy.select(sqlalchemy.literal(True))
            .select_from(Permission)
            .join(PermissionApi)
            .join(PermissionApi.roles)
            .join(Api)
            .where(
                Api.name == api_name,
                Permission.name == permission,
                Role.id.in_(db_role_ids),
            )
            .limit(1)
        )
        result = await smart_run(db.current_session.scalar, stmt)
        result = bool(result)
        if result:
            return

        raise HTTPException(
            fastapi.status.HTTP_403_FORBIDDEN, ErrorCode.PERMISSION_DENIED
        )

    return check_permission


async def set_global_background_tasks(background_tasks: fastapi.BackgroundTasks):
    """
    A dependency for FastAPI that will set the `background_tasks` to the global variable `g.background_tasks`.

    Usage:
    ```python
    async def get_info(
            *,
            session: AsyncSession | Session = Depends(get_async_session),
            none: None = Depends(set_global_background_tasks),
        ):
    ...more code
    """
    g.background_tasks = background_tasks


async def set_global_request(request: fastapi.Request):
    """
    A dependency for FastAPI that will set the `request` to the global variable `g.request`.

    Usage:
    ```python
    async def get_info(
            *,
            session: AsyncSession | Session = Depends(get_async_session),
            none: None = Depends(set_global_request),
        ):
    ...more code
    """
    g.request = request


def _ensure_roles(err_forbidden_message=ErrorCode.GET_USER_NO_ROLES):
    """
    A dependency for FastAPI that will ensure the current user has roles assigned.

    Args:
        err_forbidden_message (str): The error message to be used when raising `403 Forbidden`. Defaults to `ErrorCode.GET_USER_NO_ROLES`.

    Raises:
        HTTPException: Raised when the user is not authenticated.
        HTTPException: Raised when the user has no roles assigned.
    """
    if not g.user:
        raise HTTPException(
            fastapi.status.HTTP_401_UNAUTHORIZED,
            ErrorCode.GET_USER_MISSING_TOKEN_OR_INACTIVE_USER,
        )

    if not g.user.roles:
        raise HTTPException(fastapi.status.HTTP_403_FORBIDDEN, err_forbidden_message)
