# fastapi_opinionated/app.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_opinionated.registry.plugin import PluginRegistry
from fastapi_opinionated.routing.registry import RouterRegistry
from fastapi_opinionated.shared.base_plugin import BasePlugin
from fastapi_opinionated.shared.logger import ns_logger
from fastapi_opinionated.exceptions.plugin_exception import PluginException

logger = ns_logger("FastAPIOpinionated")


class App(PluginRegistry):
    _cmd_handlers = {}
    plugin = type("Plugins", (), {})()
    fastapi = None
    
    # ===========================================================
    # FASTAPI FACTORY
    # ===========================================================
    @classmethod
    def create(cls, **fastapi_kwargs):
        try:
            user_lifespan = fastapi_kwargs.get("lifespan", None)

            # STEP 1 — create FastAPI FIRST
            app = FastAPI(**fastapi_kwargs)
            cls.fastapi = app
            
            

            # STEP 2 — now safe to enable plugins
            cls._load_enabled_plugins()
            
            # -----------------------------
            # load controllers
            # -----------------------------
            RouterRegistry.load()

            # =======================================================
            # COMBINED LIFESPAN
            # =======================================================
            @asynccontextmanager
            async def combined_lifespan(app):
                plugins = cls._plugin_instances

                # -----------------------------
                # on_plugins_loaded
                # -----------------------------
                for name, plugin in plugins.items():
                    if hasattr(plugin, "on_plugins_loaded"):
                        plugin.on_plugins_loaded(cls, app)

                # -----------------------------
                # on_controllers_loaded
                # -----------------------------
                for name, plugin in plugins.items():
                    if hasattr(plugin, "on_controllers_loaded"):
                        plugin.on_controllers_loaded(cls, app)

                # -----------------------------
                # on_ready + on_ready_async
                # -----------------------------
                for name, plugin in plugins.items():
                    plugin_api = getattr(cls.plugin, name, None)

                    if hasattr(plugin, "on_ready"):
                        plugin.on_ready(cls, app, plugin_api)

                    if hasattr(plugin, "on_ready_async"):
                        await plugin.on_ready_async(cls, app, plugin_api)

                # -----------------------------
                # on_app_ready
                # -----------------------------
                for name, plugin in plugins.items():
                    if hasattr(plugin, "on_app_ready"):
                        plugin.on_app_ready(cls, app)

                logger.info("FastAPI application completed initialization.")

                # user lifespan
                if user_lifespan:
                    async with user_lifespan(app):
                        yield
                else:
                    yield

                # -----------------------------
                # shutdown
                # -----------------------------
                for name, plugin in plugins.items():
                    plugin_api = getattr(cls.plugin, name, None)

                    if hasattr(plugin, "on_before_shutdown"):
                        plugin.on_before_shutdown(cls, app, plugin_api)

                    if hasattr(plugin, "on_before_shutdown_async"):
                        await plugin.on_before_shutdown_async(cls, app, plugin_api)

                for name, plugin in plugins.items():
                    plugin_api = getattr(cls.plugin, name, None)

                    if "on_shutdown_async" in plugin.__class__.__dict__:
                        logger.info(f"Shutting down plugin '{name}'")
                        await plugin.on_shutdown_async(cls, app, plugin_api)

                    if "on_shutdown" in plugin.__class__.__dict__:
                        logger.info(f"Shutting down plugin '{name}'")
                        plugin.on_shutdown(cls, app, plugin_api)

            # Attach lifespan to app
            app.router.lifespan_context = combined_lifespan

            # PluginException handler
            @app.exception_handler(PluginException)
            async def plugin_exception_handler(request, exc: PluginException):
                logger.error(f"PluginException occurred: {exc}")
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"Plugin error: {exc}"},
                )

            # Bind routes
            router = RouterRegistry.as_fastapi_router()
            app.include_router(router)

            return app
        except RuntimeError as e:
            raise e

    # ===========================================================
    # COMMAND REGISTRY
    # ===========================================================
    @classmethod
    def register_cmd(cls, name, handler):
        cls._cmd_handlers[name] = handler

    @classmethod
    def _cmd(cls, name, **kwargs):
        if name not in cls._cmd_handlers:
            raise RuntimeError(f"Command '{name}' not found.")

        if cls.fastapi is None:
            raise RuntimeError("FastAPI must be initialized before running commands.")

        result = cls._cmd_handlers[name](cls, cls.fastapi, **kwargs)

        if result is None:
            raise RuntimeError(
                f"Command '{name}' returned None. Internal() must return plugin API."
            )
        return result


# ===========================================================
# DECORATOR
# ===========================================================
def AppCmd(name: str):
    def decorator(func):
        App.register_cmd(name, func)
        return func
    return decorator
