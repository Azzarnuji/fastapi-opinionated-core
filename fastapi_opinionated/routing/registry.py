import importlib
import inspect
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi_opinionated.exceptions.plugin_exception import PluginException, PluginRuntimeException
from fastapi_opinionated.middleware.di import resolve_middleware_dependencies
from fastapi_opinionated.middleware import Next
from fastapi_opinionated.shared.logger import ns_logger
import traceback
from fastapi_opinionated.exceptions.middleware_exception import (
    MiddlewareException)
from fastapi_opinionated.http.abort import AbortException

logger = ns_logger("RouterRegistry")


class RouterRegistry:
    """
    Centralized registry for collecting, loading, and converting controller
    metadata into FastAPI routes.

    This registry supports:
        - Class-based controllers (decorator-defined metadata)
        - Functional-based routes (manually registered)
        - Automatic module discovery with safe import
        - Conversion to a FastAPI ``APIRouter`` instance

    Overview
    --------
    Controllers discovered by the framework push metadata into
    ``register_controller()`` while functional routes are added using
    ``register_function_route()``. These are later transformed into concrete
    FastAPI route definitions inside ``as_fastapi_router()``.

    The registry operates declaratively: controllers store metadata only,
    while binding to FastAPI occurs at the very end.

    Attributes
    ----------
    controllers : list
        Contains metadata dictionaries describing class-based controllers.
        Each metadata item includes:
            - controller_name
            - instance
            - base (base path)
            - methods (list of HTTP method definitions)
            - file_path (source file)

    function_routes : list
        Contains metadata for functional routes:
            - handler (callable)
            - http_method (str)
            - path (str)
            - group (str or None)
            - file_path (str)

    Notes
    -----
    - This registry does *not* execute imports twice; imports rely purely on
      Python's import system caching.
    - No dynamic execution (``exec``) is used, ensuring safety and clarity.
    - Automatic module loading walks through ``app/domains`` unless overridden.
    """

    controllers = []
    function_routes = []

    # ----------------------------------------------------------------------
    # CONTROLLER REGISTRATION
    # ----------------------------------------------------------------------
    @classmethod
    def register_controller(cls, meta):
        """
        Register a class-based controller.

        Parameters
        ----------
        meta : dict
            Controller metadata produced by the framework decorators.
            Expected keys:
                - ``controller_name`` : str
                - ``instance`` : object
                - ``base`` : str
                - ``methods`` : list
                - ``file_path`` : str

        Notes
        -----
        Metadata is stored for later conversion into concrete FastAPI routes.
        """
        # prevent duplicate controllers
        for c in cls.controllers:
            if c["controller_name"] == meta["controller_name"] and c["file_path"] == meta["file_path"]:
                return  # skip duplicate

        cls.controllers.append(meta)

    # ----------------------------------------------------------------------
    # ROUTE EXTRACTION
    # ----------------------------------------------------------------------
    @classmethod
    def get_routes(cls):
        """
        Convert all registered controller metadata into normalized route entries.

        Returns
        -------
        list of dict
            Each dict contains:
                - path : str
                - http_method : str
                - handler : callable
                - controller : str
                - file_path : str
                - group : str or None

        Notes
        -----
        No routing is added to FastAPI here. This method only transforms
        metadata into an internal structure ready for router creation.
        """
        routes = []
        for ctrl in cls.controllers:
            logger.info(f"Processing controller: {ctrl['controller_name']}")

            instance = ctrl["instance"]
            base = ctrl["base"]
            file_path = ctrl.get("file_path")

            for m in ctrl["methods"]:
                routes.append({
                    "path": base + m["path"],
                    "http_method": m["http_method"],
                    "handler": getattr(instance, m["func_name"]),
                    "controller": ctrl["controller_name"],
                    "file_path": file_path,
                    "group": m.get("group"),
                })

        return routes

    # ----------------------------------------------------------------------
    # FUNCTIONAL ROUTES
    # ----------------------------------------------------------------------
    @classmethod
    def register_function_route(cls, handler, method, path, group, file_path):
        """
        Register a functional-based route.

        Parameters
        ----------
        handler : callable
            Function to be executed for the route.

        method : str
            HTTP method (e.g., ``"GET"``, ``"POST"``).

        path : str
            URL path.

        group : str or None
            Tag/group for FastAPI documentation grouping.

        file_path : str
            File where the handler is declared (for introspection/logging).

        Notes
        -----
        Functional routes are stored similarly to class-based routes, but
        without any controller binding.
        """
        cls.function_routes.append({
            "handler": handler,
            "http_method": method,
            "path": path,
            "group": group,
            "file_path": file_path,
            "controller": None,
        })

    # ----------------------------------------------------------------------
    # MODULE LOADING / DISCOVERY
    # ----------------------------------------------------------------------
    @classmethod
    def load(cls, root="app/domains"):
        """
        Recursively import ONLY Python modules inside any `controllers/` folder.
        Supports unlimited nested subdirectories under controllers/.
        """

        root = root.rstrip("/")

        for current_root, dirs, files in os.walk(root):

            # Skip everything that is NOT inside a controllers folder
            # Example valid: .../controllers, .../controllers/x, .../controllers/x/y
            if "controllers" not in current_root.split("/"):
                continue

            # Clean directory list (skip hidden, __pycache__, etc.)
            dirs[:] = [
                d for d in dirs
                if not d.startswith("__")
                and not d.startswith(".")
                and d != "__pycache__"
            ]

            dirs.sort()
            files.sort()

            for file in files:
                if not file.endswith(".py") or file.startswith("__"):
                    continue

                file_path = os.path.join(current_root, file)

                module_path = (
                    file_path
                    .replace("/", ".")
                    .replace("\\", ".")
                    .rsplit(".py", 1)[0]
                )

                try:
                    importlib.import_module(module_path)
                    logger.info(f"Imported controller: {module_path}")
                except Exception as e:
                    logger.error(f"Failed to import {module_path}: {e}")
                    os._exit(1)
                except (PluginException, PluginRuntimeException) as pe:
                    logger.error(f"Plugin error during import of {module_path}: {pe}")
                    os._exit(1)

                
    # ----------------------------------------------------------------------
    # PATH NORMALIZATION
    # ----------------------------------------------------------------------
    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize route path to avoid false non-duplicates like /users vs /users/."""
        if not path.startswith("/"):
            path = "/" + path

        # remove trailing slash except root
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        # collapse multiple slashes
        while "//" in path:
            path = path.replace("//", "/")

        return path

                
    # ----------------------------------------------------------------------
    # DUPLICATE DETECTION
    # ----------------------------------------------------------------------
    @classmethod
    def detect_route_duplicates(cls, routes):
        """
        Detect duplicate (METHOD, PATH) routes across class-based and functional routes.

        Returns
        -------
        dict :
            {
                (method, path): [
                    { handler, file, controller },
                    ...
                ]
            }
        """
        collisions = {}

        # CLASS-BASED
        for r in routes:
            key = (r["http_method"].upper(), cls.normalize_path(r["path"]))
            entry = {
                "handler": r["handler"].__name__,
                "file": r["file_path"],
                "controller": r["controller"],
            }
            collisions.setdefault(key, []).append(entry)

        # FUNCTIONAL-BASED
        for fr in cls.function_routes:
            key = (fr["http_method"].upper(), fr["path"])
            entry = {
                "handler": fr["handler"].__name__,
                "file": fr["file_path"],
                "controller": None,
            }
            collisions.setdefault(key, []).append(entry)

        # Return only duplicates
        return {key: vals for key, vals in collisions.items() if len(vals) > 1}
            
    

        # ----------------------------------------------------------------------
    # FASTAPI ROUTER OUTPUT (WITH DUPLICATE VALIDATION)
    # ----------------------------------------------------------------------
    @classmethod
    def as_fastapi_router(cls):
        """
        Convert registered routes into a FastAPI router,
        and throw error if duplicate (METHOD, PATH) exists.
        """

        # ================================
        # DUPLICATE VALIDATION
        # ================================
        routes = cls.get_routes()
        duplicates = cls.detect_route_duplicates(routes)
        if duplicates:
            msg_lines = ["Duplicate route definitions detected:\n"]

            for (method, path), entries in duplicates.items():
                msg_lines.append(f"  [{method}] {path}")
                for e in entries:
                    controller_info = f" (controller={e['controller']})" if e["controller"] else ""
                    msg_lines.append(
                        f"    - handler: {e['handler']}{controller_info}\n"
                        f"      file: {e['file']}"
                    )
                msg_lines.append("")  # spacing

            raise RuntimeError("\n".join(msg_lines))

        # ================================
        # NO DUPLICATE → PROCEED
        # ================================
        router = APIRouter()

        # CLASS-BASED ROUTES
        for route in routes:
            handler = route["handler"]
            fastapi_handler = cls._wrap_with_middleware(handler) if getattr(handler, "__attached_middlewares__", False) else handler
            router.add_api_route(
                route["path"],
                fastapi_handler,
                methods=[route["http_method"]],
                tags=[route["group"]],
            )

            logger.info(
                f"Registered route: [{route['http_method']}] {route['path']} -> "
                f"{route['controller']}.{route['handler'].__name__}"
            )

        # FUNCTIONAL ROUTES
        for fr in cls.function_routes:
            handler = fr["handler"]
            fastapi_handler = cls._wrap_with_middleware(handler)
            router.add_api_route(
                fr["path"],
                fastapi_handler,
                methods=[fr["http_method"]],
                tags=[fr["group"]],
            )

            logger.info(
                f"Registered route: [{fr['http_method']}] "
                f"{fr['path']} -> {fr['handler'].__name__}"
            )

        return router
    
    
    @classmethod
    def _wrap_with_middleware(cls, handler, instance=None):
        try:
            import inspect
            from fastapi import Request
            from fastapi.responses import JSONResponse
            import traceback

            from fastapi_opinionated.http.abort import AbortException
            from fastapi_opinionated.exceptions.middleware_exception import MiddlewareException

            sig = inspect.signature(handler)  # ✅ ambil signature ASLI handler

            async def wrapped(**kwargs):
                try:
                    request: Request = kwargs.get("request")

                    # ✅ FRAMEWORK-LEVEL VALIDATION
                    if request is None:
                        raise MiddlewareException(
                            handler_name=handler.__name__,
                            middleware_name=None,
                            msg="Route with middleware must have a 'request: Request' parameter",
                        )

                    # ============================
                    # 1. AMBIL MIDDLEWARE CLASS
                    # ============================
                    class_middlewares = []
                    if instance:
                        class_middlewares = getattr(
                            instance.__class__,
                            "__class_middlewares__",
                            []
                        )

                    # ============================
                    # 2. AMBIL MIDDLEWARE METHOD
                    # ============================
                    method_middlewares = getattr(
                        handler,
                        "__method_middlewares__",
                        []
                    )

                    all_middlewares = [
                        *class_middlewares,
                        *method_middlewares,
                    ]

                    async def call_handler():
                        bound = sig.bind_partial(**kwargs)
                        return await handler(*bound.args, **bound.kwargs)

                    async def run(index: int):
                        try:
                            if index >= len(all_middlewares):
                                return await call_handler()

                            mw = all_middlewares[index]

                            if not getattr(mw, "__is_opinionated_middleware__", False):
                                raise MiddlewareException(
                                    handler.__name__,
                                    getattr(mw, "__name__", str(mw)),
                                    "Middleware must be decorated with @Middleware",
                                )

                            values, target, mw_instance = await resolve_middleware_dependencies(
                                mw, request
                            )

                            Next.set(Next(lambda: run(index + 1)))

                            if mw_instance is not None:
                                result = await target(mw_instance, **values)
                            else:
                                result = await target(**values)

                            if result is not None:
                                return result

                            return await run(index + 1)

                        except AbortException as e:
                            logger.warning(
                                f"Request aborted by middleware {mw.__name__}: "
                                f"{e.status_code} {e.message}"
                            )
                            return JSONResponse(
                                status_code=e.status_code,
                                content={"detail": e.message},
                            )

                    return await run(0)

                except MiddlewareException as e:
                    logger.error(f"[MiddlewareException] {e.payload}")

                    return JSONResponse(
                        status_code=e.status_code,
                        content={"detail": e.payload},
                    )

                except AbortException:
                    raise  # biar FastAPI yang handle kalau keluar dari handler

                except Exception as e:
                    traceback.print_exc()
                    logger.error(f"Fatal error in handler {handler.__name__}: {e}")
                    raise

            wrapped.__signature__ = sig
            wrapped.__name__ = handler.__name__
            wrapped.__doc__ = handler.__doc__

            return wrapped

        except Exception as e:
            logger.error(f"Gagal membungkus handler {handler}: {e}")
            raise


    @classmethod
    def get_all_routes(cls):
        """
        Get all registered routes (class-based + functional) as a combined list.

        Returns
        -------
        list of dict
            Each dict contains:
                - path : str
                - http_method : str
                - handler : callable
                - controller : str or None
                - file_path : str
                - group : str or None

        Notes
        -----
        This method combines routes from both class-based controllers and
        functional registrations into a single list for inspection.
        """
        routes = cls.get_routes()
        routes.extend(cls.function_routes)
        return routes