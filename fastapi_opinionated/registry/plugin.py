# fastapi_opinionated/registry/plugin.py

from fastapi_opinionated.shared.base_plugin import BasePlugin
from fastapi_opinionated.shared.logger import ns_logger
from fastapi_opinionated.exceptions.plugin_exception import PluginRuntimeException
from fastapi_opinionated.utils import import_string
import inspect
import os

logger = ns_logger("PluginRegistry")


class PluginRegistry:
    """
    FINAL PluginRegistry — compatible with BasePlugin Hybrid version.

    Perubahan penting:
    - Support plugin_api optional (returns_plugin_api=False)
    - Command execution is optional
    - Register plugin even when no plugin_api returned
    - Keep backward compatibility for socket/eventbus plugins
    """

    metadata_scanning = False
    plugin = type("Plugins", (), {})()      # dynamic namespace
    _plugin_instances = {}                  # {"socket": instance}
    _plugin_config = {}                     # config before create()

    fastapi = None                          # assigned dalam App.create()

    # ===========================================================
    # USER-FACING PUBLIC API — CONFIGURE PLUGIN
    # ===========================================================
    @classmethod
    def configurePlugin(cls, plugin: BasePlugin, **config):
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
        Enable plugin with full lifecycle support.
        Now supports plugin_api optional.
        """
        if cls.fastapi is None:
            raise RuntimeError("FastAPI must be initialized first.")

        app = cls.fastapi

        pname = plugin.public_name or plugin.__class__.__name__

        # -------------------------------------------------------
        # PRE ENABLE
        # -------------------------------------------------------
        if plugin.__class__.on_pre_enable is not BasePlugin.on_pre_enable:
            plugin.on_pre_enable(cls, app)

        # -------------------------------------------------------
        # INTERNAL INITIALIZER (_internal)
        # plugin_api may NOT be required anymore
        # -------------------------------------------------------
        plugin_api = None

        if plugin.returns_plugin_api:
            # must call command, and must return plugin_api
            plugin_api = cls._cmd(plugin.command_name, **plugin_kwargs)

            if plugin_api is None:
                raise RuntimeError(
                    f"Plugin '{pname}' is expected to return plugin_api, "
                    f"but _internal() returned None."
                )
        else:
            # UI plugin / admin plugin
            # does NOT need to call command or _internal
            try:
                # still call internal if provided, but result ignored
                if plugin.__class__._internal is not BasePlugin._internal:
                    plugin._internal(cls, app, **plugin_kwargs)
            except Exception:
                pass
            plugin_api = None  # explicitly None

        # -------------------------------------------------------
        # ENABLE HOOK
        # -------------------------------------------------------
        if plugin.__class__.on_enable is not BasePlugin.on_enable:
            plugin.on_enable(cls, app, plugin_api)

        # -------------------------------------------------------
        # REGISTER NAMESPACE
        # plugin.plugin_name = plugin_api / None
        # -------------------------------------------------------
        setattr(cls.plugin, pname, plugin_api)
        cls._plugin_instances[pname] = plugin

        # -------------------------------------------------------
        # POST ENABLE
        # -------------------------------------------------------
        if plugin.__class__.on_post_enable is not BasePlugin.on_post_enable:
            plugin.on_post_enable(cls, app, plugin_api)

        return plugin_api

    # ===========================================================
    # LOAD ENABLED PLUGINS
    # ===========================================================
    @classmethod
    def _load_enabled_plugins(cls, metadata_only: bool = False):
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

            entry = cls._plugin_config.get(plugin_path)
            config = entry["config"] if entry else {}

            # Required config validation
            if not metadata_only:
                if getattr(plugin_instance, "required_config", False) and not config:
                    raise RuntimeError(
                        f"Plugin '{plugin_instance.public_name}' requires configuration.\n"
                        f"Configure it via:\n"
                        f"    App.configurePlugin({plugin_instance.__class__.__name__}(), ...)"
                    )

            # Use user-provided instance if exists
            if entry:
                plugin_instance = entry["instance"]

            # ENABLE (unless metadata_only)
            if not metadata_only:
                cls._enable_plugin_instance(plugin_instance, **config)
            else:
                cls._plugin_instances[plugin_instance.public_name] = plugin_instance

    # ===========================================================
    # CHECK IF ENABLED
    # ===========================================================
    @classmethod
    def ensure_enabled(cls, plugin_name: str) -> bool:
        if plugin_name not in cls._plugin_instances:
            raise PluginRuntimeException(
                plugin_name,
                (
                    f"Plugin '{plugin_name}' is not enabled or not installed.\n"
                    f"Enable via CLI:\n"
                    f"    fastapi-opinionated plugins enable plugin_path\n"
                ),
                {"file": plugin_name},
            )
        return True
