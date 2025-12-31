
import pytest
from fastapi_opinionated.decorators.routing import Controller, Get, Post, _normalize_path
from fastapi_opinionated.routing.registry import RouterRegistry

def test_normalize_path():
    assert _normalize_path(None) == "/"
    assert _normalize_path("") == "/"
    assert _normalize_path("  ") == "/"
    assert _normalize_path("users") == "/users"
    assert _normalize_path("/users") == "/users"

def test_class_based_controller_registration():
    @Controller("/users")
    class UserController:
        @Get("/")
        def list_users(self):
            return ["a", "b"]
            
        @Post("/create")
        def create_user(self):
            return {"id": 1}

    # Verify controller is registered
    assert len(RouterRegistry.controllers) == 1
    ctrl_meta = RouterRegistry.controllers[0]
    assert ctrl_meta["controller_name"] == "UserController"
    assert ctrl_meta["base"] == "/users"
    assert len(ctrl_meta["methods"]) == 2

    # Verify method metadata
    methods = {m["func_name"]: m for m in ctrl_meta["methods"]}
    assert "list_users" in methods
    assert methods["list_users"]["path"] == "/"
    assert methods["list_users"]["http_method"] == "GET"
    
    assert "create_user" in methods
    assert methods["create_user"]["path"] == "/create"
    assert methods["create_user"]["http_method"] == "POST"

def test_get_routes_extraction():
    @Controller("/api")
    class ApiController:
        @Get("/check")
        def check(self):
            pass

    routes = RouterRegistry.get_routes()
    assert len(routes) == 1
    r = routes[0]
    assert r["path"] == "/api/check"
    assert r["http_method"] == "GET"
    assert r["controller"] == "ApiController"


def test_functional_route_registration():
    def health_check():
        pass
    # Helper to trick the decorator into thinking this is a top-level function
    health_check.__qualname__ = "health_check"
    
    # Manually apply decorator
    Get("/health")(health_check)
        
    assert len(RouterRegistry.function_routes) == 1
    r = RouterRegistry.function_routes[0]
    assert r["path"] == "/health"
    assert r["http_method"] == "GET"
    assert r["handler"] == health_check
    assert r["controller"] is None

def test_duplicate_route_detection():
    # Define a functional route
    def ping1(): pass
    ping1.__qualname__ = "ping1"
    Get("/ping")(ping1)
    
    # Define class based route that conflicts
    @Controller("/")
    class PingController:
        @Get("ping")
        def ping2(self): pass
            

    all_routes = RouterRegistry.get_routes()
    duplicates = RouterRegistry.detect_route_duplicates(all_routes)
    
    assert ("GET", "/ping") in duplicates
    assert len(duplicates[("GET", "/ping")]) == 2 # function + class

def test_duplicate_exception_in_router_creation():
    def dup1(): pass
    dup1.__qualname__ = "dup1"
    Get("/dup")(dup1)
    
    def dup2(): pass
    dup2.__qualname__ = "dup2"
    Get("/dup")(dup2)
    
    with pytest.raises(RuntimeError) as excinfo:
        RouterRegistry.as_fastapi_router()
    
    assert "Duplicate route definitions detected" in str(excinfo.value)

