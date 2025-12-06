# fastapi_opinionated/exceptions/middleware_exception.py

class MiddlewareException(Exception):
    def __init__(self, handler_name: str, middleware_name: str | None, msg: str):
        self.status_code = 500
        self.payload = {
            "handler": handler_name,
            "middleware": middleware_name,
            "msg": msg,
        }
        super().__init__(msg)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(handler={self.payload['handler']!r}, "
            f"middleware={self.payload['middleware']!r}, "
            f"msg={self.payload['msg']!r})"
        )
