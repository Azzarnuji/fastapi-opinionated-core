from inspect import Signature, signature


class BasePlugin:
    """
    Plugin sangat minimal:
    - public_name: nama di App.plugin.<public_name>
    - command_name: nama event di AppCmd
    - target_class: library eksternal, untuk auto-generate signature
    """

    public_name: str = ""
    command_name: str = ""
    target_class = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not cls.target_class:
            return
        
        sig = signature(cls.target_class.__init__)

        # generate constructor dengan jumlah argumen dinamis
        def __init__(self, *args, **kwargs):
            self._plugin_args = args
            self._plugin_kwargs = kwargs

        __init__.__signature__ = sig
        setattr(cls, "__init__", __init__)