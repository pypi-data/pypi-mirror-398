class _Constants_Meta(type):
    def __setattr__(cls, name, value):
        if name in cls.__dict__:
            raise PermissionError(f"Cannot modify constant '{name}'")
        super().__setattr__(name, value)

    def __delattr__(cls, name):
        raise PermissionError(f"Cannot delete constant '{name}'")


class Constants(metaclass=_Constants_Meta):
    _FROZEN = False

    @classmethod
    def load_config(cls, config: dict):
        cls._check_frozen()
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Constants" in config.keys():
            constants_config = config["Constants"]
            for key, value in constants_config.items():
                cls.define(key, value)

    @classmethod
    def define(cls, name: str, value):
        cls._check_frozen()
        if name.startswith("_"):
            raise ValueError("Constant names cannot start with underscore")
        if name in cls.__dict__:
            raise PermissionError(f"Constant '{name}' is already defined")
        setattr(cls, name, value)

    @classmethod
    def define_many(cls, constants: dict):
        cls._check_frozen()
        for name, value in constants.items():
            cls.define(name, value)

    @classmethod
    def freeze(cls):
        cls._FROZEN = True

    @classmethod
    def is_defined(cls, name: str) -> bool:
        return name in cls.__dict__ and not name.startswith("_")

    @classmethod
    def get(cls, name: str, default=None):
        if cls.is_defined(name):
            return getattr(cls, name)
        return default

    @classmethod
    def all(cls) -> dict:
        return {k: v for k, v in cls.__dict__.items() if not k.startswith("_") and not callable(v)}

    @classmethod
    def protect_class_meta(cls, protected_attrs: set, lock_constant: str):
        parent_cls = cls

        class _Protected_Meta(type):
            def __setattr__(meta_cls, name, value):
                if name in protected_attrs and parent_cls.get(lock_constant, False):
                    raise PermissionError(f"Cannot modify '{name}' - class is locked")
                super().__setattr__(name, value)

            def __delattr__(meta_cls, name):
                if name in protected_attrs:
                    raise PermissionError(f"Cannot delete '{name}'")
                super().__delattr__(name)

        return _Protected_Meta

    ### PRIVATE UTILITIES START
    @classmethod
    def _check_frozen(cls):
        if cls._FROZEN:
            raise PermissionError("Constants class is frozen and cannot be modified")
    ### PRIVATE UTILITIES END
