import inspect


# ===========================================================
# PATH NORMALIZER
# ===========================================================
def _normalize_path(path: str | None) -> str:
    """
    Normalizes any incoming path into a valid URL path.
    - None -> "/"
    - "" or "   " -> "/"
    - "list" -> "/list"
    - "/list" -> "/list"
    - "/" stays "/"
    """
    if path is None or str(path).strip() == "":
        return "/"

    path = str(path).strip()

    if not path.startswith("/"):
        return f"/{path}"

    return path


# ===========================================================
# UNIVERSAL HTTP DECORATOR
# ===========================================================
def Http(method: str, path: str | None, group: str | None = None):
    """
    Low-level decorator used by @Get, @Post, etc.

    - Works for class-based controllers (metadata only)
    - Works for functional routes (registered immediately)
    """
    def decorator(func):
        normalized = _normalize_path(path)

        # Attach metadata
        func._http_method = method.upper()
        func._http_path = normalized
        func._http_group = group

        # Functional-based: register immediately
        if "." not in func.__qualname__:  # not part of a class
            from fastapi_opinionated.routing.registry import RouterRegistry

            final_group = group if group else normalized.replace("/", "").upper()

            RouterRegistry.register_function_route(
                handler=func,
                method=method.upper(),
                path=normalized,
                group=final_group,
                file_path=inspect.getfile(func)
            )

        return func

    return decorator


# ===========================================================
# CLASS-BASED CONTROLLER DECORATOR
# ===========================================================
def Controller(base_path: str, group: str | None = None):
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

        from fastapi_opinionated.routing.registry import RouterRegistry

        RouterRegistry.register_controller({
            "instance": cls(),
            "base": base_path,
            "methods": routes,
            "file_path": inspect.getfile(cls),
            "controller_name": cls.__name__,
        })

        return cls

    return wrapper


# ===========================================================
# FLEXIBLE DECORATOR FACTORY
# ===========================================================
def _auto(method: str, path=None, group=None):
    """
    Supports:
    @Get
    @Get()
    @Get("/x")
    """

    # Case: @Get (decorator called directly on function)
    if callable(path):
        func = path
        return Http(method, None, group)(func)

    # Case: @Get() or @Get("/x")
    return Http(method, path, group)


# ===========================================================
# SHORTCUT DECORATORS
# ===========================================================
def Get(path=None, group=None):
    return _auto("GET", path, group)

def Post(path=None, group=None):
    return _auto("POST", path, group)

def Put(path=None, group=None):
    return _auto("PUT", path, group)

def Patch(path=None, group=None):
    return _auto("PATCH", path, group)

def Delete(path=None, group=None):
    return _auto("DELETE", path, group)

def Options(path=None, group=None):
    return _auto("OPTIONS", path, group)

def Head(path=None, group=None):
    return _auto("HEAD", path, group)
