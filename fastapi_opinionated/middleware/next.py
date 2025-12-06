# fastapi_opinionated/middleware/next.py

from contextvars import ContextVar
from typing import Callable, Awaitable, Any

_next_ctx: ContextVar["Next"] = ContextVar("_next_ctx")

class Next:
    def __init__(self, fn: Callable[[], Awaitable[Any]]):
        self._fn = fn

    async def __call__(self) -> Any:
        return await self._fn()

    @classmethod
    def set(cls, next_obj: "Next"):
        _next_ctx.set(next_obj)

    @classmethod
    def current(cls) -> "Next":
        value = _next_ctx.get(None)
        if value is None:
            raise RuntimeError("Next() tidak tersedia di context middleware")
        return value
    
    @classmethod
    async def run(cls):
        value = cls.current()
        return await value()