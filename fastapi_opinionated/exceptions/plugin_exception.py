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


class PluginRuntimeException(RuntimeError):
    """
    Fatal exception untuk plugin.
    Me-warisi SystemExit → server langsung exit tanpa ditangkap FastAPI.
    """

    def __init__(
        self,
        plugin_name: str,
        message: str = "Plugin runtime error occurred",
        cause: Exception | None = None,
        **context
    ):
        # Bangun message yang clean
        error_msg = f"{message}"

        if cause is not None:
            error_msg += f" | Cause: {cause!r}"

        # Tambahkan context apabila ada
        if context:
            error_msg += f" | Context: {context}"

        # PASS hanya 1 ARGUMEN ke SystemExit
        super().__init__(error_msg)

        # Simpan atribut
        self.plugin_name = plugin_name
        self.cause = cause
        self.context = context
