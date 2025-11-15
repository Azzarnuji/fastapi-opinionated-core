from fastapi_opinionated.shared.logger import ns_logger

logger = ns_logger("PluginRegistryStore")

class PluginRegistryStore:
    registries = {}

    @classmethod
    def add(cls, plugin_name, key, value):
        if plugin_name not in cls.registries:
            cls.registries[plugin_name] = {}

        registry = cls.registries[plugin_name]

        if key not in registry:
            registry[key] = []

        registry[key].append(value)

    @classmethod
    def get(cls, plugin_name):
        """
        Ambil semua metadata plugin -> langsung hapus registry nya.
        """
        registry = cls.registries.get(plugin_name, {})
        return registry
