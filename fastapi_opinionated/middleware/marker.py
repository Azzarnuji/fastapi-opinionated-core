# fastapi_opinionated/middleware/marker.py
def Middleware(obj):
    obj.__is_opinionated_middleware__ = True
    return obj
