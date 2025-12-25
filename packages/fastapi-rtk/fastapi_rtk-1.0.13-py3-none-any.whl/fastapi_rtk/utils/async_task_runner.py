import asyncio
import contextvars
import functools
import inspect
import traceback as tb
import typing

from .prettify_dict import prettify_dict

__all__ = ["AsyncTaskRunner"]

T = typing.TypeVar("T")


class CallerInfo(typing.TypedDict):
    """
    Represents information about the caller of a function.
    This is used to capture the context in which an async task was added.
    """

    filename: str
    lineno: int
    name: str


class AsyncTaskRunnerException(Exception):
    """
    Base exception for AsyncTaskRunner-related errors.
    """


class AsyncTaskException(AsyncTaskRunnerException):
    def __init__(
        self, *args, original_exception: Exception, caller: CallerInfo | None = None
    ):
        super().__init__(*args)
        self.original_exception = original_exception
        self.caller = caller


class ResultAccessor(typing.Generic[T]):
    """Helper class that can be awaited OR accessed directly."""

    def __init__(self, task: "AsyncTask[T]"):
        self._task = task

    def __await__(self):
        """Allow awaiting: await task.result"""
        return self._task.__await__()

    def __repr__(self) -> str:
        """Direct access without await - returns value or raises error."""
        return repr(self._ensure_result())

    def __str__(self) -> str:
        """Direct access without await - returns value or raises error."""
        return str(self._ensure_result())

    # Make it behave like the actual value when accessed
    def __getattr__(self, name):
        return getattr(self._ensure_result(), name)

    def _ensure_result(self):
        if not hasattr(self._task, "_result"):
            raise RuntimeError(
                "Task has not been executed yet. Await the task to get the result."
            )
        return self._task._result


class AsyncTask(typing.Generic[T]):
    """
    Represents a task to be run asynchronously.

    This is a callable that returns an awaitable (coroutine) or a coroutine directly.
    """

    def __init__(
        self,
        task: typing.Callable[..., typing.Awaitable[T]] | typing.Awaitable[T],
        /,
        caller: CallerInfo | None = None,
        tags: list[str] | None = None,
    ):
        self.task = task
        self.caller = caller
        self.tags = tags or []

    @property
    def result(self):
        """
        Provides access to the result of the task.

        Returns:
            ResultAccessor[T]: An accessor that can be awaited or accessed directly.
        """
        return ResultAccessor(self)

    def __call__(self):
        return self._run()

    def __await__(self):
        return self._run().__await__()

    async def _run(self):
        """
        Runs the task and caches the result.

        Returns:
            T: The result of the task.
        """
        if hasattr(self, "_result"):
            return self._result

        try:
            coro = self.task
            if callable(coro):
                coro = coro()
            self._result = await coro
            return self._result
        except Exception as e:
            raise AsyncTaskException(
                str(e), original_exception=e, caller=self.caller
            ) from e


