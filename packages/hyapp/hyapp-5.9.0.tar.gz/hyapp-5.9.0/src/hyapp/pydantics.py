from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, ClassVar, TypeVar

from frozendict import frozendict
from frozendict.cool import deepfreeze
from pydantic_core.core_schema import (
    CoreSchema,
    chain_schema,
    dict_schema,
    is_instance_schema,
    json_or_python_schema,
    no_info_plain_validator_function,
    plain_serializer_function_ser_schema,
    union_schema,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue


class _PydanticFrozenDictAnnotation:
    """https://github.com/pydantic/pydantic/discussions/8721"""

    _cast_func: ClassVar[Callable[[Any], Any]] = frozendict

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        from_dict_schema = chain_schema([dict_schema(), no_info_plain_validator_function(cls._cast_func)])
        return json_or_python_schema(
            json_schema=from_dict_schema,
            python_schema=union_schema([is_instance_schema(frozendict), from_dict_schema]),
            serialization=plain_serializer_function_ser_schema(dict),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(dict_schema())


class _PydanticDeepFrozenDictAnnotation(_PydanticFrozenDictAnnotation):
    """
    A hack to handle multi-layered frozen dicts.
    Ideally, recursive use of the normal form should work,
    but no such luck.
    WARNING: does not support pydantic models inside the structure (forces them into frozendicts).
    """

    _cast_func: ClassVar[Callable[[Any], Any]] = deepfreeze


_K = TypeVar("_K")
_V = TypeVar("_V")
PydanticFrozenDict = Annotated[frozendict[_K, _V], _PydanticFrozenDictAnnotation]
PydanticDeepFrozenDict = Annotated[frozendict[_K, _V], _PydanticDeepFrozenDictAnnotation]
