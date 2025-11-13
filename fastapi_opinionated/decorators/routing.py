# fastapi_opinionated/decorators/routing.py
import inspect


def Controller(base_path: str, group: str | None = None):
    def wrapper(cls):
        routes = []

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if hasattr(attr, "_http_method"):
                routes.append({
                    "func_name": attr_name,
                    "path": attr._http_path,
                    "http_method": attr._http_method,
                    "group": attr._http_group 
                        if attr._http_group 
                        else (group if group else base_path.replace("/", "").upper()),
                })

        file_path = inspect.getfile(cls)

        from fastapi_opinionated.routing.registry import RouterRegistry

        RouterRegistry.register_controller({
            "instance": cls(),
            "base": base_path,
            "methods": routes,
            "file_path": file_path,
            "controller_name": cls.__name__
        })

        return cls
    return wrapper



def Http(method: str, path: str, group: str | None = None):
    """
    Universal decorator:
    - Marks class methods with HTTP metadata (collected later by @Controller)
    - Immediately registers standalone functions as routes
    """
    def decorator(func):
        func._http_method = method.upper()
        func._http_path = path
        func._http_group = group

        # If not inside class -> register as function-based route
        # Functional route has __qualname__ like "ping"
        if "." not in func.__qualname__:
            from fastapi_opinionated.routing.registry import RouterRegistry

            # Auto-generate group if not given
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
    return Http("GET", path, group)

def Post(path: str, group: str | None = None):
    return Http("POST", path, group)

def Put(path: str, group: str | None = None):
    return Http("PUT", path, group)

def Patch(path: str, group: str | None = None):
    return Http("PATCH", path, group)

def Delete(path: str, group: str | None = None):
    return Http("DELETE", path, group)

def Options(path: str, group: str | None = None):
    return Http("OPTIONS", path, group)

def Head(path: str, group: str | None = None):
    return Http("HEAD", path, group)
