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
                    "group": group if group else base_path.replace("/", "").upper(),
                })

        # ambil lokasi file controller.py
        file_path = inspect.getfile(cls)

        from fastapi_opinionated.routing.registry import RouterRegistry

        RouterRegistry.register_controller({
            "instance": cls(),
            "base": base_path,
            "methods": routes,
            "file_path": file_path,        # <--- tambahkan ini
            "controller_name": cls.__name__
        })

        return cls
    return wrapper


def Http(method: str, path: str):
    def decorator(func):
        func._http_method = method
        func._http_path = path
        return func
    return decorator

# ----------------------------------------------------------------
# HTTP METHOD DECORATORS (FULL LIST)
# ----------------------------------------------------------------

def Get(path: str):
    return Http("GET", path)

def Post(path: str):
    return Http("POST", path)

def Put(path: str):
    return Http("PUT", path)

def Patch(path: str):
    return Http("PATCH", path)

def Delete(path: str):
    return Http("DELETE", path)

def Options(path: str):
    return Http("OPTIONS", path)

def Head(path: str):
    return Http("HEAD", path)

def Trace(path: str):
    return Http("TRACE", path)

def Connect(path: str):
    return Http("CONNECT", path)
