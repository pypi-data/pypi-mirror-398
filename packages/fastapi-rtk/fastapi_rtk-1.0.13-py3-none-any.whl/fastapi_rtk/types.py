import sqlalchemy.dialects.postgresql as postgresql
from sqlalchemy import types as sa_types

from .exceptions import FastAPIReactToolkitException
from .globals import g
from .utils import lazy

__all__ = [
    "ListColumn",
    "JSONBListColumn",
    "FileColumn",
    "ImageColumn",
    "FileColumns",
    "ImageColumns",
    "JSONBFileColumns",
    "JSONBImageColumns",
]


class ListColumn(sa_types.TypeDecorator):
    """
    Extends SQLAlchemy to support and mostly identify a List Column
    """

    impl = sa_types.JSON
    cache_ok = True

    def __init__(self, col_type: type | None = None, *args, **kwargs):
        """
        Initializes the ListColumn with a specific column type.

        Args:
            col_type (type | None, optional): The type of the items in the list. When given, the column will attempt to coerce the items in the list to this type. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.col_type = col_type

    def process_bind_param(self, value, dialect):
        if not value:
            return value
        if not isinstance(value, list):
            raise ValueError("Value must be a list")
        if self.col_type:
            value = [self.col_type(v) for v in value]
        return value


class JSONBListColumn(ListColumn):
    """
    Extends ListColumn to use PostgreSQL's JSONB type.
    """

    impl = postgresql.JSONB


class BaseFileColumn:
    manager = lazy(lambda: g.file_manager)
    origin = "g.file_manager"

    def __init__(self, allowed_extensions: list[str] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_extensions is None:
            allowed_extensions = self.manager.allowed_extensions
        else:
            # Check whether all extensions are in the allowed extensions from `g.file_manager`
            if self.manager.allowed_extensions is not None and not all(
                ext in self.manager.allowed_extensions for ext in allowed_extensions
            ):
                raise FastAPIReactToolkitException(
                    f"Some extensions are not in the allowed extensions from {self.origin}",
                )
        self.allowed_extensions = allowed_extensions


class FileColumn(BaseFileColumn, sa_types.TypeDecorator):
    """
    Extends SQLAlchemy to support and mostly identify a File Column.
    """

    impl = sa_types.Text
    cache_ok = True


class ImageColumn(BaseFileColumn, sa_types.TypeDecorator):
    """
    Extends SQLAlchemy to support and mostly identify an Image Column.
    """

    impl = sa_types.Text
    cache_ok = True
    manager = lazy(lambda: g.image_manager)
    origin = "g.image_manager"

    def __init__(
        self,
        allowed_extensions: list[str] | None = None,
        thumbnail_size=(20, 20, True),
        size=(100, 100, True),
        *args,
        **kwargs,
    ):
        super().__init__(allowed_extensions, *args, **kwargs)
        self.thumbnail_size = thumbnail_size
        self.size = size


class FileColumns(FileColumn, ListColumn):
    """
    A column that represents a list of files.
    """

    impl = ListColumn


class ImageColumns(ImageColumn, ListColumn):
    """
    A column that represents a list of images.
    """

    impl = ListColumn


class JSONBFileColumns(FileColumn, JSONBListColumn):
    """
    A column that represents a list of files stored as JSONB.
    """

    impl = JSONBListColumn


class JSONBImageColumns(ImageColumn, JSONBListColumn):
    """
    A column that represents a list of images stored as JSONB.
    """

    impl = JSONBListColumn
