
from fastapi_opinionated.app import App

def AppCmd(name: str):
    """
    Decorator factory that registers a callable as an application command.

    AppCmd(name) returns a decorator which, when applied to a function, registers that
    function with the application's command registry via App.register_cmd(name, func)
    and returns the original function. Use this to mark functions as named commands
    handled by the application (e.g., CLI commands or dispatchable handlers).

    Parameters
    ----------
    name : str
        The name under which the function will be registered in the application's
        command registry.

    Returns
    -------
    Callable[[Callable], Callable]
        A decorator that registers the decorated function and returns it unchanged.

    Example
    -------
    @AppCmd("migrate")
    def migrate_db(...):
        \"\"\"Perform database migration.\"\"\"
        ...

    Notes
    -----
    - Side effect: calls App.register_cmd(name, func) at decoration time.
    - The decorated function object is returned, allowing normal use and imports.
    """
    def decorator(func):
        # register fungsi + metadata
        App.register_cmd(
            name,
            func,
        )
        return func
    return decorator