import ssl
import typing
from datetime import UTC, datetime
from typing import Any, Callable, Coroutine, Dict, Optional, overload

import fastapi
from fastapi import HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, exceptions
from fastapi_users.db import BaseUserDatabase
from fastapi_users.jwt import generate_jwt
from fastapi_users.password import PasswordHelperProtocol
from pydantic import BaseModel
from sqlalchemy import select

from .const import ErrorCode, logger
from .db import UserDatabase
from .exceptions import RolesMismatchException
from .schemas import (
    generate_user_create_schema,
    generate_user_update_schema,
)
from .security.sqla.models import Role, User
from .setting import Setting
from .utils import call_with_valid_kwargs, safe_call

__all__ = ["UserManager"]


class IDParser:
    def parse_id(self, value: Any) -> int:
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except ValueError as e:
            raise exceptions.InvalidID() from e


class UserManager(IDParser, BaseUserManager[User, int]):
    user_db: UserDatabase[User, int]

    def __init__(
        self,
        user_db: BaseUserDatabase[User, int],
        secret_key: str,
        password_helper: PasswordHelperProtocol | None = None,
    ):
        super().__init__(user_db, password_helper)
        self.reset_password_token_secret = secret_key
        self.verification_token_secret = secret_key

    async def get_by_username(self, username: str) -> User:
        """
        Get a user by its username.

        :param username: The username of the user.
        :raises UserNotExists: The user does not exist.
        :return: A user.
        """
        user = await self.user_db.get_by_username(username)

        if user is None:
            raise exceptions.UserNotExists()

        return user

    async def get_roles_by_names(
        self, roles: list[str] | str, *, raise_exception_when_mismatch=True
    ):
        """
        Get roles by their names.

        Args:
            roles (list[str] | str): A list of role names or a single role name to look up.
            raise_exception_when_mismatch (bool, optional): If True, raises `RolesMismatchException` when the number of roles found in the database does not match the number of role names provided. Defaults to True.

        Raises:
            RolesMismatchException: If raise_exception_when_mismatch is True and the expected and retrieved role counts do not match.

        Returns:
            list[Role]: A list of Role objects that match the given role names.
        """
        if isinstance(roles, str):
            roles = [roles]
        statement = select(Role).where(Role.name.in_(roles))
        result = await safe_call(self.user_db.session.scalars(statement))
        roles_from_db = list(result.all())
        if raise_exception_when_mismatch and len(roles) != len(roles_from_db):
            raise RolesMismatchException(
                f"Expected roles {roles} do not match the found roles {[r.name for r in roles_from_db]}."
            )
        return roles_from_db

    async def authenticate(self, credentials: OAuth2PasswordRequestForm) -> User | None:
        """
        Override the default authenticate method to search by username instead of email.

        Args:
            credentials (OAuth2PasswordRequestForm): The credentials to authenticate the user.

        Returns:
            User | None: The user if the credentials are valid, None otherwise.
        """
        try:
            user = await self.get_by_username(credentials.username)
        except exceptions.UserNotExists:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self.password_helper.hash(credentials.password)
            return None

        verified, updated_password_hash = self.password_helper.verify_and_update(
            credentials.password, user.hashed_password
        )
        if not verified:
            await self.on_after_authenticate(user, False)
            return None
        # Update password hash to a more robust one if needed
        if updated_password_hash is not None:
            await self.user_db.update(user, {"hashed_password": updated_password_hash})

        await self.on_after_authenticate(user)
        return user

    async def authenticate_ldap(self, credentials: OAuth2PasswordRequestForm):
        """
        Authenticate a user using LDAP.

        Args:
            credentials (OAuth2PasswordRequestForm): The credentials to authenticate the user.

        Returns:
            User | None: The user if the credentials are valid, None otherwise.
        """
        try:
            user = await self.get_by_username(credentials.username)
        except exceptions.UserNotExists:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self.password_helper.hash(credentials.password)
            user = None

        # If no username is provided, go away
        if not credentials.username:
            return None

        # If user is not active, go away
        if user and not user.is_active:
            return None

        # If user is not registered, and not self-registration, go away
        if not user and not Setting.AUTH_USER_REGISTRATION:
            logger.warning(
                "Tried to login using ldap with username %s, but self-registration is disabled.",
                credentials.username,
            )
            return None

        # Ensure ldap3 is installed
        try:
            import ldap3
            import ldap3.core.exceptions
        except ImportError:
            logger.error(
                "You tried to use LDAP authentication, but 'ldap3' is not installed."
            )
            return None

        # --- 1. Configure TLS ---
        # ldap3 centralizes TLS settings into a Tls object.
        assert Setting.AUTH_LDAP_SERVER
        tls_config = None
        use_ssl = Setting.AUTH_LDAP_USE_TLS or "ldaps://" in Setting.AUTH_LDAP_SERVER
        if use_ssl:
            validate_cert = ssl.CERT_REQUIRED
            if Setting.AUTH_LDAP_ALLOW_SELF_SIGNED:
                validate_cert = ssl.CERT_OPTIONAL
            elif not Setting.AUTH_LDAP_TLS_DEMAND:
                # Default behavior is to require certs if TLS is on
                pass

            tls_config = ldap3.Tls(
                local_private_key_file=Setting.AUTH_LDAP_TLS_KEYFILE,
                local_certificate_file=Setting.AUTH_LDAP_TLS_CERTFILE,
                validate=validate_cert,
                ca_certs_path=Setting.AUTH_LDAP_TLS_CACERTDIR,
                ca_certs_file=Setting.AUTH_LDAP_TLS_CACERTFILE,
                version=ssl.PROTOCOL_TLS,
            )

        # --- 2. Define the Server ---
        server = ldap3.Server(
            Setting.AUTH_LDAP_SERVER,
            use_ssl=use_ssl,
            tls=tls_config,
            get_info=None,  # No need for get_info for authentication
        )

        try:
            user_dn = None
            user_attributes = {}

            # --- Flow 1 (Indirect Search Bind) ---
            if Setting.AUTH_LDAP_BIND_USER:
                # Bind with service account, search, then rebind with user credentials.
                # The 'with' statement handles connection and unbinding.
                with ldap3.Connection(
                    server,
                    Setting.AUTH_LDAP_BIND_USER,
                    Setting.AUTH_LDAP_BIND_PASSWORD,
                    auto_bind=True,
                    auto_referrals=False,  # Equivalent to OPT_REFERRALS = 0
                ) as conn:
                    assert Setting.AUTH_LDAP_SEARCH

                    # Search for the user
                    user_dn, user_attributes = self._ldap3_search(
                        conn, credentials.username
                    )

                    if not user_dn:
                        logger.info(
                            "No LDAP object found for user '%s'.", credentials.username
                        )
                        return None

                    # Validate user credentials by attempting a rebind
                    if not conn.rebind(user_dn, credentials.password):
                        logger.info("Login Failed for user: %s", credentials.username)
                        if user:
                            await self.on_after_authenticate(user, False)
                        return None

            # --- Flow 2 (Direct Search Bind) ---
            else:
                # Bind directly with the end-user's credentials.
                bind_username = credentials.username
                if Setting.AUTH_LDAP_APPEND_DOMAIN:
                    bind_username = f"{bind_username}@{Setting.AUTH_LDAP_APPEND_DOMAIN}"
                if Setting.AUTH_LDAP_USERNAME_FORMAT:
                    bind_username = (
                        Setting.AUTH_LDAP_USERNAME_FORMAT % credentials.username
                    )

                with ldap3.Connection(
                    server,
                    bind_username,
                    credentials.password,
                    auto_bind=True,
                    auto_referrals=False,
                ) as conn:
                    # If we are here, the bind was successful.

                    if Setting.AUTH_LDAP_SEARCH:
                        # Search for user attributes
                        user_dn, user_attributes = self._ldap3_search(
                            conn, credentials.username
                        )
                        if not user_dn:
                            logger.info(
                                "No LDAP object found for: %s", credentials.username
                            )
                            # Bind succeeded but search failed. Decide if this is an error.
                            # For now, we exit as the original code did.
                            return None

            # --- 3. Post-Authentication Processing ---
            # (This logic remains largely the same)
            if user and user_attributes and Setting.AUTH_ROLES_SYNC_AT_LOGIN:
                user = await self._ldap3_calculate_user(user, user_attributes)
                logger.debug(
                    "Calculated new roles for user='%s' as: %s", user_dn, user.roles
                )

            if not user and user_attributes and Setting.AUTH_USER_REGISTRATION:
                user = await self.create(
                    {
                        "username": credentials.username,
                        "password": self.password_helper.generate(),
                        "first_name": (
                            user_attributes.get(Setting.AUTH_LDAP_FIRSTNAME_FIELD)
                            or [""]
                        )[0],
                        "last_name": (
                            user_attributes.get(Setting.AUTH_LDAP_LASTNAME_FIELD)
                            or [""]
                        )[0],
                        "email": (
                            user_attributes.get(
                                Setting.AUTH_LDAP_EMAIL_FIELD,
                            )
                            or [f"{credentials.username}@email.notfound"]
                        )[0],
                    }
                )
                user = await self._ldap3_calculate_user(user, user_attributes)

            if user:
                await self.on_after_authenticate(user)
                return user
            else:
                return None

        except ldap3.core.exceptions.LDAPBindError:
            # More specific error for failed logins
            logger.info("Login Failed for user: %s", credentials.username)
            if user:
                await self.on_after_authenticate(user, False)
            return None
        except ldap3.core.exceptions.LDAPException as e:
            # Catch all other ldap3 specific errors
            logger.error("LDAP Error %s", e)
            return None

    async def create(
        self,
        user_create: BaseModel | dict[str, Any],
        roles: list[str] | str | None = None,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        """
        Modified version of the default `create` method.
        - Allows `user_create` to be a dict.
        - Adds `roles` parameter to allow specifying roles during user creation.
        - `safe` parameter is kept for compatibility but is unused.

        Create a user in database.

        Triggers the on_after_register handler on success.

        :param user_create: The UserCreate model to create. Can be a dict.
        :param roles: Optional list of roles to add to the user.
        :param safe: If True, sensitive values like is_superuser or is_verified
        will be ignored during the creation, defaults to False.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        :raises UserAlreadyExists: A user already exists with the same e-mail.
        :return: A new user.
        """
        if isinstance(user_create, dict):
            user_create = generate_user_create_schema(User, True)(**user_create)

        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(
            user_create.email
        ) or await self.user_db.get_by_username(user_create.username)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = user_create.model_dump(exclude_unset=True)
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)

        role_names = roles
        if role_names is None:
            if request:
                from .setting import Setting

                role_names = Setting.AUTH_USER_REGISTRATION_ROLE

        # Get the roles if they exist
        if role_names:
            if isinstance(role_names, str):
                role_names = [role_names]
            user_dict["roles"] = await self.get_roles_by_names(role_names)

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user

    async def update(
        self,
        user_update: BaseModel | dict[str, Any],
        user: User,
        roles: list[str] | str | None = None,
        safe: bool = False,
        request: Request | None = None,
    ) -> User:
        """
        Modified version of the default `update` method.
        - Allows `user_update` to be a dict.
        - Adds `roles` parameter to allow specifying roles during user update.
        - `safe` parameter is kept for compatibility but is unused.

        Update a user.

        Triggers the on_after_update handler on success

        :param user_update: The UserUpdate model containing
        the changes to apply to the user.
        :param user: The current user to update.
        :param safe: If True, sensitive values like is_superuser or is_verified
        will be ignored during the update, defaults to False
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        :return: The updated user.
        """
        updated_user_data = (
            user_update.model_dump(exclude_unset=True)
            if isinstance(user_update, BaseModel)
            else generate_user_update_schema(User, True)(**user_update).model_dump(
                exclude_unset=True
            )
        )
        if roles is not None:
            if isinstance(roles, str):
                roles = [roles]
            updated_user_data["roles"] = await self.get_roles_by_names(roles)
        updated_user = await self._update(user, updated_user_data)
        await self.on_after_update(updated_user, updated_user_data, request)
        return updated_user

    async def oauth_callback(
        self,
        oauth_name: str,
        access_token: str,
        account_id: str,
        account_email: str,
        expires_at: int | None = None,
        refresh_token: str | None = None,
        request: Request | None = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
        oauth_token: Optional[dict[str, Any]] = None,
        on_before_register: Optional[
            Callable[..., None] | Coroutine[None, None, None]
        ] = None,
        on_after_register: Optional[
            Callable[..., None] | Coroutine[None, None, None]
        ] = None,
        on_before_login: Optional[
            Callable[..., None] | Coroutine[None, None, None]
        ] = None,
    ) -> User:
        """
        Modified version of the default `oauth_callback` method:
        - `oauth_token` to pass the OAuth token to the callbacks.
        - `on_before_register` callback that is triggered before a new user is registered.
        - `on_after_register` callback that is triggered after a new user is registered.
        - `on_before_login` callback that is triggered after a user logs in.

        Handle the callback after a successful OAuth authentication.

        If the user already exists with this OAuth account, the token is updated.

        If a user with the same e-mail already exists and `associate_by_email` is True,
        the OAuth account is associated to this user.
        Otherwise, the `UserNotExists` exception is raised.

        If the user does not exist, it is created and the on_after_register handler
        is triggered.

        :param oauth_name: Name of the OAuth client.
        :param access_token: Valid access token for the service provider.
        :param account_id: models.ID of the user on the service provider.
        :param account_email: E-mail of the user on the service provider.
        :param expires_at: Optional timestamp at which the access token expires.
        :param refresh_token: Optional refresh token to get a
        fresh access token from the service provider.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None
        :param associate_by_email: If True, any existing user with the same
        e-mail address will be associated to this user. Defaults to False.
        :param is_verified_by_default: If True, the `is_verified` flag will be
        set to `True` on newly created user. Make sure the OAuth Provider you're
        using does verify the email address before enabling this flag.
        Defaults to False.
        :param oauth_token: Optional OAuth token from the OAuth provider.
        :param on_before_register: Optional callback to be executed before a new user is registered.
        :param on_after_register: Optional callback to be executed after a new user is registered.
        :param on_before_login: Optional callback to be executed before a user logs in.
        :return: A user.
        """
        oauth_account_dict = {
            "oauth_name": oauth_name,
            "access_token": access_token,
            "account_id": account_id,
            "account_email": account_email,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
        }
        oauth_callback_params = {
            **oauth_account_dict,
            "user_dict": {},
            "oauth_token": oauth_token,
            "user_manager": self,
            "session": self.user_db.session,
        }

        try:
            user = await self.get_by_oauth_account(oauth_name, account_id)
        except exceptions.UserNotExists:
            try:
                # Associate account
                user = await self.get_by_email(account_email)
                if not associate_by_email:
                    await self.on_after_authenticate(user, False)
                    raise exceptions.UserAlreadyExists()
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
            except exceptions.UserNotExists:
                # Create account
                password = self.password_helper.generate()
                oauth_callback_params["user_dict"] = {
                    "email": account_email,
                    "hashed_password": self.password_helper.hash(password),
                    "is_verified": is_verified_by_default,
                }

                if on_before_register:
                    result = await safe_call(
                        call_with_valid_kwargs(
                            on_before_register, oauth_callback_params
                        )
                    )
                    if result:
                        oauth_callback_params["user_dict"].update(result)
                    oauth_callback_params["user_dict"] = await self._handle_role_keys(
                        oauth_callback_params["user_dict"],
                        oauth_callback_params["user_dict"].pop("role_keys", None),
                    )
                user = await self.user_db.create(oauth_callback_params["user_dict"])
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
                oauth_callback_params["user"] = user
                if on_after_register:
                    result = await safe_call(
                        call_with_valid_kwargs(on_after_register, oauth_callback_params)
                    )
                    if result:
                        oauth_callback_params["user_dict"].update(result)
                    user = await self._handle_role_keys(
                        user, oauth_callback_params["user_dict"].pop("role_keys", None)
                    )
                await self.on_after_register(user, request)
        else:
            # Update oauth
            for existing_oauth_account in user.oauth_accounts:
                if (
                    existing_oauth_account.account_id == account_id
                    and existing_oauth_account.oauth_name == oauth_name
                ):
                    user = await self.user_db.update_oauth_account(
                        user, existing_oauth_account, oauth_account_dict
                    )

        if on_before_login:
            oauth_callback_params["user"] = user
            result = await safe_call(
                call_with_valid_kwargs(on_before_login, oauth_callback_params)
            )
            if result:
                oauth_callback_params["user_dict"].update(result)
            user = await self._handle_role_keys(
                user, oauth_callback_params["user_dict"].pop("role_keys", None)
            )
        await self.on_after_authenticate(user)
        return user

    @overload
    async def forgot_password(self, user: User, request: Request) -> None: ...
    @overload
    async def forgot_password(
        self, user: User, request: Optional[Request] = None
    ) -> str: ...
    async def forgot_password(self, user: User, request: Optional[Request] = None):
        """
        Modified version of the default `forgot_password` method to return the token when it is not in a request context.

        Start a forgot password request.

        Triggers the on_after_forgot_password handler on success.

        :param user: The user that forgot its password.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None.
        :raises UserInactive: The user is inactive.
        :return: None if in a request context, otherwise returns the reset token.
        """
        if not user.is_active:
            raise exceptions.UserInactive()

        token_data = {
            "sub": str(user.id),
            "password_fgpt": self.password_helper.hash(user.hashed_password),
            "aud": self.reset_password_token_audience,
        }
        token = generate_jwt(
            token_data,
            self.reset_password_token_secret,
            self.reset_password_token_lifetime_seconds,
        )
        await self.on_after_forgot_password(user, token, request)

        if not request:
            return token

    async def on_after_logout(
        self,
        user: User,
        request: Request | None = None,
        response: Response | None = None,
    ) -> None:
        """
        Perform logic after user logout.

        *You should overload this method to add your own logic.*

        Args:
            user (User): The user that is logging out.
            request (Request | None, optional): Optional FastAPI request.
            response (Response | None, optional): Optional response built by the transport.
        """
        return

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        if request:
            raise HTTPException(
                fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                ErrorCode.FEATURE_NOT_IMPLEMENTED,
            )

    async def on_after_reset_password(
        self, user: User, request: Request | None = None
    ) -> None:
        if request:
            raise HTTPException(
                fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                ErrorCode.FEATURE_NOT_IMPLEMENTED,
            )

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        if request:
            raise HTTPException(
                fastapi.status.HTTP_501_NOT_IMPLEMENTED,
                ErrorCode.FEATURE_NOT_IMPLEMENTED,
            )

    async def on_after_authenticate(self, user: User, success=True):
        """
        Perform logic after authentication attempt.

        Please call `await super().on_after_authenticate(user, success)` to keep the default behavior.

        Args:
            user (User): The user that attempted authentication.
            success (bool, optional): Whether the authentication was successful. Defaults to True.
        """
        update_fields = {}
        if success:
            update_fields["fail_login_count"] = 0
            update_fields["last_login"] = datetime.now(UTC).replace(tzinfo=None)
            update_fields["login_count"] = (user.login_count or 0) + 1
        else:
            update_fields["fail_login_count"] = (user.fail_login_count or 0) + 1
        if update_fields:
            await self.user_db.update(user, update_fields)

    async def _update(self, user: User, update_dict: Dict[str, Any]) -> User:
        """
        Modified version of the default `_update` method to also check for existing users with the same username.
        """
        validated_update_dict = {}
        for field, value in update_dict.items():
            if field == "email" and value != user.email:
                try:
                    await self.get_by_email(value)
                    raise exceptions.UserAlreadyExists()
                except exceptions.UserNotExists:
                    validated_update_dict["email"] = value
                    validated_update_dict["is_verified"] = False
            elif field == "username" and value != user.username:
                try:
                    await self.get_by_username(value)
                    raise exceptions.UserAlreadyExists()
                except exceptions.UserNotExists:
                    validated_update_dict["username"] = value
            elif field == "password" and value is not None:
                await self.validate_password(value, user)
                validated_update_dict["hashed_password"] = self.password_helper.hash(
                    value
                )
            else:
                validated_update_dict[field] = value
        return await self.user_db.update(user, validated_update_dict)

    @typing.overload
    async def _handle_role_keys(
        self, user_or_user_dict: User, role_keys: list[str] | None = None
    ) -> User: ...
    @typing.overload
    async def _handle_role_keys(
        self, user_or_user_dict: dict[str, Any], role_keys: list[str] | None = None
    ) -> dict[str, Any]: ...
    async def _handle_role_keys(
        self,
        user_or_user_dict: User | dict[str, Any],
        role_keys: list[str] | None = None,
    ):
        """
        Handle the role keys for a user or user dictionary.

        This method retrieves the roles based on the provided role keys and updates
        the user or user dictionary with the corresponding roles.

        Args:
            user_or_user_dict (User | dict[str, Any]): The user or user dictionary to update.
            role_keys (list[str] | None, optional): The role keys to retrieve roles for.

        Returns:
            User | dict[str, Any]: The updated user or user dictionary with roles.
        """
        if not role_keys:
            return user_or_user_dict
        role_names = [Setting.AUTH_ROLES_MAPPING.get(key, []) for key in role_keys]
        role_names = [name for sublist in role_names for name in sublist]
        role_names = list(dict.fromkeys(role_names).keys())
        if not role_names:
            return user_or_user_dict
        if isinstance(user_or_user_dict, User):
            user_or_user_dict = await self.update({}, user_or_user_dict, role_names)
        else:
            user_or_user_dict["roles"] = await self.get_roles_by_names(role_names)
        return user_or_user_dict

    """
    --------------------------------------------------------------------------------------------------------
        LDAP3 HELPER METHODS
    --------------------------------------------------------------------------------------------------------
    """

    def _ldap3_search(self, conn, username: str):
        """
        Helper function to perform an LDAP search using ldap3.

        Args:
            conn (ldap3.Connection): The LDAP connection object.
            username (str): The username to search for.

        Returns:
            Tuple[str | None, dict | None]: A tuple containing the user's DN and attributes if found, otherwise (None, None).
        """
        import ldap3.utils.conv

        # Configuration check remains good practice
        assert Setting.AUTH_LDAP_SEARCH

        # 1. Filter Construction (with security improvement)
        # ldap3 provides a utility to escape special characters to prevent LDAP injection
        safe_username = ldap3.utils.conv.escape_filter_chars(username)

        base_filter = f"({Setting.AUTH_LDAP_UID_FIELD}={safe_username})"
        if Setting.AUTH_LDAP_SEARCH_FILTER:
            # Combine the custom filter with the UID search
            filter_str = f"(&{Setting.AUTH_LDAP_SEARCH_FILTER}{base_filter})"
        else:
            filter_str = base_filter

        # 2. Attribute List Construction
        # Using a set to prevent duplicates if config fields overlap
        attributes_to_fetch = {
            Setting.AUTH_LDAP_FIRSTNAME_FIELD,
            Setting.AUTH_LDAP_LASTNAME_FIELD,
            Setting.AUTH_LDAP_EMAIL_FIELD,
        }
        if Setting.AUTH_ROLES_MAPPING:
            attributes_to_fetch.add(Setting.AUTH_LDAP_GROUP_FIELD)

        logger.debug(
            "LDAP search for '%s' with filter '%s' in base '%s'",
            username,
            filter_str,
            Setting.AUTH_LDAP_SEARCH,
        )

        # 3. The Search Method
        # The search operation is a method of the connection object
        conn.search(
            Setting.AUTH_LDAP_SEARCH,
            filter_str,
            search_scope=ldap3.SUBTREE,
            attributes=list(attributes_to_fetch),
        )
        logger.debug("LDAP search returned: %s", conn.entries)

        # 4. Result Processing
        # Results are stored in the conn.entries property
        if len(conn.entries) > 1:
            logger.error("LDAP search for '%s' returned multiple results.", username)
            return None, None

        if conn.entries:
            # Get the first (and only) entry
            user_entry = conn.entries[0]

            # Extract DN and attributes
            user_dn = user_entry.entry_dn
            # .entry_attributes_as_dict provides a simple dict format
            user_attributes = user_entry.entry_attributes_as_dict

            return user_dn, user_attributes
        else:
            # No results found
            return None, None

    async def _ldap3_calculate_user(
        self, user: User, user_attributes: dict[str, typing.Any]
    ):
        """
        Calculate the roles for the user.

        Args:
            user (User): User object to update.
            user_attributes (dict[str, typing.Any]): User attributes from LDAP.

        Returns:
            User: Updated user object.
        """
        # Apply AUTH_ROLES_MAPPING
        user_role_keys = user_attributes.get(Setting.AUTH_LDAP_GROUP_FIELD, [])
        user = await self._handle_role_keys(user, user_role_keys)

        # Apply AUTH_USER_REGISTRATION
        if Setting.AUTH_USER_REGISTRATION:
            if not Setting.AUTH_USER_REGISTRATION_ROLE:
                logger.warning(
                    "AUTH_USER_REGISTRATION is set but AUTH_USER_REGISTRATION_ROLE is not set"
                )
                return user

            # lookup registration role in flask db
            db_roles = await self.get_roles_by_names(
                Setting.AUTH_USER_REGISTRATION_ROLE
            )
            if not db_roles:
                logger.warning(
                    "Can't find AUTH_USER_REGISTRATION_ROLE in database: %s",
                    Setting.AUTH_USER_REGISTRATION_ROLE,
                )
                return user
            await self.update(
                {}, user, list(set(r.name for r in db_roles + user.roles))
            )

        return user
