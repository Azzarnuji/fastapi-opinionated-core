# fastapi_opinionated/shared/base_plugin.py

import inspect

class BasePlugin:
    """
    Base class for all FastAPI Opinionated plugins.
    Provides:
    - Lifecycle hooks
    - Plugin API returning (optional)
    - Publishable plugin metadata
    - Plugin configuration support
    """

    # Human-friendly name (for CLI listing)
    public_name: str = None

    # Unique command name (for CLI enable/disable)
    command_name: str = None

    # Whether plugin expects config passed in App.configurePlugin()
    required_config: bool = False

    # Whether plugin exposes publishable files (e.g., UI controllers)
    publishable: bool = False

    # Name of folder inside plugin root that contains publishable files
    publish_dir: str = "publish"

    # Whether plugin returns plugin_api (EventBus & Socket do, UI type usually not)
    returns_plugin_api: bool = True

    def __init__(self, **config):
        """
        Store plugin config passed by App.configurePlugin().
        """
        self.config = config or {}

    # ---------- INTERNAL HOOK FOR MOUNTING ----------
    @staticmethod
    def _internal(app, fastapi_app, **kwargs):
        """
        Must be implemented by plugin if returns_plugin_api=True.
        Should return plugin_api object OR None.
        """
        raise NotImplementedError(
            "Plugins must implement `_internal` unless returns_plugin_api=False."
        )

    # ---------- LIFECYCLE HOOKS ----------
    def on_pre_enable(self, app, fastapi_app):
        """Called before plugin enable (validation stage)."""
        pass

    def on_enable(self, app, fastapi_app, plugin_api):
        """Called after plugin enabled but before discovery."""
        pass

    def on_post_enable(self, app, fastapi_app, plugin_api):
        """Called after plugin is fully enabled."""
        pass

    def on_plugins_loaded(self, app, fastapi_app):
        """Called after all plugins are loaded, before controllers are discovered."""
        pass

    def on_controllers_loaded(self, app, fastapi_app):
        """Called after controllers discovery."""
        pass

    def on_ready(self, app, fastapi_app, plugin_api):
        """Called before serving (sync)."""
        pass

    async def on_ready_async(self, app, fastapi_app, plugin_api):
        """Async version of on_ready."""
        pass

    def on_app_ready(self, app, fastapi_app, plugin_api):
        """Final sync hook before server serves."""
        pass

    # ---------- SHUTDOWN ----------
    def on_before_shutdown(self, app, fastapi_app, plugin_api):
        pass

    async def on_before_shutdown_async(self, app, fastapi_app, plugin_api):
        pass

    def on_shutdown(self, app, fastapi_app, plugin_api):
        pass

    async def on_shutdown_async(self, app, fastapi_app, plugin_api):
        pass

    # ---------- HELPER ----------
    @classmethod
    def get_plugin_root(cls):
        """
        Return root path of plugin module using inspect.getfile().
        """
        import os
        plugin_file = inspect.getfile(cls)
        return os.path.dirname(plugin_file)
    
    @classmethod
    def get_publish_metadata(cls):
        """
        Return publish metadata if defined in plugin module.
        """
        from fastapi_opinionated.shared.publish_metadata import PublishMetadata
        import sys
        module = sys.modules[cls.__module__]
        if hasattr(module, "publish_metadata"):
            pm = getattr(module, "publish_metadata")
            if isinstance(pm, PublishMetadata):
                return pm
        return None