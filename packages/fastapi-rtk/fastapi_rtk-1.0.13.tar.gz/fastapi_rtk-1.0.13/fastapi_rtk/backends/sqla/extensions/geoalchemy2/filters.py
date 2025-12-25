from typing import Any

import fastapi
from sqlalchemy import Select, func

from .....exceptions import HTTPWithValidationException
from .....lang import lazy_text
from ...filters import (
    BaseFilter,
    FilterContains,
    FilterEqual,
    FilterNotContains,
    FilterNotEqual,
    SQLAFilterConverter,
)

__all__ = [
    "GeoBaseFilter",
    "GeoFilterEqual",
    "GeoFilterNotEqual",
    "GeoFilterContains",
    "GeoFilterNotContains",
    "GeoFilterIntersects",
    "GeoFilterNotIntersects",
    "GeoFilterOverlaps",
    "GeoFilterNotOverlaps",
]


class GeoBaseFilter(BaseFilter):
    def _convert_value(self, value: Any, col: str, check=False) -> Any:
        try:
            value = self.datamodel.geometry_converter.two_way_converter(
                value, self._get_column(col).type.geometry_type if check else ""
            )
        except ValueError as e:
            raise HTTPWithValidationException(
                fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                "value_error",
                "query",
                "filters",
                f"Value error, {e}",
                value,
            )

        if isinstance(value, dict):
            return func.ST_GeomFromGeoJSON(value)

        return func.ST_GeomFromEWKT(value)


class GeoFilterEqual(GeoBaseFilter, FilterEqual):
    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            func.ST_Equals(self._get_column(col), self._convert_value(value, col, True))
        )


class GeoFilterNotEqual(GeoBaseFilter, FilterNotEqual):
    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            ~func.ST_Equals(
                self._get_column(col), self._convert_value(value, col, True)
            )
        )


class GeoFilterContains(GeoBaseFilter, FilterContains):
    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            func.ST_Contains(self._get_column(col), self._convert_value(value, col))
        )


class GeoFilterNotContains(GeoBaseFilter, FilterNotContains):
    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            ~func.ST_Contains(self._get_column(col), self._convert_value(value, col))
        )


class GeoFilterIntersects(GeoBaseFilter):
    name = lazy_text("Intersects")
    arg_name = "int"

    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            func.ST_Intersects(self._get_column(col), self._convert_value(value, col))
        )


class GeoFilterNotIntersects(GeoBaseFilter):
    name = lazy_text("Not Intersects")
    arg_name = "nint"

    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            ~func.ST_Intersects(self._get_column(col), self._convert_value(value, col))
        )


class GeoFilterOverlaps(GeoBaseFilter):
    name = lazy_text("Overlaps")
    arg_name = "ovl"

    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            func.ST_Overlaps(self._get_column(col), self._convert_value(value, col))
        )


class GeoFilterNotOverlaps(GeoBaseFilter):
    name = lazy_text("Not Overlaps")
    arg_name = "novl"

    def apply(self, stmt: Select, col: str, value: Any) -> Select:
        return stmt.filter(
            ~func.ST_Overlaps(self._get_column(col), self._convert_value(value, col))
        )


SQLAFilterConverter.conversion_table += (
    (
        "is_geometry",
        [
            GeoFilterEqual,
            GeoFilterNotEqual,
            GeoFilterContains,
            GeoFilterNotContains,
            GeoFilterIntersects,
            GeoFilterNotIntersects,
            GeoFilterOverlaps,
            GeoFilterNotOverlaps,
        ],
    ),
)
