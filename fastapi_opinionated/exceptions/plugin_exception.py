class PluginException(Exception):
    """
    Base exception untuk semua plugin.
    Memuat: plugin_name, message, dan error cause (exception asli).
    """
    def __init__(
        self,
        plugin_name: str,
        message: str = "Plugin error occurred",
        cause: Exception | None = None,
        **context
    ):
        self.plugin_name = plugin_name
        self.cause = cause
        self.context = context or {}

        # Format error yang clean
        error_msg = f"[Plugin: {plugin_name}] {message}"
        if cause is not None:
            error_msg += f" | Cause: {cause!r}"

        super().__init__(error_msg)
