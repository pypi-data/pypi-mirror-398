from __future__ import annotations

import contextlib
import uuid
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

# See also: https://github.com/snok/asgi-correlation-id
TRACE_ID_VAR: ContextVar[str | None] = ContextVar("trace_id", default=None)
LOG_EXTRAS_VAR: ContextVar[dict[str, Any] | None] = ContextVar("log_extras", default=None)


def make_new_trace_id(
    subprefix: str, prefix: str = "", total_len: int = 16, parent: str | None = None, parent_sep: str = "__"
) -> str:
    uuid_len = total_len - len(prefix) - len(subprefix)
    uuid_val = uuid.uuid4().hex[:uuid_len]  # This could be simple `getrandbits` though.
    result = f"{prefix}{subprefix}{uuid_val}"
    if parent:
        result = f"{parent}{parent_sep}{result}"
    return result


new_trace_id = make_new_trace_id  # compat alias (deprecated)


def use_new_trace_id(prefix: str) -> None:
    trace_id = make_new_trace_id(prefix)
    TRACE_ID_VAR.set(trace_id)


def update_log_ctx(updates: dict[str, Any]) -> None:
    """
    Set extra values for the logging
    for the current aio task and the new subtasks
    (`ContextVar` logic).
    """
    prev_ctx = LOG_EXTRAS_VAR.get() or {}
    new_ctx = {key: val for obj in (prev_ctx, updates) for key, val in obj.items() if val is not None}
    LOG_EXTRAS_VAR.set(new_ctx)


@contextlib.contextmanager
def with_log_ctx(updates: dict[str, Any]) -> Generator[None, None, None]:
    prev_ctx = LOG_EXTRAS_VAR.get() or {}
    prev_values = {key: prev_ctx.get(key) for key in updates}
    try:
        update_log_ctx(updates)
        yield None
    finally:
        update_log_ctx(prev_values)
