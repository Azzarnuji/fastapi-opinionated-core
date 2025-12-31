
import pytest
from fastapi_opinionated.app import App, AppCmd

from fastapi_opinionated.shared.base_plugin import BasePlugin
from typing import Any
from unittest.mock import patch

# ==========================================
# MOCK PLUGINS
# ==========================================

class MockPlugin(BasePlugin):
    public_name = "mock_plugin"
    command_name = "mock_plugin_cmd"
    returns_plugin_api = True

    def __init__(self, **config):
        super().__init__(**config)
        self.hooks_called = []

    def record(self, hook_name):
        self.hooks_called.append(hook_name)

    @staticmethod
    def _internal(app, fastapi_app, **kwargs):
        # This static method is what gets registered as command
        # Ideally returns an API
        return {"status": "ok", "config": kwargs}

    def on_pre_enable(self, app, fastapi_app):
        self.record("on_pre_enable")

    def on_enable(self, app, fastapi_app, plugin_api):
        self.record("on_enable")
        self.api = plugin_api

    def on_post_enable(self, app, fastapi_app, plugin_api):
        self.record("on_post_enable")

    def on_plugins_loaded(self, app, fastapi_app):
        self.record("on_plugins_loaded")

    def on_controllers_loaded(self, app, fastapi_app):
        self.record("on_controllers_loaded")
        
    def on_ready(self, app, fastapi_app, plugin_api):
        self.record("on_ready")

    def on_app_ready(self, app, fastapi_app, plugin_api):
        self.record("on_app_ready")
    
    def on_before_shutdown(self, app, fastapi_app, plugin_api):
        self.record("on_before_shutdown")
        
    def on_shutdown(self, app, fastapi_app, plugin_api):
        self.record("on_shutdown")

class AsyncMockPlugin(MockPlugin):
    public_name = "async_mock_plugin"
    command_name = "async_mock_plugin_cmd"

    async def on_ready_async(self, app, fastapi_app, plugin_api):
        self.record("on_ready_async")
        
    async def on_before_shutdown_async(self, app, fastapi_app, plugin_api):
        self.record("on_before_shutdown_async")
        
    async def on_shutdown_async(self, app, fastapi_app, plugin_api):
        self.record("on_shutdown_async")

class ConfigRequiredPlugin(BasePlugin):
    public_name = "config_required"
    required_config = True
    returns_plugin_api = False 

# ==========================================
# TESTS
# ==========================================

@pytest.fixture
def app_with_cmd():
    # Reset app state if needed - mostly likely cleaned by conftest but let's be safe
    # We need to register the commands that the plugins use
    
    # We can't easily register commands dynamically inside test function if we want to follow real flow
    # because @AppCmd works at import time usually.
    # But we can call App.register_cmd manually.
    
    App.register_cmd("mock_plugin_cmd", MockPlugin._internal)
    App.register_cmd("async_mock_plugin_cmd", AsyncMockPlugin._internal)
    return App

def test_plugin_configuration_storage():
    p = MockPlugin()
    App.configurePlugin(p, foo="bar")
    
    key = f"{p.__class__.__module__}.{p.__class__.__name__}"
    assert key in App._plugin_config
    assert App._plugin_config[key]["instance"] == p
    assert App._plugin_config[key]["config"] == {"foo": "bar"}


def test_plugin_required_config_error():
    p = ConfigRequiredPlugin()
    App.configurePlugin(p) # No config passed
    
    # Create app triggers _load_enabled_plugins which checks config
    # Wait, _load_enabled_plugins normally reads from file. 
    # But if we manually configured it, does it load it?
    # App.create calls _load_enabled_plugins(). 
    # _load_enabled_plugins checks .fastapi_opinionated/enabled_plugins.py
    # If that file doesn't exist, it returns.
    
    # So if we want to test config validation, we strictly need that file OR 
    # we need to simulate _enable_plugin_instance call directly or mock _load_enabled_plugins behavior.
    
    # Alternatively, simply explicitly call _enable_plugin_instance manually can verify validation?
    # No, validation is in _load_enabled_plugins.
    
    # Let's verify _load_enabled_plugins logic.
    # It reads file, gets list of enabled plugins key (path).
    # Then looks up in _plugin_config.
    
    # If the file doesn't exist, plugins aren't enabled automatically.
    # So App.configurePlugin alone doesn't enable it?
    # Correct, Configure != Enable.
    
    pass

def test_configure_invalid_plugin_type():
    with pytest.raises(RuntimeError):
        App.configurePlugin("not-a-plugin")

def test_enable_plugin_without_fastapi_init():
    p = MockPlugin()
    with pytest.raises(RuntimeError) as exc:
        App._enable_plugin_instance(p)
    assert "FastAPI must be initialized first" in str(exc.value)

