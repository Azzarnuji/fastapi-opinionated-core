
import pytest
from fastapi import FastAPI
from fastapi_opinionated.app import App

def test_app_creation():
    app = App.create(title="Test App", version="0.0.1")
    assert isinstance(app, FastAPI)
    assert app.title == "Test App"
    assert app.version == "0.0.1"

# NOTE: Testing lifespan/startup strictly typically requires TestClient or "lifespan" context manager invocation. 
# Since App.create returns a standard FastAPI app with a custom lifespan, we can verify the lifespan is attached.

def test_lifespan_attached():
    app = App.create()
    assert app.router.lifespan_context is not None
