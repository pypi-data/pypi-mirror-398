from __future__ import annotations

import datetime
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

import orjson

TJSONScalar = None | bool | int | float | str
TJSONParsed = dict[str, "TJSONParsed"] | list["TJSONParsed"] | TJSONScalar
TJSONDumpable = Mapping[str, "TJSONDumpable"] | Sequence["TJSONDumpable"] | TJSONScalar
TJSONScalarExt = TJSONScalar | datetime.datetime | Decimal
TJSONDumpableExt = Mapping[str, "TJSONDumpableExt"] | Sequence["TJSONDumpableExt"] | TJSONScalarExt | TJSONDumpable


def json_default(value: Any) -> TJSONParsed:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError


def json_dumps(value: TJSONDumpableExt) -> bytes:
    return orjson.dumps(value, default=json_default)


def json_dumps_text(value: TJSONDumpableExt) -> str:
    return json_dumps(value).decode()


def json_loads(value: bytes | str | bytearray | memoryview) -> TJSONParsed:
    return orjson.loads(value)
