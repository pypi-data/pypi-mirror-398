from __future__ import annotations

import contextlib
from typing import Any, Self


class ACMManaged:
    """
    Helper to handle lifetime of multiple dependencies through a single AsyncExitStack.

    It's like subclassing an AsyncExitStack but cleaner.
    """

    _cm_stack: contextlib.AsyncExitStack | None = None

    async def _enter_contexts(self, cm_stack: contextlib.AsyncExitStack) -> None:
        """Subclass-override point"""

    async def __aenter__(self) -> Self:
        if self._cm_stack is not None:
            raise Exception("Already started")
        cm_stack = contextlib.AsyncExitStack()
        await cm_stack.__aenter__()
        self._cm_stack = cm_stack
        try:
            await self._enter_contexts(cm_stack)
        except BaseException as exc:  # `BaseException` because e.g. timeouts do not absolve of resource-closing.
            # Make sure to unroll whatever was initialized.
            await self.__aexit__(type(exc), exc, exc.__traceback__)
            raise
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> Any:
        cm_stack = self._cm_stack
        if cm_stack is None:
            return None  # already stopped. Re-runnable without error for convenience.
        self._cm_stack = None
        return await cm_stack.__aexit__(exc_type, exc_value, exc_tb)
