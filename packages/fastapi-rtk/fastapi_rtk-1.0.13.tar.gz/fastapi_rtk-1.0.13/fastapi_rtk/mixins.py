from .const import logger
from .utils import lazy

__all__ = ["LoggerMixin"]


class LoggerMixin:
    """
    A mixin that provides a logger for the class.
    """

    logger = lazy(lambda self: logger.getChild(self.__class__.__name__))
