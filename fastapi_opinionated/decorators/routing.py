# fastapi_opinionated/decorators/routing.py
import inspect


def Controller(base_path: str, group: str | None = None):
    """
    Class decorator that registers a controller and collects all HTTP route
    metadata defined via the ``@Http`` family of decorators.

    This decorator inspects all methods of the class and collects those
    decorated with HTTP metadata (``_http_method``, ``_http_path``,
    ``_http_group``). It then registers a controller instance with the
    ``RouterRegistry``.

    Parameters
    ----------
    base_path : str
        Base URL path for all class methods. Example: ``"/users"``.

    group : str or None, optional
        Default group name (tag) for FastAPI documentation.
        If omitted, a group will be generated from the base path.

    Behavior
    --------
    - Inspects the class for methods decorated with ``@Http``.
    - Retrieves metadata:
        - ``_http_method`` (GET/POST/...)
        - ``_http_path`` ("/list")
        - ``_http_group`` (optional)
    - Assigns route grouping:
        - Explicit override from ``@Http`` decorator
        - Else use controller-level ``group``
        - Else generate group name from base path

    - Registers the controller with:
        - its instance
        - base path
        - list of methods
        - file path
        - controller name

    Notes
    -----
    - Controller classes must not rely on non-idempotent side effects in
      ``__init__``; instances may be created during routing bootstrap.
    - Class methods are only *marked* here; real FastAPI route binding
      happens inside ``RouterRegistry.as_fastapi_router()``.

    Returns
    -------
    callable
        The original class, unmodified.
    """
    def wrapper(cls):
        routes = []

        # Collect all methods decorated with @Http
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if hasattr(attr, "_http_method"):
                routes.append({
                    "func_name": attr_name,
                    "path": attr._http_path,
                    "http_method": attr._http_method,
                    "group": (
                        attr._http_group
                        if attr._http_group
                        else (group if group else base_path.replace("/", "").upper())
                    ),
                })

        file_path = inspect.getfile(cls)

        from fastapi_opinionated.routing.registry import RouterRegistry

        RouterRegistry.register_controller({
            "instance": cls(),
            "base": base_path,
            "methods": routes,
            "file_path": file_path,
            "controller_name": cls.__name__,
        })

        return cls

    return wrapper



def Http(method: str, path: str, group: str | None = None):
    """
    Universal decorator for marking functions or class methods as HTTP routes.

    This decorator serves two purposes:

    1. **Class-based route definition (used with @Controller):**
       - Stores metadata on the function (method, path, group)
       - Controller will collect them via reflection

    2. **Functional-based route registration:**
       If the decorated function is *not* a class method
       (i.e., ``func.__qualname__`` has no dot), the route is immediately
       registered as a standalone functional route in ``RouterRegistry``.

    Parameters
    ----------
    method : str
        HTTP method, e.g. ``"GET"``, ``"POST"``, etc.

    path : str
        URL path, e.g. ``"/ping"`` or ``"/users/list"``.

    group : str or None, optional
        Group/tag for FastAPI docs. If not provided, defaults to a name
        generated from the path.

    Stored Metadata
    ---------------
    The following attributes are injected into the function:

    - ``_http_method`` : str
    - ``_http_path`` : str
    - ``_http_group`` : str or None

    Automatic Functional Route Behavior
    -----------------------------------
    A function is considered *standalone* (not inside a class) if:
        ``"." not in func.__qualname__``

    In this case the decorator:
        - resolves final group name
        - registers the route immediately via ``RouterRegistry``

    Returns
    -------
    callable
        The wrapped function, unmodified except for attached metadata.
    """
    def decorator(func):
        # Mark metadata
        func._http_method = method.upper()
        func._http_path = path
        func._http_group = group

        # If standalone function, register immediately
        if "." not in func.__qualname__:
            from fastapi_opinionated.routing.registry import RouterRegistry

            final_group = (
                group if group
                else path.replace("/", "").upper()
            )

            RouterRegistry.register_function_route(
                handler=func,
                method=method.upper(),
                path=path,
                group=final_group,
                file_path=inspect.getfile(func)
            )

        return func

    return decorator


def Get(path: str, group: str | None = None):
    """
    Shortcut for ``@Http("GET", path, group)``.
    """
    return Http("GET", path, group)


def Post(path: str, group: str | None = None):
    """
    Shortcut for ``@Http("POST", path, group)``.
    """
    return Http("POST", path, group)


def Put(path: str, group: str | None = None):
    """
    Shortcut for ``@Http("PUT", path, group)``.
    """
    return Http("PUT", path, group)


def Patch(path: str, group: str | None = None):
    """
    Shortcut for ``@Http("PATCH", path, group)``.
    """
    return Http("PATCH", path, group)


def Delete(path: str, group: str | None = None):
    """
    Shortcut for ``@Http("DELETE", path, group)``.
    """
    return Http("DELETE", path, group)


def Options(path: str, group: str | None = None):
    """
    Shortcut for ``@Http("OPTIONS", path, group)``.
    """
    return Http("OPTIONS", path, group)


def Head(path: str, group: str | None = None):
    """
    Shortcut for ``@Http("HEAD", path, group)``.
    """
    return Http("HEAD", path, group)
