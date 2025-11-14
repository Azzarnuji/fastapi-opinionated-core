# fastapi_opinionated/app.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_opinionated.routing.registry import RouterRegistry
from fastapi_opinionated.shared.base_plugin import BasePlugin
from fastapi_opinionated.shared.logger import ns_logger
from fastapi_opinionated.exceptions.plugin_exception import PluginException

logger = ns_logger("FastAPIOpinionated")
class App:
    """
    Core application container and factory for the opinionated FastAPI framework.

    This class functions as a lightweight application "core" object that:
    - Creates and configures a FastAPI application (factory).
    - Maintains a small plugin/command registry for extending application behavior.
    - Stores the created FastAPI instance for later use by registered commands and plugins.

    Attributes
    _cmd_handlers : dict
        Mapping of command names to callables. Command handlers are expected to have
        the signature (core_cls, fastapi_app, **kwargs) and may return arbitrary values.
    plugin : object
        A dynamic container object used to attach enabled plugin APIs as attributes.
        Plugins are typically accessed as App.plugin.<public_name>.
    fastapi : fastapi.FastAPI | None
        Holds the FastAPI application instance created by App.create(). Initially None
        and set to the FastAPI instance when create() completes successfully.

    Methods
    create(**fastapi_kwargs)
        Build, configure, and return a FastAPI application. Performs logging setup,
        loads routes from the RouterRegistry, includes the assembled router into the
        FastAPI app, assigns the created app to App.fastapi, and returns the app.
        Parameters are forwarded to fastapi.FastAPI. Exceptions raised during
        initialization (e.g. RouterRegistry errors, FastAPI errors) propagate to the caller.

    register_cmd(name, handler)
        Register a command handler under the provided name. The handler will later be
        invoked by App.cmd and is supplied with the App class and the FastAPI instance.

    cmd(name, **kwargs)
        Execute a previously registered command handler. Validates that the named
        command exists and that App.fastapi has been initialized; otherwise raises
        RuntimeError. Calls the handler as handler(App, App.fastapi, **kwargs) and
        returns the handler's result.

    enable(plugin: BasePlugin, **plugin_kwargs)
        Enable a plugin instance derived from BasePlugin. Validates the plugin type,
        calls plugin.enable(...) for IDE/method-signature purposes, then executes the
        plugin's registered command via App.cmd(plugin.command_name, **plugin_kwargs)
        to obtain a plugin-specific API object. The returned API is attached to
        App.plugin under plugin.public_name and also returned to the caller.
        Raises RuntimeError if the plugin is not an instance of BasePlugin or if the
        required FastAPI instance has not been initialized.

    Behavioral notes
    ----------------
    - create() must be called before enable() to ensure a FastAPI instance exists.
    - Plugins are expected to advertise two attributes used by enable():
      - command_name: the command name to invoke via App.cmd
      - public_name: the attribute name to use when attaching the plugin API to App.plugin
    - Command handlers receive the App class and the FastAPI instance so they can
      register routes, middleware, or perform other app-scoped operations.
    """
    _cmd_handlers = {}
    plugin = type("Plugins", (), {})()
    fastapi = None   # <--- FASTAPI INSTANCE DISIMPAN DI SINI


    # ============================
    # FASTAPI FACTORY
    # ============================
    @classmethod
    def create(cls, **fastapi_kwargs):
        """
        Create and configure a FastAPI application.

        This classmethod performs the following steps:
        - Initializes logging via setup_logging() and logs startup messages.
        - Constructs a FastAPI application with the provided keyword arguments.
        - Loads routes from RouterRegistry and includes the resulting router into the app.
        - Stores the constructed FastAPI application on the class as `fastapi`.
        - Returns the configured FastAPI application instance.

        Parameters
        ----------
        **fastapi_kwargs : dict
            Keyword arguments forwarded to fastapi.FastAPI.

        Returns
        -------
        fastapi.FastAPI
            The configured FastAPI application instance.

        Side effects
        ------------
        - Calls setup_logging() and emits log messages.
        - Mutates and uses RouterRegistry (RouterRegistry.load()).
        - Assigns the created app to `cls.fastapi`.

        Raises
        ------
        Any exception raised by FastAPI initialization, RouterRegistry.load(), or app.include_router()
        will propagate to the caller.
        """

        app = FastAPI(**fastapi_kwargs)
        @app.exception_handler(PluginException)
        async def plugin_exception_handler(request, exc: PluginException):
            logger.error(f"PluginException occurred: {exc}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Plugin error: {exc}"},
            )
            
        RouterRegistry.load()

        router = RouterRegistry.as_fastapi_router()
        app.include_router(router)

        logger.info("Application started successfully")

        cls.fastapi = app  # <--- Save fastapi instance here

        return app


    # ============================
    # PLUGIN SYSTEM
    # ============================
    @classmethod
    def register_cmd(cls, name, handler):
        cls._cmd_handlers[name] = handler

    @classmethod
    def _cmd(cls, name, **kwargs):
        if name not in cls._cmd_handlers:
            raise RuntimeError(f"Command '{name}' not found.")
        if cls.fastapi == None:
            raise RuntimeError("FastAPI Must be initialized before using commands.")
        # PASS FastAPI instance otomatis
        return cls._cmd_handlers[name](cls, cls.fastapi, **kwargs)

    @classmethod
    def enable(cls, plugin: BasePlugin, **plugin_kwargs):
        """
        Enable a plugin on the application.

        This class-level helper validates and activates a plugin, delegates
        initialization to the plugin itself, constructs the plugin's public API via
        the class's internal factory, and binds that API onto the class plugin
        namespace.

        Parameters
        ----------
        plugin : BasePlugin
            The plugin instance to enable. Must be an instance (or subclass) of
            BasePlugin.
        **plugin_kwargs
            Arbitrary keyword arguments forwarded to both plugin.enable(...) and
            cls._cmd(...). These are used for plugin initialization and API creation.

        Raises
        ------
        RuntimeError
            If the provided `plugin` is not an instance of BasePlugin.

        Returns
        -------
        Any
            The plugin API object produced by cls._cmd(plugin.command_name, **plugin_kwargs).
            As a side effect, this object is attached to the class-level `plugin`
            namespace under the attribute name given by plugin.public_name.

        """
        if not isinstance(plugin, BasePlugin):
            raise RuntimeError("Plugin must be a subclass of BasePlugin")

        plugin_api = cls._cmd(plugin.command_name, **plugin_kwargs)

        setattr(cls.plugin, plugin.public_name, plugin_api)

        return plugin_api


def AppCmd(name: str):
    def decorator(func):
        App.register_cmd(name, func)
        return func
    return decorator
