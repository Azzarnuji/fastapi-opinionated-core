from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_opinionated.routing.registry import RouterRegistry
from fastapi_opinionated.shared.base_plugin import BasePlugin
from fastapi_opinionated.shared.logger import ns_logger
from fastapi_opinionated.exceptions.plugin_exception import PluginRuntimeException
from fastapi_opinionated.utils import import_string
import inspect
import os
logger = ns_logger("PluginRegistry")
class PluginRegistry:
    metadata_scanning = False
    plugin = type("Plugins", (), {})()
    
    # {"socket": plugin_instance }
    _plugin_instances = {}

    # {"fastapi_opinionated_socket.plugin.SocketPlugin": {"instance": p, "config": {...}}}
    _plugin_config = {}
    
    # ===========================================================
    # USER-FACING PUBLIC API — CONFIGURE PLUGIN
    # ===========================================================
    @classmethod
    def configurePlugin(cls, plugin: BasePlugin, **config):
        """
        User sets configuration for a plugin instance BEFORE App.create().
        """
        if not isinstance(plugin, BasePlugin):
            raise RuntimeError("plugin must be an instance of BasePlugin")

        module = plugin.__class__.__module__
        name = plugin.__class__.__name__
        full_path = f"{module}.{name}"

        cls._plugin_config[full_path] = {
            "instance": plugin,
            "config": config,
        }
        
    # ===========================================================
    # INTERNAL — ENABLE PLUGIN INSTANCE
    # ===========================================================
    @classmethod
    def _enable_plugin_instance(cls, plugin: BasePlugin, **plugin_kwargs):
        """
        Internal enabling only — user never calls this manually.
        """
        if cls.fastapi is None:
            raise RuntimeError("FastAPI must be initialized first.")

        app = cls.fastapi

        # PRE ENABLE
        if hasattr(plugin, "on_pre_enable"):
            plugin.on_pre_enable(cls, app)

        # Internal initializer
        plugin_api = cls._cmd(plugin.command_name, **plugin_kwargs)

        # ON ENABLE
        if hasattr(plugin, "on_enable"):
            plugin.on_enable(cls, app, plugin_api)

        # Register in namespace
        setattr(cls.plugin, plugin.public_name, plugin_api)
        cls._plugin_instances[plugin.public_name] = plugin

        # POST ENABLE
        if hasattr(plugin, "on_post_enable"):
            plugin.on_post_enable(cls, app, plugin_api)

        return plugin_api
    
    # ===========================================================
    # LOAD ENABLED PLUGINS (EXECUTED AFTER FASTAPI EXISTS)
    # ===========================================================
    @classmethod
    def _load_enabled_plugins(cls, metadata_only: bool = False):
        """
        Read enabled plugins from .fastapi_opinionated/enabled_plugins.py.
        Instantiate + apply config + enable internally.
        """
        if metadata_only and not cls.metadata_scanning:
            raise RuntimeError(
                "metadata_only load is only permitted during CLI metadata scanning."
            )
        CONFIG_FILE = ".fastapi_opinionated/enabled_plugins.py"
        if not os.path.exists(CONFIG_FILE):
            return

        cfg = {}
        try:
            exec(open(CONFIG_FILE).read(), cfg)
        except Exception as e:
            raise RuntimeError(f"Failed loading enabled plugins: {e}")

        enabled = cfg.get("ENABLED_PLUGINS", [])
        for plugin_path in enabled:
            PluginClass = import_string(plugin_path)
            plugin_instance = PluginClass()

            # Retrieve user config (if any)
            entry = cls._plugin_config.get(plugin_path)
            # logger.info(f"Config entry for plugin '{plugin_path}': {entry}")
            config = entry["config"] if entry else {}
        
            # Required config validation
            if not metadata_only:
                if getattr(plugin_instance, "required_config", False) and not config:
                    raise RuntimeError(
                        f"Plugin '{plugin_instance.public_name}' requires configuration.\n\n"
                        f"Please configure it via:\n"
                        f"    App.configurePlugin({plugin_instance.__class__.__name__}(), ...)\n"
                    )

            # If user defined a custom instance, use that
            if entry:
                plugin_instance = entry["instance"]

            # ENABLE internally
            if not metadata_only:
                cls._enable_plugin_instance(plugin_instance, **config)
            else:
                cls._plugin_instances[plugin_instance.public_name] = plugin_instance

    @classmethod
    def ensure_enabled(cls, plugin_name: str) -> bool:
        """
        Check if a plugin is enabled by its public_name.
        """
        if plugin_name not in cls._plugin_instances:
            raise PluginRuntimeException(
                plugin_name, 
                (
                    f"Plugin '{plugin_name}' is not enabled or not installed.\n"
                    f"Enable it via CLI: fastapi-opinionated plugins enable plugin_path\n"
                ),
                {
                    "file": plugin_name,
                }
            )
        return True