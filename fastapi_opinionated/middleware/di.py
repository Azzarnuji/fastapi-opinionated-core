# fastapi_opinionated/middleware/di.py

from fastapi import Request
from fastapi.dependencies.utils import get_dependant, solve_dependencies
from contextlib import AsyncExitStack
import inspect


async def resolve_middleware_dependencies(callable_obj, request: Request):
    """
    Resolve Depends() untuk middleware (function atau class-based)
    FULLY COMPATIBLE dengan semua versi FastAPI.
    """

    # =========================================================
    # ✅ DETEKSI JENIS MIDDLEWARE DENGAN BENAR
    # =========================================================

    # ✅ CLASS-BASED MIDDLEWARE
    if inspect.isclass(callable_obj):
        target = callable_obj.__call__
        instance = callable_obj()

    # ✅ FUNCTION-BASED MIDDLEWARE
    elif inspect.isfunction(callable_obj):
        target = callable_obj
        instance = None

    else:
        raise RuntimeError(
            f"Middleware tidak valid: {callable_obj} "
            f"(harus function atau class)"
        )

    # =========================================================
    # ✅ BUILD DEPENDANT
    # =========================================================
    dependant = get_dependant(
        path="",
        call=target,
        use_cache=False,   # ✅ WAJIB supaya Depends dieksekusi ulang
    )

    # =========================================================
    # ✅ BUILD ARGUMENTS DINAMIS UNTUK solve_dependencies
    # =========================================================
    sig = inspect.signature(solve_dependencies)
    kwargs = {}

    if "request" in sig.parameters:
        kwargs["request"] = request

    if "dependant" in sig.parameters:
        kwargs["dependant"] = dependant

    if "body" in sig.parameters:
        kwargs["body"] = None

    if "dependency_overrides_provider" in sig.parameters:
        kwargs["dependency_overrides_provider"] = None

    async with AsyncExitStack() as async_exit_stack:

        if "async_exit_stack" in sig.parameters:
            kwargs["async_exit_stack"] = async_exit_stack

        if "embed_body_fields" in sig.parameters:
            kwargs["embed_body_fields"] = False

        solved = await solve_dependencies(**kwargs)

    # =========================================================
    # ✅ NORMALISASI RETURN VALUE
    # =========================================================
    if isinstance(solved, tuple):
        values = solved[0]
    else:
        values = solved.values

    return values, target, instance
