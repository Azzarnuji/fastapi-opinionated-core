
import pytest
from fastapi_opinionated.routing.registry import RouterRegistry
from fastapi_opinionated.registry.plugin import PluginRegistry

@pytest.fixture(autouse=True)
def reset_registries():
    # Setup
    original_controllers = RouterRegistry.controllers[:]
    original_functions = RouterRegistry.function_routes[:]
    original_plugins = PluginRegistry._plugin_instances.copy()
    
    # Clear for test

    RouterRegistry.controllers = []
    RouterRegistry.function_routes = []
    
    from fastapi_opinionated.app import App
    App.fastapi = None
    App._plugin_instances = {}
    App._plugin_config = {}
    # Also clear dynamic plugin attributes if possible or recreating App.plugin object might be better but it's a class attribute type instance.
    App.plugin = type("Plugins", (), {})()
    
    yield
    
    # Teardown
    RouterRegistry.controllers = original_controllers
    RouterRegistry.function_routes = original_functions
    # Restore plugins if needed (though usually we don't need to restore for fresh run if we cleared it properly)
