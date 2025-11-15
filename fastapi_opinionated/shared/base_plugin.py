from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """
    Base abstraction for all plugins.

    Existing hooks:
        - on_ready
        - on_ready_async
        - on_shutdown
        - on_shutdown_async

    NEW (Lifecycle V2 hooks — fully optional, non-breaking):
        ENABLE PHASE (before FastAPI startup):
            - on_pre_enable
            - on_enable
            - on_post_enable

        STARTUP PHASE (during lifespan startup):
            - on_plugins_loaded
            - on_controllers_loaded
            - on_app_ready

        SHUTDOWN PHASE (before existing shutdown hooks):
            - on_before_shutdown
            - on_before_shutdown_async
    """

    public_name: str = ""
    command_name: str = ""
    required_config: bool | None = False 

    # =======================================================
    # MANDATORY INTERNAL INIT
    # =======================================================
    @staticmethod
    @abstractmethod
    def _internal(app, fastapi_app, *args, **kwargs):
        raise NotImplementedError

    # =======================================================
    # LIFECYCLE V2 — ENABLE PHASE
    # =======================================================
    def on_pre_enable(self, app, fastapi_app):
        """
        Called BEFORE plugin._internal() is executed.
        Good for validating config, preparing state, etc.
        """
        pass

    def on_enable(self, app, fastapi_app, plugin_api):
        """
        Called AFTER plugin._internal() returns plugin_api.
        Good for binding API or initializing extra fields.
        """
        pass

    def on_post_enable(self, app, fastapi_app, plugin_api):
        """
        Called AFTER plugin is registered into App.plugin namespace.
        Good for discovery, file scanning, etc.
        """
        pass

    # =======================================================
    # LIFECYCLE V2 — STARTUP PHASE
    # =======================================================
    def on_plugins_loaded(self, app, fastapi_app):
        """
        Called once all plugins have been enabled,
        but BEFORE controllers are loaded.
        Good for plugin interdependency.
        """
        pass

    def on_controllers_loaded(self, app, fastapi_app):
        """
        Called AFTER RouterRegistry.load() finishes.
        Good for binding controller-based events, sockets, jobs.
        """
        pass

    def on_app_ready(self, app, fastapi_app):
        """
        Called AFTER on_ready & on_ready_async.
        At this point, the app is fully ready to serve requests.
        Good for starting workers, cron schedulers, etc.
        """
        pass

    # =======================================================
    # EXISTING HOOKS (UNCHANGED)
    # =======================================================
    def on_ready(self, app, fastapi_app, plugin_api):
        pass

    async def on_ready_async(self, app, fastapi_app, plugin_api):
        pass

    def on_shutdown(self, app, fastapi_app, plugin_api):
        pass

    async def on_shutdown_async(self, app, fastapi_app, plugin_api):
        pass

    # =======================================================
    # LIFECYCLE V2 — SHUTDOWN PHASE (NEW)
    # =======================================================
    def on_before_shutdown(self, app, fastapi_app, plugin_api):
        """
        Called BEFORE on_shutdown/on_shutdown_async.
        Good for flushing buffers, stopping schedulers, pausing queue.
        """
        pass

    async def on_before_shutdown_async(self, app, fastapi_app, plugin_api):
        """
        Async counterpart executed before async shutdown hooks.
        """
        pass
