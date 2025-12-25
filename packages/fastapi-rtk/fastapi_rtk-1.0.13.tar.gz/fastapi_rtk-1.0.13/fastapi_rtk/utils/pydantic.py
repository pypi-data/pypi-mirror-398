import typing

import pydantic

__all__ = ["generate_schema_from_typed_dict", "get_pydantic_model_field"]


def generate_schema_from_typed_dict(typed_dict: type):
    """
    Generate a Pydantic model schema from a TypedDict.
    Args:
        typed_dict (type): A type that is a subclass of dict, typically a TypedDict.
    Returns:
        BaseModel: A Pydantic model generated from the TypedDict.
    Raises:
        TypeError: If the provided typed_dict is not a type or not a subclass of dict.
    """
    if not isinstance(typed_dict, type) or not issubclass(typed_dict, dict):
        raise TypeError("typed_dict must be a type that is a subclass of dict")

    fields = {}
    for key, val in typed_dict.__annotations__.items():
        if getattr(val, "__origin__", None) is typing.NotRequired:
            fields[key] = (val.__args__[0], pydantic.Field(None))
        else:
            fields[key] = (val, pydantic.Field(...))
    return pydantic.create_model(typed_dict.__name__, **fields)


def get_pydantic_model_field(model_cls: typing.Type[pydantic.BaseModel], field: str):
    """
    Get the Pydantic model class for a specific field in a Pydantic model.

    Also works if the field is a list of Pydantic models.

    Args:
        model_cls (typing.Type[pydantic.BaseModel]): The Pydantic model class.
        field (str): The name of the field.

    Returns:
        typing.Type[pydantic.BaseModel] | None: The Pydantic model class for the field, or None if not found.
    """
    annotation = model_cls.model_fields.get(field).annotation
    field_types = _get_list_of_singular_type(annotation)
    return next(
        (
            t
            for t in field_types
            if isinstance(t, type) and issubclass(t, pydantic.BaseModel)
        ),
        None,
    )


def _get_list_of_singular_type(type_or_union: type) -> list[type]:
    """
    Recursively extract all singular (leaf) types from a typing.Union, typing.List, etc.

    Args:
        type_or_union (type): The type to analyze, which may be a generic type like Union or List.

    Returns:
        list[type]: A list of singular types extracted from the input type.
    """
    args = typing.get_args(type_or_union)
    if not args:
        # Base case: not a generic type
        return [type_or_union]
    result = []
    for arg in args:
        result.extend(_get_list_of_singular_type(arg))
    return result
