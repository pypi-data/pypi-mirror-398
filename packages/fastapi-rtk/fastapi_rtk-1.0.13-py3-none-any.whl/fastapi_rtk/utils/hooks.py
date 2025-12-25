import functools
import typing

__all__ = ["hooks"]


def hooks(
    pre: typing.Callable[..., None] | None = None,
    post: typing.Callable[..., None] | None = None,
):
    """
    Decorator to add optional pre and post hook methods to a function.

    Args:
        pre (typing.Callable[..., None] | None): Function to run before the main function. Defaults to None.
        post (typing.Callable[..., None] | None): Function to run after the main function. Defaults to None.

    Returns:
        typing.Callable[..., typing.Any]: The decorated function.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if pre:
                pre(*args, **kwargs)
            result = func(*args, **kwargs)
            if post:
                post(result, *args, **kwargs)
            return result

        return wrapper

    return decorator
