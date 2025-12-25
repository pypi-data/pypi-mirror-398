import abc

__all__ = ["AbstractSession"]


class AbstractSession(abc.ABC):
    """
    Abstract base class for a session of a database or other persistent storage.
    """
