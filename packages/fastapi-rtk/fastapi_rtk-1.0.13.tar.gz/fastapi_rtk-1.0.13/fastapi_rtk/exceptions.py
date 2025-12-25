import typing

import fastapi
import pydantic

from .utils import T

__all__ = [
    "raise_exception",
    "FastAPIReactToolkitException",
    "RolesMismatchException",
    "HTTPWithValidationException",
]


def raise_exception(message: str, return_type: typing.Type[T] | None = None) -> T:
    """
    Raise a FastAPIReactToolkitException with the given message.

    Args:
        message (str): The error message.
        return_type (typing.Type[T] | None, optional): The expected return type. Defaults to None.

    Raises:
        FastAPIReactToolkitException: Always raised.

    Returns:
        T: The return value.
    """
    raise FastAPIReactToolkitException(message)


class FastAPIReactToolkitException(Exception):
    """Base exception for FastAPI React Toolkit errors."""


class RolesMismatchException(FastAPIReactToolkitException):
    """Exception raised when the roles do not match the expected roles."""


class HTTPWithValidationException(fastapi.HTTPException):
    """
    Custom HTTP Exception for FastAPI with validation details.
    """

    URL = f"https://errors.pydantic.dev/{pydantic.version.version_short()}/v"
    _no_input = object()

    def __init__(
        self,
        status_code: int,
        type: str,
        location_type: typing.Literal["path", "query", "body"],
        field: str,
        msg: str,
        input: typing.Any = _no_input,
        headers: typing.Dict[str, str] | None = None,
    ):
        """
        Initialize the HTTPWithValidationException.

        Args:
            status_code (int): HTTP status code for the exception.
            type (str): Type of the error (e.g., "string_type", "validation_error").
            location_type (typing.Literal["path", "query", "body"]): Location type of the error, either "path", "query", or "body".
            field (str): Field name where the error occurred.
            msg (str): Error message describing the validation issue.
            input (typing.Any, optional): Optional input value that caused the error. Defaults to _no_input.
            headers (typing.Dict[str, str] | None, optional): Optional headers to include in the response. Defaults to None.
        """
        obj = {"type": type, "loc": [location_type, field], "msg": msg}
        if input is not self._no_input:
            if isinstance(input, pydantic.BaseModel):
                input = input.model_dump(mode="json")
            else:
                input = str(input)
            obj["input"] = input
        obj["url"] = f"{self.URL}/{type}"

        super().__init__(status_code, [obj], headers)
