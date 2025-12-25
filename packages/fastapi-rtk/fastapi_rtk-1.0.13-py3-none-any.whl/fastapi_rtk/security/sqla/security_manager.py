import json
import typing
from datetime import datetime

import fastapi_users.exceptions
import sqlalchemy
import sqlalchemy.orm
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...const import logger
from ...globals import g
from ...setting import Setting
from ...utils import T, lazy, merge_schema, safe_call
from .models import Api, Permission, PermissionApi, Role, User

__all__ = ["SecurityManager"]

from ...db import UserDatabase, db

if typing.TYPE_CHECKING:
    from ...fastapi_react_toolkit import FastAPIReactToolkit


class SecurityManager:
    """
    The SecurityManager class provides functions to manage users, roles, permissions, and APIs.
    """

    toolkit: typing.Optional["FastAPIReactToolkit"]
    builtin_roles = lazy(lambda: Setting.ROLES)
    """
    The built-in roles defined in the settings.
    
    Format:
    ```python
    {
        "role_name": [
            (api_name1|api_name2|..., permission_name1|permission_name2|...),
            ...
        ],
        ...
    }
    ```
    """

    def __init__(self, toolkit: typing.Optional["FastAPIReactToolkit"] = None) -> None:
        self.toolkit = toolkit

    """
    -----------------------------------------
         USER MANAGER FUNCTIONS
    -----------------------------------------
    """

    async def get_user(
        self,
        email_or_username: str,
        *,
        session: AsyncSession | Session = None,
    ):
        """
        Gets the user with the specified email or username.

        Args:
            email_or_username (str): The email or username of the user.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.

        Returns:
            User | None: The user object if found, else None.
        """
        try:
            if not session:
                async with db.session() as session:
                    return await self.get_user(email_or_username, session=session)

            manager = next(g.auth.get_user_manager(UserDatabase(session, User)))
            try:
                return await manager.get_by_email(email_or_username)
            except fastapi_users.exceptions.UserNotExists:
                return await manager.get_by_username(email_or_username)
        except fastapi_users.exceptions.UserNotExists:
            return None

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        roles: list[str] | str | None = None,
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool | typing.Literal["user_exists"] = True,
        **kwargs,
    ):
        """
        Creates a new user with the given information.

        Args:
            username (str): The username of the user.
            email (str): The email address of the user.
            password (str): The password of the user.
            first_name (str, optional): The first name of the user. Defaults to "".
            last_name (str, optional): The last name of the user. Defaults to "".
            roles (list[str] | str | None, optional): The roles assigned to the user. Defaults to None.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool | Literal["user_exists"], optional): When set to True, raises an exception if an error occurs, otherwise returns None. If set to `user_exists`, raises an exception if the user with the given email or username already exists. Defaults to True.
            **kwargs: Additional keyword arguments to be given to the user manager.

        Returns:
            User | None: The created user object if successful, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """

        try:
            if not session:
                async with db.session() as session:
                    return await self.create_user(
                        username,
                        email,
                        password,
                        first_name,
                        last_name,
                        roles,
                        session=session,
                        raise_exception=raise_exception,
                        **kwargs,
                    )

            manager = next(g.auth.get_user_manager(UserDatabase(session, User)))
            return await manager.create(
                {
                    "email": email,
                    "username": username,
                    "password": password,
                    "first_name": first_name,
                    "last_name": last_name,
                    **kwargs,
                },
                roles,
            )
        except Exception as e:
            if not raise_exception:
                return
            if raise_exception == "user_exists":
                if isinstance(e, fastapi_users.exceptions.UserAlreadyExists):
                    raise e
            else:
                raise e

    async def update_user(
        self,
        user_update: BaseModel | dict[str, typing.Any],
        user: User,
        roles: list[str] | str | None = None,
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool | typing.Literal["user_exists"] = True,
    ):
        """
        Updates the specified user with the given information.

        Args:
            update_dict (UserUpdate, dict[str, typing.Any]): The information to update.
            user (User): The user to update.
            roles (list[str] | str | None, optional): The roles to assign to the user. Defaults to None.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool | Literal["user_exists"], optional): When set to True, raises an exception if an error occurs, otherwise returns None. If set to `user_exists`, raises an exception if the user with the given email or username already exists. Defaults to True.

        Returns:
            User | None: The updated user object if successful, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        try:
            if not session:
                async with db.session() as session:
                    return await self.update_user(
                        user_update,
                        user,
                        roles,
                        session=session,
                        raise_exception=raise_exception,
                    )

            manager = next(g.auth.get_user_manager(UserDatabase(session, User)))
            return await manager.update(user_update, user, roles)
        except Exception as e:
            if not raise_exception:
                return
            if raise_exception == "user_exists":
                if isinstance(e, fastapi_users.exceptions.UserAlreadyExists):
                    raise e
            else:
                raise e

    async def get_roles(
        self,
        roles: list[str] | str,
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool | typing.Literal["roles_mismatch"] = True,
    ):
        """
        Retrieves the roles with the specified names.

        Args:
            roles (list[str] | str): The names of the roles to retrieve.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool | Literal['roles_mismatch'], optional): When set to True, raises an exception if an error occurs, otherwise returns None. If set to `roles_mismatch`, raises an exception only when the roles do not match the expected roles. Defaults to True.


        Returns:
            list[Role] | None: The list of role objects if found, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        try:
            if not session:
                async with db.session() as session:
                    return await self.get_roles(
                        roles, session=session, raise_exception=raise_exception
                    )

            manager = next(g.auth.get_user_manager(UserDatabase(session, User)))
            return await manager.get_roles_by_names(
                roles,
                raise_exception_when_mismatch=raise_exception is True
                or raise_exception == "roles_mismatch",
            )
        except Exception as e:
            if not raise_exception:
                return
            raise e

    async def create_role(
        self,
        name: str,
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool = True,
    ):
        """
        Creates a new role with the given name.

        Args:
            name (str): The name of the role to create.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool, optional): When set to True, raises an exception if an error occurs, otherwise returns None. Defaults to True.

        Returns:
            Role | None: The created role object if successful, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        try:
            if not session:
                async with db.session() as session:
                    return await self.create_role(
                        name, session=session, raise_exception=raise_exception
                    )

            role = Role(name=name)
            session.add(role)
            await safe_call(session.commit())
            return role
        except Exception as e:
            if not raise_exception:
                return
            raise e

    async def reset_password(
        self,
        user: User,
        new_password: str,
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool | typing.Literal["user_inactive"] = True,
    ):
        """
        Resets the password of the specified user.

        Args:
            user (User): The user whose password is to be reset.
            new_password (str): The new password to set.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool | Literal["user_inactive"], optional): When set to True, raises an exception if an error occurs, otherwise returns None. If set to `user_inactive`, raises an exception if the user is inactive. Defaults to True.

        Returns:
            User | None: The user object with the updated password if successful, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        try:
            if not session:
                async with db.session() as session:
                    return await self.reset_password(
                        user,
                        new_password,
                        session=session,
                        raise_exception=raise_exception,
                    )

            manager = next(g.auth.get_user_manager(UserDatabase(session, User)))
            token = await manager.forgot_password(user)
            return await manager.reset_password(token, new_password)
        except Exception as e:
            if not raise_exception:
                return
            if raise_exception == "user_inactive":
                if isinstance(e, fastapi_users.exceptions.UserInactive):
                    raise e
            else:
                raise e

    async def export_data(
        self,
        data: typing.Literal["users", "roles"],
        type: typing.Literal["json", "csv"] = "json",
        *,
        session: AsyncSession | Session = None,
    ):
        """
        Exports the specified data to a file.

        Args:
            data (typing.Literal["users", "roles"]): The data to export (users or roles).
            type (typing.Literal["json", "csv"], optional): The type of file to export the data to. Defaults to "json".
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.

        Returns:
            str: The exported data in JSON or CSV format.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        if not session:
            async with db.session() as session:
                return await self.export_data(data, type, session=session)

        match data:
            case "users":
                from ...schemas import generate_user_get_schema

                user_schema = generate_user_get_schema(User)
                user_schema = merge_schema(
                    user_schema, {"password": (str, Field())}, name="ExportUserSchema"
                )
                stmt = select(User)
                users = await safe_call(session.scalars(stmt))
                user_dict = {}
                for user in users:
                    validated_user = user_schema.model_validate(user)
                    validated_dict = validated_user.model_dump()
                    for key, value in validated_dict.items():
                        if isinstance(value, datetime):
                            validated_dict[key] = value.isoformat()
                    user_dict[user.username] = validated_dict
                if type == "json":
                    return json.dumps(user_dict, indent=4)

                csv_data = "Username,Data\n"
                for username, data in user_dict.items():
                    csv_data += f"{username},{data}\n"
                return csv_data
            case "roles":
                from ...backends.sqla.interface import SQLAInterface

                role_schema = SQLAInterface(Role).generate_schema(
                    ["id", "name"],
                    with_id=False,
                    with_name=False,
                    name="ExportRoleSchema",
                )
                stmt = select(Role)
                roles = await safe_call(session.scalars(stmt))
                role_dict = {}
                for role in roles:
                    # TODO: Change result
                    role_dict[role.name] = role_schema.model_validate(role).model_dump()
                if type == "json":
                    return json.dumps(role_dict, indent=4)

                csv_data = "Role,Data\n"
                for role, data in role_dict.items():
                    csv_data += f"{role},{','.join(data)}\n"
                return csv_data

    """
    -----------------------------------------
         SECURITY FUNCTIONS
    -----------------------------------------
    """

    def has_access_in_builtin_roles(
        self, role_name: str, api_name: str, permission_name: str
    ):
        """
        Checks if the given role has access to the specified API and permission in the built-in roles.

        Args:
            role_name (str): The name of the role to check.
            api_name (str): The name of the API to check.
            permission_name (str): The name of the permission to check.

        Returns:
            bool: True if the role has access, False otherwise.
        """
        if role_name not in self.builtin_roles:
            return False

        for api, perm in self.builtin_roles[role_name]:
            api_names = api.split("|")
            perm_names = perm.split("|")
            if api_name in api_names and permission_name in perm_names:
                return True
        return False

    def get_roles_from_builtin_roles(self):
        """
        Retrieves the names of the built-in roles.

        Returns:
            list[str]: The list of built-in role names.
        """
        return list(self.builtin_roles.keys())

    def get_api_permission_tuples_from_builtin_roles(self, role: str | None = None):
        """
        Retrieves the API-permission tuples from the built-in roles.

        Args:
            role (str | None, optional): The name of the role to filter by. If None, retrieves from all roles. Defaults to None.

        Returns:
            list[tuple[str, str]]: The list of API-permission tuples.
        """
        api_permission_tuples = list[tuple[str, str]]()
        for role_name, role_api_permission_list in self.builtin_roles.items():
            if role is not None and role != role_name:
                continue

            for api, perm in role_api_permission_list:
                api_permission_tuples.append((api, perm))
        return api_permission_tuples

    def get_role_and_api_permission_tuples_from_builtin_roles(self):
        """
        Retrieves the role and API-permission tuples from the built-in roles.

        Returns:
            list[tuple[str, list[tuple[str, str]]]]: The list of role and API-permission tuples.
        """
        role_api_permission_tuples = list[tuple[str, list[tuple[str, str]]]]()
        for role_name, role_api_permission_list in self.builtin_roles.items():
            api_permission_list = list[tuple[str, str]]()
            for api, perm in role_api_permission_list:
                api_permission_list.append((api, perm))
            role_api_permission_tuples.append((role_name, api_permission_list))
        return role_api_permission_tuples

    async def create_roles(
        self,
        roles: list[str],
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool = True,
    ):
        """
        Creates new roles with the given names. Existing roles are not duplicated.

        Args:
            roles (list[str]): The names of the roles to create.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool, optional): When set to True, raises an exception if an error occurs, otherwise returns None. Defaults to True.

        Returns:
            list[Role] | None: The created role objects if successful, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        return await self._create_entities(
            Role,
            roles,
            session=session,
            raise_exception=raise_exception,
            on_after_create=lambda role: logger.info(f"ADDING ROLE {role}"),
        )

    async def create_permissions(
        self,
        permissions: list[str],
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool = True,
    ):
        """
        Creates new permissions with the given names. Existing permissions are not duplicated.

        Args:
            permissions (list[str]): The names of the permissions to create.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool, optional): When set to True, raises an exception if an error occurs, otherwise returns None. Defaults to True.

        Returns:
            list[Permission] | None: The created permission objects if successful, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        return await self._create_entities(
            Permission,
            permissions,
            session=session,
            raise_exception=raise_exception,
            on_after_create=lambda permission: logger.info(
                f"ADDING PERMISSION {permission}"
            ),
        )

    async def create_apis(
        self,
        apis: list[str],
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool = True,
    ):
        """
        Creates new APIs with the given names. Existing APIs are not duplicated.

        Args:
            apis (list[str]): The names of the APIs to create.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool, optional): When set to True, raises an exception if an error occurs, otherwise returns None. Defaults to True.

        Returns:
            list[Api] | None: The created API objects if successful, else None.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        return await self._create_entities(
            Api,
            apis,
            session=session,
            raise_exception=raise_exception,
            on_after_create=lambda api: logger.info(f"ADDING API {api}"),
        )

    async def associate_list_of_permission_with_api(
        self,
        permission_api_tuples: list[tuple[Permission, Api]],
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool = True,
    ):
        """
        Associates a list of permissions with APIs. Existing associations are not duplicated.

        Args:
            permission_api_tuples (list[tuple[Permission, Api]]): A list of tuples containing Permission and Api objects to associate.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool, optional): When set to True, raises an exception if an error occurs, otherwise returns None. Defaults to True.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        try:
            if not session:
                async with db.session() as session:
                    await self.associate_list_of_permission_with_api(
                        permission_api_tuples,
                        session=session,
                        raise_exception=raise_exception,
                    )
                    return

            conditions = []
            query = select(PermissionApi).options(
                sqlalchemy.orm.joinedload(PermissionApi.api),
                sqlalchemy.orm.joinedload(PermissionApi.permission),
                sqlalchemy.orm.selectinload(PermissionApi.roles),
            )
            for permission, api in permission_api_tuples:
                conditions.append(
                    sqlalchemy.and_(
                        PermissionApi.permission_id == permission.id,
                        PermissionApi.api_id == api.id,
                    )
                )
            query = query.where(sqlalchemy.or_(*conditions))
            result = await safe_call(session.scalars(query))
            existing_permission_apis = list(result.all())

            new_tuples = list[tuple[Permission, Api]]()
            for permission, api in permission_api_tuples:
                exists = False
                for permission_api in existing_permission_apis:
                    if (
                        permission_api.permission.id == permission.id
                        and permission_api.api.id == api.id
                    ):
                        exists = True
                        break
                if not exists:
                    new_tuples.append((permission, api))

            new_permission_apis = list[PermissionApi]()
            for permission, api in new_tuples:
                permission_api = PermissionApi(permission=permission, api=api, roles=[])
                session.add(permission_api)
                new_permission_apis.append(permission_api)
                logger.info(f"ASSOCIATING PERMISSION {permission} WITH API {api}")
            await safe_call(session.commit())
            return existing_permission_apis + new_permission_apis
        except Exception as e:
            if not raise_exception:
                return
            raise e

    async def associate_list_of_role_with_permission_api(
        self,
        role_permission_api_tuples: list[tuple[Role, PermissionApi]],
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool = True,
    ):
        """
        Associates a list of roles with permission APIs. Existing associations are not duplicated.

        Args:
            role_permission_api_tuples (list[tuple[Role, PermissionApi]]): A list of tuples containing Role and PermissionApi objects to associate.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool, optional): When set to True, raises an exception if an error occurs, otherwise returns None. Defaults to True.

        Raises:
            SomeException: Description of the exception raised, if any.
        """
        try:
            if not session:
                async with db.session() as session:
                    await self.associate_list_of_role_with_permission_api(
                        role_permission_api_tuples,
                        session=session,
                        raise_exception=raise_exception,
                    )
                    return

            for role, permission_api in role_permission_api_tuples:
                if role not in permission_api.roles:
                    permission_api.roles.append(role)
                    logger.info(
                        f"ASSOCIATING ROLE {role} WITH PERMISSION API {permission_api}"
                    )
            await safe_call(session.commit())
        except Exception as e:
            if not raise_exception:
                return
            raise e

    async def cleanup(self, *, session: AsyncSession | Session = None):
        """
        Cleanup unused permissions from apis and roles.

        Args:
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.

        Raises:
            Exception: If the FastAPIReactToolkit instance is not provided.
        """
        if not session:
            async with db.session() as session:
                await self.cleanup(session=session)

        if not self.toolkit:
            raise Exception(
                "FastAPIReactToolkit instance not provided, you must provide it to use this function."
            )

        api_permission_tuples = self.get_api_permission_tuples_from_builtin_roles()
        apis = [api.__class__.__name__ for api in self.toolkit.apis]
        permissions = self.toolkit.total_permissions()
        for api, permission in api_permission_tuples:
            apis.append(api)
            permissions.append(permission)

        # Clean up unused permissions
        unused_permissions = await safe_call(
            session.scalars(select(Permission).where(~Permission.name.in_(permissions)))
        )
        for permission in unused_permissions:
            logger.info(f"DELETING PERMISSION {permission} AND ITS ASSOCIATIONS")
            await safe_call(session.delete(permission))

        # Clean up unused apis
        unused_apis = await safe_call(
            session.scalars(select(Api).where(~Api.name.in_(apis)))
        )
        for api in unused_apis:
            logger.info(f"DELETING API {api} AND ITS ASSOCIATIONS")
            await safe_call(session.delete(api))

        roles = self.get_roles_from_builtin_roles()
        if g.admin_role is not None:
            roles.append(g.admin_role)

        # Clean up existing permission-apis, that are no longer connected to any roles
        permission_apis_in_db = await safe_call(
            session.scalars(
                select(PermissionApi).options(
                    sqlalchemy.orm.selectinload(PermissionApi.roles)
                )
            )
        )
        for permission_api in permission_apis_in_db:
            for role in permission_api.roles:
                if role.name not in roles:
                    permission_api.roles.remove(role)
                    logger.info(
                        f"DISASSOCIATING ROLE {role} FROM PERMISSION API {permission_api}"
                    )

        await safe_call(session.commit())

    """
    -----------------------------------------
         HELPER FUNCTIONS
    -----------------------------------------
    """

    async def _create_entities(
        self,
        entity_class: typing.Type[T],
        names: list[str],
        *,
        session: AsyncSession | Session = None,
        raise_exception: bool = True,
        on_after_create: typing.Optional[
            typing.Callable[[T], typing.Awaitable[None] | None]
        ] = None,
    ):
        """
        Helper function to create new entities with the given names.
        Existing entities are not duplicated.

        Args:
            entity_class (typing.Type[T]): The entity class to create.
            names (list[str]): The names of the entities to create.
            session (AsyncSession | Session, optional): The database session to use. If not given, a new session will be created. Defaults to None.
            raise_exception (bool, optional): When set to True, raises an exception if an error occurs, otherwise returns None. Defaults to True.
            on_after_create (Optional[Callable[[T], Awaitable[None] | None]], optional): An optional callback function to be called after each entity is created. Defaults to None.

        Returns:
            list[T] | None: The created entity objects if successful, else None.

        Raises:
            Exception: If an error occurs and raise_exception is True.
        """
        try:
            if not session:
                async with db.session() as session:
                    return await self._create_entities(
                        entity_class,
                        names,
                        session=session,
                        raise_exception=raise_exception,
                    )

            # Check for existing entities
            result = await safe_call(
                session.scalars(
                    select(entity_class).where(entity_class.name.in_(names))
                )
            )
            existing_entities = list(result.all())
            existing_names = [entity.name for entity in existing_entities]

            new_names = [name for name in names if name not in existing_names]
            new_entities = list[T]()
            for name in new_names:
                entity = entity_class(name=name)
                session.add(entity)
                new_entities.append(entity)
                if on_after_create:
                    await safe_call(on_after_create(entity))
            await safe_call(session.commit())
            return existing_entities + new_entities
        except Exception as e:
            if not raise_exception:
                return
            raise e
