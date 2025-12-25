import contextlib

__all__ = ["multiple_async_contexts"]


@contextlib.asynccontextmanager
async def multiple_async_contexts(
    contexts: list[contextlib.AbstractAsyncContextManager],
):
    """
    Async context manager to enter multiple async contexts.

    Args:
        contexts (list): A list of async context managers to enter.

    Yields:
        list: A list of entered context values.
    """
    async with contextlib.AsyncExitStack() as stack:
        entered = [await stack.enter_async_context(ctx) for ctx in contexts]
        yield entered
