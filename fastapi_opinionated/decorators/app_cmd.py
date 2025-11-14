
from fastapi_opinionated.app import App

def AppCmd(name: str):
    def decorator(func):
        # register fungsi + metadata
        App.register_cmd(
            name,
            func,
        )
        return func
    return decorator