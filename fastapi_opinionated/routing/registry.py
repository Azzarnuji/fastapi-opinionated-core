import importlib
import os
from fastapi import APIRouter
from fastapi_opinionated.shared.logger import ns_logger

logger = ns_logger("RouterRegistry")
class RouterRegistry:
    controllers = []
    function_routes = []

    @classmethod
    def register_controller(cls, meta):
        cls.controllers.append(meta)

    @classmethod
    def get_routes(cls):
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
                    "group": m["group"] if "group" in m else None,
                })

        return routes
    
    @classmethod
    def register_function_route(cls, handler, method, path, group, file_path):
        cls.function_routes.append({
            "handler": handler,
            "http_method": method,
            "path": path,
            "group": group,
            "file_path": file_path,
            "controller": None,
        })
    
    @classmethod
    def load(cls, root="app/domains"):
        """
        Auto-import semua controller berdasarkan module path yang benar
        Tidak ada exec_module, tidak ada double import.
        """
        for root, dirs, files in os.walk(root):
            for file in files:
                if not file.endswith(".py") or file.startswith("__"):
                    continue

                file_path = os.path.join(root, file)

                module_path = (
                    file_path
                    .replace("/", ".")
                    .replace("\\", ".")
                    .rsplit(".py", 1)[0]
                )

                importlib.import_module(module_path)
                logger.info(f"Imported module: {module_path}")
                
    @classmethod
    def as_fastapi_router(cls):
        router = APIRouter()

        for route in cls.get_routes():
            router.add_api_route(
                route["path"],
                route["handler"],
                methods=[route["http_method"]],
                tags=[route["group"]],
            )
            logger.info(
                f"Registered route: [{route['http_method']}] {route['path']} -> "
                f"{route['controller']}.{route['handler'].__name__} "
            )
        # FUNCTIONAL ROUTES
        for fr in cls.function_routes:
            router.add_api_route(
                fr["path"],
                fr["handler"],
                methods=[fr["http_method"]],
                tags=[fr["group"]],
            )
            logger.info(
                f"Registered function route: [{fr['http_method']}] {fr['path']} -> {fr['handler'].__name__}"
            )
        return router