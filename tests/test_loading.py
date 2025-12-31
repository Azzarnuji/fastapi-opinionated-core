
import os
import pytest
from fastapi_opinionated.app import App
from fastapi_opinionated.routing.registry import RouterRegistry

from fastapi_opinionated.shared.base_plugin import BasePlugin
from typing import Generator
from unittest.mock import patch

# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def mock_enabled_plugins_file(tmp_path):
    # Setup .fastapi_opinionated/enabled_plugins.py
    # We need to change CWD or mock the path check.
    # Changing CWD can be dangerous for other tests.
    
    # Let's mock builtins.open and os.path.exists using pytest-mock if available, 
    # but I don't see it in pyproject.toml. 
    # I can use unittest.mock.patch.
    
    # Alternatively, write to the real path if I'm in a safe sandbox?
    # The sandbox is /home/zarnuji/project/my-framework/fastapi-opinionated-core/
    # I can write to .fastapi_opinionated/enabled_plugins.py and delete it after.
    
    config_dir = ".fastapi_opinionated"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        
    file_path = f"{config_dir}/enabled_plugins.py"
    
    # We need a real plugin class that can be imported via string.
    # We can use one of the built-in classes or define one in a file.
    # Let's use 'tests.test_loading.LoadablePlugin'
    
    content = """
ENABLED_PLUGINS = [
    "tests.test_loading.LoadablePlugin"
]
"""
    with open(file_path, "w") as f:
        f.write(content)
        
    yield file_path
    
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(config_dir) and not os.listdir(config_dir):
        os.rmdir(config_dir)

class LoadablePlugin(BasePlugin):
    public_name = "loadable"
    
    @staticmethod
    def _internal(app, fastapi_app, **kwargs):
        pass

# ==========================================
# TESTS
# ==========================================

def test_load_enabled_plugins_integration(mock_enabled_plugins_file):
    # reset plugins
    App._plugin_instances = {}
    App.fastapi = "mock_app" # Needs to be something for _enable_plugin_instance checks
    
    # Mocking _enable_plugin_instance to avoid executing full lifecycle 
    # and just verify it was called, OR just let it run.
    # Let's let it run but we need to ensure LoadablePlugin is valid.
    
    # LoadablePlugin defaults returns_plugin_api=True, so it needs command.
    # Let's register command or set returns_plugin_api=False.
    LoadablePlugin.returns_plugin_api = False
    
    App._load_enabled_plugins()
    
    assert "loadable" in App._plugin_instances
    assert isinstance(App._plugin_instances["loadable"], LoadablePlugin)


def test_router_registry_load_discovery():
    # RouterRegistry.load depends on relative paths from CWD basically.
    # So we must create a structure in CWD.
    
    test_dir = "tests_tmp_domains"
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)
        
    os.makedirs(f"{test_dir}/user/controllers")
    with open(f"{test_dir}/user/controllers/user_controller.py", "w") as f:
        f.write("""
from fastapi_opinionated.decorators.routing import Controller, Get
@Controller("/users")
class UserController:
    @Get("/")
    def index(self): pass
""")
        
    try:
        RouterRegistry.load(root=test_dir)
        
        # Verify
        found = False
        for c in RouterRegistry.controllers:
            if c["controller_name"] == "UserController":
                found = True
                break
        assert found
        
    finally:
        import shutil
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)



# @pytest.mark.skip(reason="Failing assertion despite fix, needs debug")
@patch("os._exit")
def test_router_registry_load_skip_ignored(mock_exit):
    test_dir = "tests_tmp_domains_skip"
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)
        
    os.makedirs(f"{test_dir}/__ignored__/controllers")
    with open(f"{test_dir}/__ignored__/controllers/bad.py", "w") as f:
        f.write("broken syntax")
        
    try:
        RouterRegistry.load(root=test_dir)
        # Should succeed (by skipping)
        assert not mock_exit.called
    except Exception as e:
        assert False, str(e)
    finally:
        import shutil
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

    
