# fastapi_opinionated/routing/registry.py
class RouterRegistry:
    controllers = []
    @classmethod
    def register_controller(cls, controller_meta):
        cls.controllers.append(controller_meta)

    @classmethod
    def get_routes(cls):
        routes = []
        for ctrl in cls.controllers:
            instance = ctrl["instance"]
            base = ctrl["base"]
            methods = ctrl["methods"]

            for m in methods:
                routes.append({
                    "path": base + m["path"],
                    "http_method": m["http_method"],
                    "handler": getattr(instance, m["func_name"])
                })

        return routes