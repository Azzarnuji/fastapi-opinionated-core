# fastapi_opinionated/http/state.py
from typing import TypeVar, Dict, Type
from fastapi import Request

T = TypeVar("T", bound="State")


class StateMeta(type):
    def __call__(cls: Type[T], request: Request, **kwargs) -> T:
        store = request.scope.setdefault("_opinionated_state", {})

        # ✅ GET MODE
        if not kwargs:
            if cls not in store:
                raise RuntimeError(
                    f"State {cls.__name__} belum di-set di request ini."
                )
            return store[cls]

        # ✅ SET MODE
        obj = super().__call__(**kwargs)  # ini memanggil __init__ dataclass
        store[cls] = obj
        return obj


class State(metaclass=StateMeta):
    pass
