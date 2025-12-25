from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any, TypeVar, overload

if TYPE_CHECKING:
    from decimal import Decimal

TType = TypeVar("TType")


def sanitize_value(value: str, max_len: int = 6, max_frac: float = 0.2, sep: str = "...") -> str:
    """

    >>> sanitize_value("")
    '...'
    >>> sanitize_value("1234")
    '...'
    >>> sanitize_value("12345")
    '...'
    >>> sanitize_value("123456789")
    '...'
    >>> sanitize_value("123456789a")
    '1...a'
    >>> sanitize_value("123456789abcdef")
    '12...f'
    >>> sanitize_value("123456789abcdef123456789abcdef")
    '123...def'
    >>> sanitize_value("123456789abcdef123456789abcdef123456789abcdef")
    '123...def'
    >>> sanitize_value("123456789abcdef123456789abcdef123456789abcdef", max_len=7)
    '1234...def'
    """
    if not value:
        return sep

    assert max_frac <= 1
    res_len = min(max_len, int(len(value) * max_frac))
    rlen = res_len // 2
    llen = res_len - rlen
    assert llen + rlen < len(value)
    return "".join((value[:llen], sep, value[-rlen:] if rlen else ""))


def sanitize_params(params: dict[str, Any], key_re: str = r"(?i)(api.?key|token)") -> dict[str, Any]:
    return {key: sanitize_value(str(val)) if re.search(key_re, key) else val for key, val in params.items()}


@overload
def round_nsd(value: Decimal, digits: int = 4, min_frac_digits: int = 2) -> Decimal: ...


@overload
def round_nsd(value: float, digits: int = 4, min_frac_digits: int = 2) -> float: ...


def round_nsd(value: Decimal | float, digits: int = 4, min_frac_digits: int = 2) -> Decimal | float:
    """
    Round to n-th significant digit. Primarily for logs.

    >>> from decimal import Decimal
    >>> round_nsd(Decimal("286988.3470174725426810713441"), 4, 2)
    Decimal('286988.35')
    >>> round_nsd(286988.3470174725426810713441, 4, 2)
    286988.35
    >>> round_nsd(Decimal("28.68883470174725426810713441"), 4, 2)
    Decimal('28.69')
    >>> round_nsd(Decimal("-28.68883470174725426810713441"), 4, 2)
    Decimal('-28.69')
    >>> round_nsd(Decimal("2.868883470174725426810713441"), 4, 2)
    Decimal('2.869')
    >>> round_nsd(Decimal("28.868883470174725426810713441"), 4, 0)
    Decimal('28.87')
    >>> round_nsd(Decimal("0.868883470174725426810713441"), 4, 2)
    Decimal('0.8689')
    >>> round_nsd(Decimal("0.03484328485037005752596079115"), 4, 2)
    Decimal('0.03484')
    >>> round_nsd(Decimal("0.00003484328485037005752596079"), 4, 2)
    Decimal('0.00003484')
    >>> 0.00003484328485037005752596079
    3.4843284850370056e-05
    >>> round_nsd(0.00003484328485037005752596079, 4, 2)
    3.484e-05
    >>> round_nsd(Decimal(0), 4, 2)
    Decimal('0')
    >>> round_nsd(0, 4, 2)
    0
    >>> round_nsd(float("NaN"), 4, 2)
    nan
    """
    if value == 0:
        return value
    if not math.isfinite(value):
        return value
    order = math.log10(abs(value))  # type: ignore[arg-type]  # mypy couldn't
    if not math.isfinite(order):
        return value

    round_digits = digits - math.floor(order) - 1
    round_digits = max(min_frac_digits, round_digits)
    return round(value, round_digits)  # type: ignore[return-value]  # mypy couldn't


def ensure_type(typ: type[TType], val: Any) -> TType:
    """`cast(typ, val)` with runtime `isinstance` validation"""
    if not isinstance(val, typ):
        raise ValueError("Unexpected value type", dict(typ=typ, val=val))
    return val


def ensure_type_or_none(typ: type[TType], val: Any) -> TType | None:
    """`cast(typ | None, val)` with runtime `isinstance` validation"""
    if val is None:
        return None
    return ensure_type(typ, val)
