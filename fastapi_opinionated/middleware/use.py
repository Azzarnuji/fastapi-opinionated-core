from fastapi_opinionated.shared.logger import  ns_logger
import inspect
from fastapi_opinionated.exceptions.middleware_exception import (
    MiddlewareException)
import os
import sys

# fastapi_opinionated/middleware/use.py
logger = ns_logger("UseMiddleware")
def UseMiddleware(*middlewares):

    def decorator(target):
        try:
            sig = inspect.signature(target)
            request = sig.parameters.get("request")
            if request is None:
                raise MiddlewareException(
                    handler_name=target.__name__,
                    middleware_name=", ".join(m.__name__ for m in middlewares),
                    msg= f"Target function/method '{target.__name__}' must have a 'request' parameter to use middlewares."
                )
            logger.info(f"Applying middlewares: {', '.join(middleware.__name__ for middleware in middlewares)} to target: {target.__name__}")
            # ===== CLASS LEVEL =====
            if isinstance(target, type):
                existing = getattr(target, "__class_middlewares__", [])
                target.__class_middlewares__ = [*existing, *middlewares]
                return target

            # ===== METHOD / FUNCTION LEVEL =====
            existing = getattr(target, "__method_middlewares__", [])
            target.__method_middlewares__ = [*existing, *middlewares]
            target.__attached_middlewares__ = True
            return target
        except MiddlewareException as e:
            logger.error(e.__repr__())
            os._exit(1)

    return decorator
