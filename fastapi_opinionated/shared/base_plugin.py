from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """
    Strict and minimal plugin abstraction used by the framework.

    Every plugin must define:
        - ``public_name`` (str): Human-friendly plugin name
        - ``command_name`` (str): Command identifier used by @AppCmd
        - ``_internal()`` (static method): The command handler, decorated
          with ``@AppCmd(plugin.command_name)`` and returning a plugin API object.

    Plugins may optionally implement lifecycle hooks:
        - ``on_ready``
        - ``on_ready_async``
        - ``on_shutdown``
        - ``on_shutdown_async``

    Lifecycle Integration
    ---------------------
    All lifecycle hooks are executed *inside* FastAPI's lifespan context,
    which is implemented using ``asynccontextmanager``:

    .. code-block:: python

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup phase
            yield
            # Shutdown phase

    This means:
        - ``on_ready`` and ``on_ready_async`` run during the startup phase,
          after all plugins are enabled and before the app starts handling requests.

        - ``on_shutdown`` and ``on_shutdown_async`` run during the shutdown phase,
          after FastAPI stops receiving requests but before the application fully exits.

    Hooks are guaranteed to run in order, are isolated per plugin, and must be
    idempotent to ensure safe reloads, reinitialization, or development hot-reloads.

    Notes
    -----
    - Long-blocking or CPU-heavy work should not run directly in hooks.
      Use background tasks or thread executors instead.

    - ``plugin_api`` returned by ``_internal()`` is passed to every hook,
      allowing stateful or resource-based plugins to keep internal handles.

    - If a hook fails, the framework may interrupt application startup/shutdown
      depending on severity.
    """

    public_name: str = ""
    command_name: str = ""

    # =======================================================
    # INTERNAL INITIALIZER (MANDATORY)
    # =======================================================
    @staticmethod
    @abstractmethod
    def _internal(app, fastapi_app, *args, **kwargs):
        """
        Internal plugin initializer.

        This method must be decorated using ``@AppCmd(plugin.command_name)``
        so the framework can dispatch commands to enable or configure the plugin.

        Parameters
        ----------
        app : Any
            The host application or plugin manager instance.
            Provides access to framework-level configuration or registries.

        fastapi_app : fastapi.FastAPI
            The underlying FastAPI application object.

        *args :
            Additional positional arguments supplied by the framework or user.

        **kwargs :
            Additional keyword arguments supplied by the framework or user.

        Returns
        -------
        Any
            A plugin API object that will be passed to all lifecycle hooks.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by the plugin.
        """
        raise NotImplementedError

    # =======================================================
    # STARTUP HOOKS
    # =======================================================
    def on_ready(self, app, fastapi_app, plugin_api):
        """
        Synchronous startup hook executed after the framework and FastAPI
        application are fully initialized, but before the server begins
        processing HTTP requests.

        Executed *inside* FastAPI's lifespan startup phase.

        Parameters
        ----------
        app : Any
            Main framework application or container object.

        fastapi_app : fastapi.FastAPI
            The FastAPI instance to which routers, middleware, or events
            may be attached.

        plugin_api : Any
            The object returned by ``_internal()``, containing plugin-scoped
            resources or state.

        Notes
        -----
        - Should be idempotent to avoid duplicate side effects.
        - Avoid long-blocking operations; use async tasks when required.
        """
        pass

    async def on_ready_async(self, app, fastapi_app, plugin_api):
        """
        Asynchronous startup hook executed after the framework and FastAPI
        application are initialized, but before request handling begins.

        Executed *inside* FastAPI's lifespan startup phase.

        Parameters
        ----------
        app : Any
            Main framework application or container object.

        fastapi_app : fastapi.FastAPI
            The FastAPI instance.

        plugin_api : Any
            Plugin-scoped API returned by ``_internal()``.

        Notes
        -----
        - Ideal for async I/O, async DB connections, or async initialization.
        - Must not block the event loop for extended periods.
        """
        pass

    # =======================================================
    # SHUTDOWN HOOKS
    # =======================================================
    def on_shutdown(self, app, fastapi_app, plugin_api):
        """
        Synchronous shutdown hook executed when FastAPI begins its shutdown
        sequence, but before the application fully exits.

        Executed *inside* FastAPI's lifespan shutdown phase.

        Parameters
        ----------
        app : Any
            Main framework application or container object.

        fastapi_app : fastapi.FastAPI
            FastAPI instance, used mainly for cleanup behavior.

        plugin_api : Any
            Plugin API returned by ``_internal()`` used for releasing resources.

        Notes
        -----
        - Suitable for closing files, flushing buffers, or synchronously
          releasing resources.
        """
        pass

    async def on_shutdown_async(self, app, fastapi_app, plugin_api):
        """
        Asynchronous shutdown hook executed as part of FastAPI's lifespan
        shutdown phase.

        Ideal for releasing async resources such as:
            - Async DB connections
            - Async queues
            - Background tasks
            - Async network clients

        Parameters
        ----------
        app : Any
            Main framework body.

        fastapi_app : fastapi.FastAPI
            The FastAPI instance.

        plugin_api : Any
            Plugin-scoped API returned by ``_internal()``.

        Notes
        -----
        - This hook should gracefully await cleanup tasks.
        - Avoid hanging the shutdown sequence indefinitely.
        """
        pass
