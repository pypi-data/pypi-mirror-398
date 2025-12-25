import collections
import datetime
import typing

import pydantic
import sqlalchemy.dialects.postgresql
import sqlalchemy.event
import sqlalchemy.orm

from .....const import logger
from .....db import db
from .....exceptions import raise_exception
from .....globals import g
from .....security.sqla.models import User
from .....utils import (
    AsyncTaskRunner,
    class_factory_from_dict,
    get_pydantic_model_field,
    lazy,
    prettify_dict,
    run_coroutine_in_threadpool,
    safe_call_sync,
    smart_run,
    smartdefaultdict,
    use_default_when_none,
)
from ...column import mapped_column
from ...interface import SQLAInterface
from ...model import Model
from ...session import SQLASession
from .types import AuditEntry, AuditOperation, SQLAModel

__all__ = ["audit_model_factory", "Audit"]


logger = logger.getChild("audit")

BASE_AUDIT_TABLE_NAME = "audit_log"
BASE_AUDIT_SEQUENCE = BASE_AUDIT_TABLE_NAME + "_id_seq"


def audit_model_factory(
    class_name: str = "AuditTable",
    bases: tuple[type, ...] = (Model,),
    dialects: typing.Literal["postgresql"] | None = None,
    **kwargs: typing.Any,
) -> typing.Type[SQLAModel]:
    """
    Factory function to create an SQLAlchemy model for auditing.

    Args:
        class_name (str, optional): The name of the audit table class. Defaults to "AuditTable".
        bases (tuple[type, ...], optional): The base classes for the audit table class. Defaults to (Model,).
        dialects (typing.Literal["postgresql"] | None, optional): The database dialect to use. Defaults to None.
        **kwargs (typing.Any): Additional attributes to add or override in the model.

    Returns:
        typing.Type[SQLAModel]: The SQLAlchemy model class for the audit table.
    """
    attrs = {
        "__tablename__": BASE_AUDIT_TABLE_NAME,
        "id": mapped_column(
            sqlalchemy.Integer,
            sqlalchemy.Sequence(BASE_AUDIT_SEQUENCE),
            primary_key=True,
        ),
        "created": mapped_column(
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        "table_name": mapped_column(sqlalchemy.String(256), nullable=False),
        "table_id": mapped_column(sqlalchemy.String(1024), nullable=False),
        "operation": mapped_column(sqlalchemy.String(256), nullable=False),
        "data": mapped_column(
            sqlalchemy.dialects.postgresql.JSONB
            if dialects == "postgresql"
            else sqlalchemy.JSON,
        ),
        "updates": mapped_column(
            sqlalchemy.dialects.postgresql.JSONB
            if dialects == "postgresql"
            else sqlalchemy.JSON,
        ),
        "created_by_fk": mapped_column(
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey(User.id, ondelete="SET NULL"),
            default=User.get_user_id,
        ),
        "created_by": sqlalchemy.orm.relationship(User),
        "__table_args__": (
            sqlalchemy.Index(
                "ix_audit_table_id", "table_name", "table_id", unique=False
            ),
        ),
        "__repr__": lambda self: prettify_dict(
            {
                "id": self.id,
                "created": self.created,
                "table_name": self.table_name,
                "table_id": self.table_id,
                "operation": self.operation,
                "data": self.data,
                "updates": self.updates,
            }
        ),
        **kwargs,
    }
    return class_factory_from_dict(class_name, bases, **attrs)


class Audit:
    """
    A class to handle auditing of SQLAlchemy models using session events.

    ***If the model of the audit needs to be changed, ensure that the `create_entry` method is updated accordingly***.

    ## Example:
    ```python
    import sqlalchemy
    from fastapi_rtk import Audit, Model

    @Audit.audit_model # Will audit the model and its subclasses
    @Audit.exclude_properties(["password", "secret_key"]) # Add this to ignore specific properties
    class MyModel(Model):
        __tablename__ = "my_model"
        id = mapped_column(sqlalchemy.Integer, primary_key=True)
        name = mapped_column(sqlalchemy.String(256))
        password = mapped_column(sqlalchemy.String(256))
        secret_key = mapped_column(sqlalchemy.String(256))

    @Audit.exclude_model # To exclude a model from being audited
    class MySubclassModel(MyModel):
        __tablename__ = "my_subclass_model"
        id = mapped_column(sqlalchemy.Integer, primary_key=True)
        additional_field = mapped_column(sqlalchemy.String(256))

    @Audit.audit_model
    @Audit.include_properties(["name"]) # To include only specific properties
    class AnotherModel(Model):
        __tablename__ = "another_model"
        id = mapped_column(sqlalchemy.Integer, primary_key=True)
        name = mapped_column(sqlalchemy.String(256))
        description = mapped_column(sqlalchemy.String(512))
    ```
    """

    model = lazy(lambda: audit_model_factory(), only_instance=False)
    """
    The SQLAlchemy model representing the audit table.
    """
    interfaces = smartdefaultdict[typing.Type[SQLAModel], SQLAInterface](
        lambda model: SQLAInterface(model)
    )
    """
    Dictionary mapping SQLAlchemy models to their interfaces.
    """
    schemas = dict[str, typing.Type[pydantic.BaseModel]]()
    """
    Dictionary mapping model name combined with columns with attributes to their corresponding schema.
    """

    models = list[typing.Type[SQLAModel]]()
    """
    List of models to be audited.
    """
    excluded_models = list[typing.Type[SQLAModel]]()
    """
    List of models to be excluded from auditing.
    """
    included_properties = collections.defaultdict[typing.Type[SQLAModel], list[str]](
        list[str]
    )
    """
    Dictionary mapping models to properties that should be included in auditing. When not given, all properties will be included.
    """
    excluded_properties = collections.defaultdict[typing.Type[SQLAModel], list[str]](
        list[str]
    )
    """
    Dictionary mapping models to properties that should be excluded from auditing.
    """
    mapping_insert_updates_when_no_changes = collections.defaultdict[
        typing.Type[SQLAModel], bool | None
    ](lambda: None)
    """
    Dictionary mapping models to a flag indicating whether to insert audit entries for updates even when there are no changes if the model is dirty.
    """
    mapping_insert_updates_when_no_changes_default = False
    """
    Default value for `mapping_insert_updates_when_no_changes` if not set for a specific model.
    """
    callbacks = list[
        typing.Callable[
            [AuditEntry], None | typing.Coroutine[typing.Any, typing.Any, None]
        ]
    ]()
    """
    List of callbacks to be called after adding the audit to the database.
    """
    scheduler = lazy(
        lambda cls: raise_exception(
            f"{cls.__name__}.scheduler is not configured. Please call `{cls.__name__}.run_in_background()` to configure it."
        )
    )
    """
    The scheduler for running audit inserts and callbacks in the background.
    """

    _session_callbacks_after_flush_postexec = collections.defaultdict[
        sqlalchemy.orm.Session,
        list[
            typing.Callable[[], None | typing.Coroutine[typing.Any, typing.Any, None]]
        ](),
    ](list)
    """
    Dictionary mapping SQLAlchemy sessions to their post-execution callbacks.
    """
    _session_callbacks_after_commit = collections.defaultdict[
        sqlalchemy.orm.Session,
        list[
            typing.Callable[[], None | typing.Coroutine[typing.Any, typing.Any, None]]
        ](),
    ](list)
    """
    Dictionary mapping SQLAlchemy sessions to their commit callbacks.
    """
    _session_is_commited = collections.defaultdict[SQLASession, bool](bool)
    """
    Dictionary mapping SQLAlchemy sessions to a flag indicating if they have been committed.
    """
    _run_in_background = False
    """
    Whether to insert audit entries and run callbacks in the background.
    """
    _configured = False
    """
    Flag to indicate if the audit class has been configured.
    """

    @classmethod
    def setup(cls):
        """
        Set up the audit class.

        - Attach `after_flush` event to `sqlalchemy.orm.Session` to collect audit entries and add callbacks to the session.
        - Attach `after_flush_postexec` event to `sqlalchemy.orm.Session` to run callbacks after the session flush post-execution.
        - Attach `after_commit` event to `sqlalchemy.orm.Session` to run callbacks after the session commit.
        - Attach `after_rollback` event to `sqlalchemy.orm.Session` to clear callbacks when a rollback occurs.
        """
        if cls._configured:
            return
        sqlalchemy.event.listen(sqlalchemy.orm.Session, "after_flush", cls._after_flush)
        sqlalchemy.event.listen(
            sqlalchemy.orm.Session, "after_flush_postexec", cls._after_flush_postexec
        )
        sqlalchemy.event.listen(
            sqlalchemy.orm.Session, "after_commit", cls._after_commit
        )
        sqlalchemy.event.listen(
            sqlalchemy.orm.Session, "after_rollback", cls._after_rollback
        )
        cls._configured = True
        logger.info("Audit class configured.")

    @classmethod
    def audit_model(
        cls,
        model_cls: typing.Type[SQLAModel] | None = None,
        *,
        include: list[str] | str | None = None,
        exclude: list[str] | str | None = None,
        insert_updates_when_no_changes: bool | None = None,
    ):
        """
        Decorator to register a model and its subclasses for auditing.

        Args:
            model_cls (typing.Type[SQLAModel]): The SQLAlchemy model class to audit.
            include (list[str] | str | None, optional): List of property names to include in the audit. Defaults to None.
            exclude (list[str] | str | None, optional): List of property names to exclude from the audit. Defaults to None.
            insert_updates_when_no_changes (bool | None, optional): Whether to insert audit entries for updates even when there are no changes if the model is dirty. Defaults to None.

        Returns:
            typing.Type[SQLAModel]: The audited model class.

        Raises:
            ValueError: If the model class is not provided and no include or exclude properties are specified.

        Example:
            ```python
            @Audit.audit_model # Standard usage, audits everything
            # Or, @Audit.audit_model(include="name, description") # To include specific properties
            # Or, @Audit.audit_model(exclude="password, secret_key") # To exclude specific properties
            class MyModel(Model):
                __tablename__ = "my_model"
                id = mapped_column(sqlalchemy.Integer, primary_key=True)
                name = mapped_column(sqlalchemy.String(256))
                description = mapped_column(sqlalchemy.String(512))
                created = mapped_column(sqlalchemy.DateTime, default=sqlalchemy.func.now())
                updated = mapped_column(sqlalchemy.DateTime, default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())
            ```
        """
        if include or exclude or insert_updates_when_no_changes is not None:

            def decorator(model_cls: typing.Type[SQLAModel]) -> typing.Type[SQLAModel]:
                model_cls = cls.audit_model(model_cls)
                params = [
                    (include, {}, cls.include_properties),
                    (exclude, {}, cls.exclude_properties),
                    (
                        insert_updates_when_no_changes,
                        {"decorator": True},
                        cls.insert_updates_when_no_changes,
                    ),
                ]
                for args, kwargs, func in params:
                    if args is None:
                        continue
                    if not isinstance(args, tuple):
                        args = (args,)
                    model_cls = func(*args, **kwargs)(model_cls)
                return model_cls

            return decorator

        if not model_cls:
            raise ValueError("Model class must be provided to `audit_model` decorator.")

        cls.setup()
        cls.models.append(model_cls)
        logger.info(
            f"Model {model_cls.__name__} and its subclasses registered for audit."
        )
        return model_cls

    @classmethod
    def exclude_model(cls, model_cls: typing.Type[SQLAModel]):
        """
        Decorator to exclude a model from being audited.

        Args:
            model_cls (typing.Type[SQLAModel]): The SQLAlchemy model class to exclude.

        Returns:
            typing.Type[SQLAModel]: The excluded model class.
        """
        cls.excluded_models.append(model_cls)
        logger.info(f"Model {model_cls.__name__} excluded from audit.")
        return model_cls

    @classmethod
    def include_properties(cls, properties: list[str] | str, *args, separator=","):
        """
        Decorator to include specific properties in the audit for a model.

        Args:
            properties (list[str] | str): List of property names to include or a single property name.
            *args: Additional property names to include.
            separator (str, optional): Separator to split the properties string. Defaults to ','.

        Returns:
            typing.Callable[[typing.Type[SQLAModel]], typing.Type[SQLAModel]]: A decorator that applies the inclusion.

        Example:
            ```python
            @Audit.include_properties(["name", "description"]) # To include specific properties
            # Or, @Audit.include_properties("name, description")
            # Or, @Audit.include_properties("name", "description")
            class MyModel(Model):
                __tablename__ = "my_model"
                id = mapped_column(sqlalchemy.Integer, primary_key=True)
                name = mapped_column(sqlalchemy.String(256))
                description = mapped_column(sqlalchemy.String(512))
            ```
        """
        if isinstance(properties, str):
            properties = properties.split(separator)
        properties.extend(args)

        def decorator(model_cls: typing.Type[SQLAModel]):
            cls.included_properties[model_cls].extend(properties)
            logger.info(
                f"Only properties {properties} included in audit for model {model_cls.__name__}."
            )
            return model_cls

        return decorator

    @classmethod
    def exclude_properties(cls, properties: list[str] | str, *args, separator=","):
        """
        Decorator to exclude specific properties from being audited for a model.

        Args:
            properties (list[str]): List of property names to exclude.
            *args: Additional property names to exclude.
            separator (str, optional): Separator to split the properties string. Defaults to ','.

        Returns:
            typing.Callable[[typing.Type[SQLAModel]], typing.Type[SQLAModel]]: A decorator that applies the exclusion.

        Example:
            ```python
            @Audit.exclude_properties(["password", "secret_key"]) # To exclude specific properties
            # Or, @Audit.exclude_properties("password, secret_key")
            # Or, @Audit.exclude_properties("password", "secret_key")
            class MyModel(Model):
                __tablename__ = "my_model"
                id = mapped_column(sqlalchemy.Integer, primary_key=True)
                name = mapped_column(sqlalchemy.String(256))
                password = mapped_column(sqlalchemy.String(256))
                secret_key = mapped_column(sqlalchemy.String(256))
            ```
        """
        if isinstance(properties, str):
            properties = properties.split(separator)
        properties.extend(args)

        def decorator(model_cls: typing.Type[SQLAModel]):
            cls.excluded_properties[model_cls].extend(properties)
            logger.info(
                f"Properties {properties} excluded from audit for model {model_cls.__name__}."
            )
            return model_cls

        return decorator

    @classmethod
    def insert_updates_when_no_changes(cls, value=True, *, decorator=False):
        """
        Set whether to insert audit entries for updates even when there are no changes if the model is dirty.

        Args:
            value (bool, optional): Whether to insert audit entries for updates even when there are no changes if the model is dirty. Defaults to True.
            decorator (bool, optional): Whether to use this method as a decorator. If True, the method returns a decorator function that can be applied to a model class. Defaults to False.
        """
        if decorator:

            def decorator(model_cls: typing.Type[SQLAModel]):
                cls.mapping_insert_updates_when_no_changes[model_cls] = value
                logger.info(
                    f"Set insert_updates_when_no_changes to {value} for model {model_cls.__name__}."
                )
                return model_cls

            return decorator
        cls.mapping_insert_updates_when_no_changes_default = value
        logger.info(f"Set insert_updates_when_no_changes to {value}.")

    @classmethod
    def callback(
        cls,
        func: typing.Callable[
            [AuditEntry], None | typing.Coroutine[typing.Any, typing.Any, None]
        ],
    ):
        """
        Decorator to register a callback function that will be called after an audit entry is added to the database.

        Args:
            func (typing.Callable[[AuditEntry], None | typing.Coroutine[typing.Any, typing.Any, None]]): The callback function to register.

        Returns:
            typing.Callable[[AuditEntry], None | typing.Coroutine[typing.Any, typing.Any, None]]: The registered callback function.
        """
        cls.callbacks.append(func)
        logger.info(f"Callback {func.__name__} registered.")
        return func

    @classmethod
    def run_in_background(cls, value: bool = True):
        """
        Set whether to insert audit entries and run callbacks in the background.

        Args:
            value (bool, optional): Whether to insert audit entries and run callbacks in the background. Defaults to True.
        """
        if value:
            try:
                import apscheduler.schedulers.asyncio

                cls.scheduler = apscheduler.schedulers.asyncio.AsyncIOScheduler()
                cls.scheduler.start()
            except ImportError as e:
                raise ImportError(
                    "apscheduler is required to run audit in background. Please install it with `pip install apscheduler` or add it to your `requirements.txt`."
                ) from e

        cls._run_in_background = value
        logger.info(f"Set run_in_background to {value}.")

    """
    --------------------------------------------------------------------------------------------------------
        MODEL METHODS - implemented
    --------------------------------------------------------------------------------------------------------
    """

    @classmethod
    def set_model(cls, model_cls: typing.Type[SQLAModel]):
        """
        Set the model class for the audit.

        Args:
            model_cls (typing.Type[SQLAModel]): The SQLAlchemy model class to set.
        """
        cls.model = model_cls
        logger.info(f"Audit model set to {model_cls.__name__}.")

    @classmethod
    def create_entry(cls, audit: AuditEntry):
        """
        Create an audit entry from the given audit data.

        Args:
            audit (AuditEntry): The audit entry to create.

        Returns:
            AuditTable: An instance of the audit table model with the provided audit data.
        """
        return cls.model(
            table_name=audit["model"].__tablename__,
            table_id=str(audit["pk"]),
            operation=audit["operation"],
            data=audit.get("data"),
            updates=audit.get("updates"),
            created_by_fk=g.user.id if g.user else None,
        )

    @classmethod
    async def create_table(cls):
        """
        Create the audit table in the database.
        """
        return await db.create_all(cls.model.__bind_key__, tables=[cls.model.__table__])

    @classmethod
    def create_table_sync(cls, *args, **kwargs):
        """
        Synchronous version of `create_table`.

        Args:
            *args: Positional arguments to pass to `create_table`.
            **kwargs: Keyword arguments to pass to `create_table`.

        Returns:
            T: The result of the synchronous table creation.
        """
        return run_coroutine_in_threadpool(cls.create_table(*args, **kwargs))

    @classmethod
    async def insert_entries(
        cls,
        entries: list[AuditEntry],
        model_entries: list[SQLAModel] | None = None,
        *,
        session: SQLASession | None = None,
        commit=True,
        raise_exception=False,
    ):
        """
        Insert multiple audit entries into the database.

        Args:
            entries (list[AuditEntry]): The audit entries to insert.
            model_entries (list[SQLAModel] | None, optional): Pre-created audit model instances to insert. If not provided, will create from `entries`. Defaults to None.
            session (SQLASession | None, optional): The database session to use. Defaults to None.
            commit (bool, optional): Whether to commit the session after inserting. Defaults to True.
            raise_exception (bool, optional): Whether to raise an exception if the insert fails. Defaults to False.

        Raises:
            e: The exception raised during the insert.
        """
        try:
            is_commited = cls._session_is_commited[session]
            if is_commited:
                logger.warning(
                    "Session has already been committed, creating a new session to insert audit entries."
                )
                commit = is_commited
                del cls._session_is_commited[session]
                session = None
            if not session:
                async with db.session(cls.model.__bind_key__) as session:
                    await cls.insert_entries(
                        entries,
                        model_entries,
                        session=session,
                        commit=commit,
                        raise_exception=raise_exception,
                    )
                    return
            model_entries = model_entries or [
                cls.create_entry(entry) for entry in entries
            ]
            session.add_all(model_entries)
            for entry in model_entries:
                operation = use_default_when_none(
                    getattr(entry, "operation", None), "UNKNOWN OPERATION"
                )
                table_name = use_default_when_none(
                    getattr(entry, "table_name", None), "UNKNOWN TABLE"
                )
                table_id = use_default_when_none(
                    getattr(entry, "table_id", None), "UNKNOWN ID"
                )
                entry_data = use_default_when_none(
                    getattr(entry, "data", None), {"detail": "No data"}
                )
                logger.info(f"[{operation}] {table_name} {table_id}")
                logger.debug(f"Entry data: \n{prettify_dict(entry_data)}")
            if commit:
                await smart_run(session.commit)
                # Run callbacks immediately after commit if not part of a larger transaction
                await cls._run_callbacks(entries)
            else:

                def callback_for_commit(entries=entries):
                    return cls._run_async_function_or_delegate_to_runner(
                        cls._run_callbacks, entries=entries
                    )

                cls._session_callbacks_after_commit[session].append(callback_for_commit)
        except Exception as e:
            logger.error(f"Error inserting audit entries: {e}")
            if not raise_exception:
                return
            raise e

    """
    --------------------------------------------------------------------------------------------------------
        EVENT LISTENER METHODS - implemented
    --------------------------------------------------------------------------------------------------------
    """

    @classmethod
    def _after_flush(cls, session: sqlalchemy.orm.Session, *_):
        """
        Event handler for `after_flush` event.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session that was flushed.
        """
        audit_entries = cls._get_audit_entries(session)
        if not audit_entries:
            logger.debug("No models to be audited in `after_flush`.")
            return

        model_entries = [cls.create_entry(entry) for entry in audit_entries]
        if cls._run_in_background:
            cls._session_callbacks_after_commit[session].append(
                lambda audit_entries=audit_entries,
                model_entries=model_entries: cls.scheduler.add_job(
                    cls.insert_entries,
                    args=[audit_entries, model_entries],
                    name=f"{cls.__name__}.insert_entries",
                )
            )
            return

        existing_session = (
            session
            if any(
                entry["model"].__bind_key__ == cls.model.__bind_key__
                for entry in audit_entries
            )
            else None
        )

        def callback_for_flush_postexec(
            audit_entries=audit_entries,
            model_entries=model_entries,
            existing_session=existing_session,
        ):
            return cls._run_async_function_or_delegate_to_runner(
                cls.insert_entries,
                audit_entries,
                model_entries,
                session=existing_session,
                commit=not existing_session,
            )

        cls._session_callbacks_after_flush_postexec[session].append(
            callback_for_flush_postexec
        )

    @classmethod
    def _after_flush_postexec(cls, session: sqlalchemy.orm.Session, *_):
        """
        Event handler for `after_flush_postexec` event.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session that was flushed post-execution.
        """
        callbacks = cls._session_callbacks_after_flush_postexec.pop(session, [])
        if not callbacks:
            logger.debug("No callbacks to run in `after_flush_postexec`.")
            return
        for callback in callbacks:
            callback()

    @classmethod
    def _after_commit(cls, session: sqlalchemy.orm.Session):
        """
        Event handler for `after_commit` event.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session that was committed.
        """
        cls._session_is_commited[session] = True
        callbacks = cls._session_callbacks_after_commit.pop(session, [])
        if not callbacks:
            logger.debug("No callbacks to run in `after_commit`.")
            return
        for callback in callbacks:
            callback()

    @classmethod
    def _after_rollback(cls, session: sqlalchemy.orm.Session):
        """
        Event handler for `after_rollback` event.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session that was rolled back.
        """
        cls._session_callbacks_after_flush_postexec.pop(session, None)
        cls._session_callbacks_after_commit.pop(session, None)
        logger.debug("Rolled back changes in session, clearing callbacks.")

    """
    --------------------------------------------------------------------------------------------------------
        HELPER METHODS - implemented
    --------------------------------------------------------------------------------------------------------
    """

    @classmethod
    def _get_audit_entries(cls, session: sqlalchemy.orm.Session):
        """
        Get audit entries from the given session.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session to get audit entries from.

        Returns:
            list[AuditEntry]: A list of audit entries.
        """
        return cls._process_model_operations(cls._get_model_operations(session))

    @classmethod
    def _get_model_operations(
        cls,
        session: sqlalchemy.orm.Session,
    ):
        """
        Gets a deque of models and their corresponding audit operations from the given session.

        Args:
            session (sqlalchemy.orm.Session): The SQLAlchemy session to get models and operations from.

        Returns:
            collections.deque[tuple[SQLAModel, AuditOperation, list[str], dict[str, sqlalchemy.orm.attributes.History]]]: A deque of tuples containing the model, operation, properties to audit, and updated columns with their history.
        """
        model_operation_deque = collections.deque[
            tuple[
                SQLAModel,
                AuditOperation,
                list[str],
                dict[str, sqlalchemy.orm.attributes.History],
            ]
        ]()
        for model in session.new:
            if not cls._should_audit(model):
                logger.debug(
                    f"[{AuditOperation.INSERT}] Model is not registered or excluded from audit: {model.__class__.__name__}"
                )
                continue
            if not hasattr(model, "__tablename__"):
                continue
            model_operation_deque.append(
                (model, AuditOperation.INSERT, cls._get_audit_properties(model), {})
            )
        for model in session.dirty:
            if not cls._should_audit(model):
                logger.debug(
                    f"[{AuditOperation.UPDATE}] Model is not registered or excluded from audit: {model.__class__.__name__}"
                )
                continue
            if not hasattr(model, "__tablename__"):
                continue
            if not session.is_modified(model):
                continue
            state = sqlalchemy.inspect(model)
            properties = cls._get_audit_properties(model)
            updates = {
                x.key: x.history
                for x in state.attrs
                if x.history.has_changes() and x.key in properties
            }
            model_operation_deque.append(
                (model, AuditOperation.UPDATE, properties, updates)
            )
        for model in session.deleted:
            if not cls._should_audit(model):
                logger.debug(
                    f"[{AuditOperation.DELETE}] Model is not registered or excluded from audit: {model.__class__.__name__}"
                )
                continue
            if not hasattr(model, "__tablename__"):
                continue
            model_operation_deque.append((model, AuditOperation.DELETE, [], {}))
        return model_operation_deque

    @classmethod
    def _process_model_operations(
        cls,
        model_operation_deque: collections.deque[
            tuple[
                SQLAModel,
                AuditOperation,
                list[str],
                dict[str, sqlalchemy.orm.attributes.History],
            ]
        ],
        *,
        result: list[AuditEntry] | None = None,
    ):
        """
        Process model operations from the given deque.

        Args:
            model_operation_deque (collections.deque[tuple[SQLAModel, AuditOperation, list[str], dict[str, sqlalchemy.orm.attributes.History]]]): The model operations to process.
            result (list[AuditEntry] | None, optional): The list to store the processed audit entries. Defaults to None. Used for recursion.

        Returns:
            list[AuditEntry]: A list of audit entries processed from the model operations.
        """
        result = result if result is not None else []
        while model_operation_deque:
            dat = model_operation_deque.popleft()
            model, operation, model_keys, update_history = dat
            if operation == AuditOperation.DELETE:
                result.append(
                    AuditEntry(
                        model=model,
                        operation=AuditOperation.DELETE,
                        pk=str(model.id_),
                    )
                )
            else:
                datamodel = cls.interfaces[model.__class__]
                schema_key = f"{model.__class__.__name__}-{'-'.join(model_keys)}"
                schema = cls.schemas.get(schema_key)
                if not schema:
                    cls.schemas[schema_key] = schema = datamodel.generate_schema(
                        model_keys,
                        with_id=False,
                        with_name=False,
                        optional=True,
                        related_kwargs={"with_property": False},
                    )
                data = schema.model_validate(model).model_dump(mode="json")
                if operation == AuditOperation.INSERT:
                    updates = {k: (None, v) for k, v in data.items()}
                    result.append(
                        AuditEntry(
                            model=model,
                            operation=AuditOperation.INSERT,
                            pk=str(model.id_),
                            data=data,
                            updates=updates,
                        )
                    )
                elif operation == AuditOperation.UPDATE:
                    update_schema_key = (
                        f"{model.__class__.__name__}-{'-'.join(update_history.keys())}"
                    )
                    update_schema = cls.schemas.get(update_schema_key)
                    if not update_schema:
                        cls.schemas[update_schema_key] = update_schema = (
                            datamodel.generate_schema(
                                update_history.keys(),
                                with_id=False,
                                with_name=False,
                                optional=True,
                                related_kwargs={"with_property": False},
                            )
                        )
                    old_data = {}
                    for col, hist in update_history.items():
                        old_value = hist.deleted if hist.deleted else None
                        old_value = (
                            old_value[0]
                            if old_value and len(old_value) == 1
                            else old_value
                        )
                        if datamodel.is_relation(col):
                            related_schema = get_pydantic_model_field(
                                update_schema, col
                            )
                            if datamodel.is_relation_one_to_one(
                                col
                            ) or datamodel.is_relation_many_to_one(col):
                                if old_value is not None:
                                    old_value = related_schema.model_validate(
                                        old_value
                                    ).model_dump(mode="json")
                            else:
                                # For one-to-many and many-to-many relations, we need to calculate the old value
                                old_value = list(hist.unchanged) + list(hist.deleted)
                                old_value = [
                                    related_schema.model_validate(x).model_dump(
                                        mode="json"
                                    )
                                    for x in old_value
                                ]

                        old_data[col] = old_value
                    old_data = update_schema.model_validate(
                        old_data, from_attributes=False
                    ).model_dump(mode="json")
                    updates = {k: (old_data[k], data[k]) for k in old_data if k in data}
                    if not updates:
                        logger.debug(
                            f"[{AuditOperation.UPDATE}] No changes detected for model: {model.__class__.__name__} {model.id_}"
                        )
                        if not use_default_when_none(
                            cls.mapping_insert_updates_when_no_changes[model.__class__],
                            cls.mapping_insert_updates_when_no_changes_default,
                        ):
                            continue
                    result.append(
                        AuditEntry(
                            model=model,
                            operation=AuditOperation.UPDATE,
                            pk=str(model.id_),
                            data=data,
                            updates=updates,
                        )
                    )
        return result

    @classmethod
    def _should_audit(cls, model: SQLAModel):
        """
        Check if a model should be audited.

        Args:
            model (SQLAModel): The SQLAlchemy model instance to check.

        Returns:
            bool: True if the model should be audited, False otherwise.
        """
        return model.__class__ not in cls.excluded_models and (
            model.__class__ in cls.models
            or any(issubclass(model.__class__, m) for m in cls.models)
        )

    @classmethod
    async def _run_callbacks(cls, entries: list[AuditEntry]):
        """
        Run registered callbacks for the given audit entries in parallel.

        Args:
            entries (list[AuditEntry]): The audit entries to process.
        """
        async with AsyncTaskRunner():
            for entry in entries:
                for callback in cls.callbacks:
                    AsyncTaskRunner.add_task(
                        lambda callback=callback, entry=entry: smart_run(
                            callback, entry
                        )
                    )

    @classmethod
    def _run_async_function_or_delegate_to_runner(
        cls,
        async_function: typing.Callable[
            ..., typing.Coroutine[typing.Any, typing.Any, None]
        ],
        *args,
        kwargs_in_task_runner: dict[str, typing.Any] | None = None,
        **kwargs,
    ):
        """
        Run an async function in the current threadpool or delegate it to the current AsyncTaskRunner if available.

        Args:
            async_function (typing.Callable[ ..., typing.Coroutine[typing.Any, typing.Any, None] ]): The async function to run.
            *args: Positional arguments to pass to the async function.
            kwargs_in_task_runner (dict[str, typing.Any] | None, optional): Additional keyword arguments to pass to function when run in AsyncTaskRunner. Defaults to None.
            **kwargs: Keyword arguments to pass to the async function.

        Returns:
            typing.Any: The result of the async function or None if delegated.
        """
        try:
            return safe_call_sync(async_function(*args, **kwargs))
        except Exception as e:
            try:
                task_runner = AsyncTaskRunner.get_current_runner()
                params = {**kwargs, **(kwargs_in_task_runner or {})}
                task_runner.add_task(lambda: async_function(*args, **params))
                logger.warning(
                    f"Delegated async function {async_function.__name__} to AsyncTaskRunner due to error running in threadpool"
                )
            except RuntimeError:
                logger.error(
                    f"Error running async function {async_function.__name__} in threadpool and no AsyncTaskRunner is available to delegate the task to: {e}"
                )

    @classmethod
    def _get_audit_properties(cls, model: SQLAModel):
        """
        Get the list of properties to include in the audit for the given model.

        Args:
            model (SQLAModel): The SQLAlchemy model instance to get included properties for.

        Returns:
            list[str]: A list of included property names.
        """
        excluded_properties = set[str]()
        for excluded_model in cls.excluded_properties:
            if model.__class__ == excluded_model or issubclass(
                model.__class__, excluded_model
            ):
                excluded_properties.update(cls.excluded_properties[excluded_model])
        state = sqlalchemy.inspect(model)
        return cls.included_properties[model.__class__] or [
            x for x in state.attrs.keys() if x not in excluded_properties
        ]
