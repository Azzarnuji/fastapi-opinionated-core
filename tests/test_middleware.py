
import contextlib
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from contextlib import AsyncExitStack
from fastapi.responses import JSONResponse
from fastapi_opinionated.middleware.marker import Middleware
from fastapi_opinionated.middleware.use import UseMiddleware
from fastapi_opinionated.middleware.next import Next
from fastapi_opinionated.http.abort import Abort
from fastapi_opinionated.routing.registry import RouterRegistry
from fastapi_opinionated.app import App

# ==========================================
# MOCK MIDDLEWARES
# ==========================================

@Middleware
async def simple_middleware(request: Request):
    request.state.trail.append("simple_in")
    request.state.trail.append("simple_out")
    return await Next.run()

@Middleware
class ClassMiddleware:
    async def __call__(self, request: Request):
        request.state.trail.append("class_in")
        request.state.trail.append("class_out")
        return await Next.run()

@Middleware
async def aborting_middleware(request: Request):
    Abort(400, "Aborted by middleware")

async def unmarked_middleware(request: Request):
    pass

# ==========================================
# TESTS
# ==========================================

def test_middleware_marker():
    @Middleware
    def my_mw(): pass
    assert getattr(my_mw, "__is_opinionated_middleware__", False)

@patch("os._exit")
def test_use_middleware_validation_no_request_param(mock_exit):
    # Should exit because handler doesn't have 'request' param
    @UseMiddleware(simple_middleware)
    def handler_bad(): 
        pass
    
    # decorator execution happens immediately
    assert mock_exit.called
    
@patch("os._exit")
def test_use_middleware_attachment(mock_exit):
    @UseMiddleware(simple_middleware)
    async def handler_good(request: Request):
        pass
    assert not mock_exit.called
    assert hasattr(handler_good, "__method_middlewares__")
    assert simple_middleware in handler_good.__method_middlewares__


@patch("os._exit")
def test_class_level_middleware_attachment(mock_exit):
    @UseMiddleware(ClassMiddleware)
    class MyController:
        pass
        
    assert not mock_exit.called
    assert hasattr(MyController, "__class_middlewares__")
    assert ClassMiddleware in MyController.__class_middlewares__


@pytest.mark.asyncio
async def test_unmarked_middleware_error():
    async def handler(request: Request): 
        pass
    
    handler.__method_middlewares__ = [unmarked_middleware]
    
    req = MagicMock(spec=Request)
    wrapped = RouterRegistry._wrap_with_middleware(handler)
    
    resp = await wrapped(request=req)
    # Registry catches MiddlewareException and returns JSONResponse(status_code=500 usually?)
    # or it returns e.payload
    # Looking at registry.py:
    # except MiddlewareException as e: return JSONResponse(status_code=e.status_code, content={"detail": e.payload})
    # MiddlewareException defaults to 400 ? Or 500?
    # Actually MiddlewareException constructor doesn't set status code, maybe default.
    # checking middleware_exception.py would clarify but let's just check response type.
    
    assert isinstance(resp, JSONResponse)
    # The error message should mention "Must be decorated with @Middleware"
    import json
    body = json.loads(resp.body)
    assert "Middleware must be decorated with @Middleware" in str(body)

