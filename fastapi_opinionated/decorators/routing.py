# fastapi_opinionated/decorators/routing.py
def Controller(base_path: str):
    def wrapper(cls):
        # collect methods marked by GET/POST/etc
        routes = []

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if hasattr(attr, "_http_method"):
                routes.append({
                    "func_name": attr_name,
                    "path": attr._http_path,
                    "http_method": attr._http_method
                })

        from fastapi_opinionated.routing.registry import RouterRegistry
        RouterRegistry.register_controller({
            "instance": cls(),  # instantiate controller
            "base": base_path,
            "methods": routes
        })

        return cls
    return wrapper


def Http(method: str, path: str):
    def decorator(func):
        func._http_method = method
        func._http_path = path
        return func
    return decorator


def Get(path: str):
    return Http("GET", path)


def Post(path: str):
    return Http("POST", path)