class AsyncTaskRunner:
    """
    A context manager for queuing and running async tasks at the end of an async with block.

    Supports nested contexts and is safe in multithreaded async environments.

    You can add either a callable that returns an awaitable (coroutine), a normal function, or a coroutine directly. But a callable is preferred
    to avoid warning about "coroutine was never awaited" in case the task fails to run.

    Example:

    Some async function that you want to run at the end of the context:
    ```python
    async def some_async_function():
        # Some asynchronous operation
        await asyncio.sleep(1)
        print("Task completed")
    ```

    Using the AsyncTaskRunner class:
    ```python
    from fastapi_rtk import AsyncTaskRunner

    # Using the AsyncTaskRunner class directly
    async with AsyncTaskRunner():
        AsyncTaskRunner.add_task(lambda: some_async_function())
        # The task will be executed when exiting the context
    ```

    Using the AsyncTaskRunner class with a variable:
    ```python
    from fastapi_rtk import AsyncTaskRunner

    # Using the AsyncTaskRunner class with a variable
    async with AsyncTaskRunner() as runner:
        runner.add_task(lambda: some_async_function())
        # The task will be executed when exiting the context

    # Using the AsyncTaskRunner class with a variable and nested context
    async with AsyncTaskRunner() as runner:
        runner.add_task(lambda: some_async_function())
        async with AsyncTaskRunner() as nested_runner:
            nested_runner.add_task(lambda: some_async_function())
            # The task will be executed when exiting the nested context
    # The task will be executed when exiting the outer context
    ```
    """

    # Each context will get a stack of task lists to support nesting
    _task_stack: contextvars.ContextVar[typing.Optional[list[list[AsyncTask]]]] = (
        contextvars.ContextVar("_task_stack", default=None)
    )
    _runner_stack: contextvars.ContextVar[typing.Optional[list["AsyncTaskRunner"]]] = (
        contextvars.ContextVar("_runner_stack", default=None)
    )

    def __init__(self, run_tasks_even_if_exception=False):
        """
        Initializes the AsyncTaskRunner.

        Args:
            run_tasks_even_if_exception (bool, optional): Whether to run tasks even if an exception occurs in the context. Defaults to False.
        """
        self.run_tasks_even_if_exception = run_tasks_even_if_exception

    @typing.overload
    @classmethod
    def add_task(
        cls,
        task: typing.Callable[..., typing.Awaitable[T]]
        | typing.Awaitable[T]
        | AsyncTask[T],
        *,
        tags: list[str] | None = None,
        instance: "AsyncTaskRunner | None" = None,
    ) -> AsyncTask[T]: ...

    @typing.overload
    @classmethod
    def add_task(
        cls,
        task1: typing.Callable[..., typing.Awaitable[T]]
        | typing.Awaitable[T]
        | AsyncTask[T],
        task2: typing.Callable[..., typing.Awaitable[T]]
        | typing.Awaitable[T]
        | AsyncTask[T],
        *tasks: typing.Callable[..., typing.Awaitable[T]]
        | typing.Awaitable[T]
        | AsyncTask[T],
        tags: list[str] | None = None,
        instance: "AsyncTaskRunner | None" = None,
    ) -> list[AsyncTask[T]]: ...
    @classmethod
    def add_task(
        cls,
        *tasks: typing.Callable[..., typing.Awaitable[T]]
        | typing.Awaitable[T]
        | AsyncTask[T],
        tags: list[str] | None = None,
        instance: "AsyncTaskRunner | None" = None,
    ):
        """
        Adds one or more tasks to the current context's task list. The tasks will be executed when exiting the context.

        Args:
            tags (list[str] | None, optional): Tags to associate with the tasks. Defaults to None.
            instance (AsyncTaskRunner | None, optional): The AsyncTaskRunner instance to add tasks to. Defaults to None.

        Returns:
            AsyncTask[T] | list[AsyncTask[T]]: The added task(s).
        """
        task_list = cls._get_current_task_list("add_task", instance=instance)
        # Get caller info
        frame = inspect.currentframe()
        caller = inspect.getouterframes(frame, 2)[1] if frame else None

        async_tasks: list[AsyncTask[T]] = [
            AsyncTask(
                task,
                caller=CallerInfo(
                    filename=caller.filename if caller else "<unknown>",
                    lineno=caller.lineno if caller else 0,
                    name=task.__name__ if callable(task) else "<coroutine>",
                ),
                tags=tags,
            )
            if not isinstance(task, AsyncTask)
            else task
            for task in tasks
        ]
        task_list.extend(async_tasks)
        return async_tasks if len(async_tasks) > 1 else async_tasks[0]

    @classmethod
    def remove_tasks_by_tag(
        cls, tag: str, *, instance: "AsyncTaskRunner | None" = None
    ):
        """
        Removes tasks with the specified tag from the current context's task list.

        Args:
            tag (str): The tag to filter tasks by.
        """
        task_list = cls._get_current_task_list("remove_tasks_by_tag", instance=instance)
        cls._update_current_task_list(
            [task for task in task_list if tag not in task.tags], instance=instance
        )

    @classmethod
    def get_current_runner(cls):
        """
        Retrieves the current AsyncTaskRunner instance from the context stack.

        Raises:
            RuntimeError: If called outside of a context.

        Returns:
            AsyncTaskRunner: The current AsyncTaskRunner instance.
        """
        stack = cls._get_current_runner_stack("get_current_runner")
        return stack[-1]

    async def __aenter__(self):
        self._handle_enter_stack()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        stack = self._get_current_stack("__aexit__")
        tasks = self._task_list
        stack.pop()  # Remove the current context's task list
        self._handle_exit_stack()

        if exc_type and not self.run_tasks_even_if_exception:
            return

        if tasks:
            exceptions_with_index = list[tuple[AsyncTaskException, int]]()
            futures = await asyncio.gather(
                *(task() for task in tasks), return_exceptions=True
            )
            for index, future in enumerate(futures):
                if isinstance(future, AsyncTaskException):
                    # Handle exceptions from tasks
                    exceptions_with_index.append((future, index))

            if exceptions_with_index:
                raise AsyncTaskRunnerException(
                    f"\n{
                        prettify_dict(
                            {
                                'message': 'One or more tasks failed.',
                                'exceptions': {
                                    f'Task {index + 1}': {
                                        'message': str(exc),
                                        'caller': exc.caller,
                                        'traceback': ''.join(
                                            tb.format_exception(exc.original_exception)
                                        ),
                                    }
                                    for exc, index in exceptions_with_index
                                },
                            }
                        )
                    }"
                )

    @classmethod
    def _get_current_task_list(
        cls, func_name: str, *, instance: "AsyncTaskRunner | None" = None
    ):
        """
        Retrieves the current task list from the context stack. If an instance is provided, it returns the task list from that instance.

        Args:
            func_name (str): The name of the function requesting the task list.
            instance (AsyncTaskRunner | None, optional): The instance to retrieve the task list from. Defaults to None.

        Raises:
            RuntimeError: If called outside of a context.

        Returns:
            list[AsyncTask]: The current task list.
        """
        if instance:
            return instance._task_list
        return cls._get_current_stack(func_name)[-1]

    @classmethod
    def _update_current_task_list(
        cls,
        new_task_list: list[AsyncTask],
        *,
        instance: "AsyncTaskRunner | None" = None,
    ):
        """
        Updates the current task list in the context stack. If an instance is provided, it updates the task list in that instance.

        Args:
            new_task_list (list[AsyncTask]): The new task list to set.
            instance (AsyncTaskRunner | None, optional): The instance to update the task list in. Defaults to None.

        Raises:
            RuntimeError: If called outside of a context.
        """
        task_list = cls._get_current_task_list(
            "update_current_task_list", instance=instance
        )
        task_list.clear()
        task_list.extend(new_task_list)

    @classmethod
    def _get_current_stack(cls, func_name: str):
        """
        Retrieves the current task stack from the context variable.

        Args:
            func_name (str): The name of the function requesting the task stack.

        Raises:
            RuntimeError: If called outside of a context.

        Returns:
            list[list[AsyncTask]]: The current task stack.
        """
        stack = cls._task_stack.get()
        if stack is None:
            raise RuntimeError(
                f"{cls.__name__}.{func_name}() called outside of context. "
                f"Use `async with {cls.__name__}():` before calling this."
            )
        return stack

    @classmethod
    def _get_current_runner_stack(cls, func_name: str):
        """
        Retrieves the current runner stack from the context variable.

        Args:
            func_name (str): The name of the function requesting the runner stack.

        Raises:
            RuntimeError: If called outside of a context.

        Returns:
            list[AsyncTaskRunner]: The current runner stack.
        """
        stack = cls._runner_stack.get()
        if stack is None:
            raise RuntimeError(
                f"{cls.__name__}.{func_name}() called outside of context. "
                f"Use `async with {cls.__name__}():` before calling this."
            )
        return stack

    def _handle_enter_stack(self):
        """
        Handles the entry into a new context by initializing or updating the task and runner stacks.
        """
        self._handle_init_stack()
        stack, runner_stack = (
            self._get_current_stack(""),
            self._get_current_runner_stack(""),
        )
        self._task_list = list[AsyncTask]()
        stack.append(self._task_list)  # Push a new task list for this context
        runner_stack.append(self)  # Push this instance to the runner stack

        # Modify instance methods to bind self
        self.add_task = functools.partial(self.__class__.add_task, instance=self)
        self.remove_tasks_by_tag = functools.partial(
            self.__class__.remove_tasks_by_tag, instance=self
        )

    def _handle_exit_stack(self):
        """
        Cleans up the context variables for task and runner stacks if they were initialized by this instance.
        """
        if self._token:
            self._task_stack.reset(self._token)
            self._token = None
        if self._runner_token:
            self._runner_stack.reset(self._runner_token)
            self._runner_token = None

    def _handle_init_stack(self):
        """
        Ensures that the context variables for task and runner stacks are initialized.
        """
        try:
            self._get_current_stack("")
            self._token = None  # Only reset when we set a new stack
        except RuntimeError:
            self._token = self._task_stack.set(list[list[AsyncTask]]())
        try:
            self._get_current_runner_stack("")
            self._runner_token = None  # Only reset when we set a new stack
        except RuntimeError:
            self._runner_token = self._runner_stack.set(list["AsyncTaskRunner"]())
