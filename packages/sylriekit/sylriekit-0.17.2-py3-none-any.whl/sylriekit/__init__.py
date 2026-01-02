import os
import importlib
import pkgutil
import inspect
import json

def _auto_import_modules():
    _loaded_modules = {}
    package_dir = os.path.dirname(__file__)
    for _, modname, _ in pkgutil.iter_modules([package_dir]):
        if modname.startswith('_') or modname == '__init__':
            continue
        try:
            module = importlib.import_module(f'.{modname}', package=__name__)
            primary_class = getattr(module, modname, None)
            if primary_class is not None:
                globals()[modname] = primary_class
                _loaded_modules[modname] = primary_class
        except (ImportError, AttributeError):
            pass
    globals()['__loaded_modules'] = _loaded_modules
    globals()['__all__'] = list(_loaded_modules.keys())

_auto_import_modules()

__version__ = "0.17.2"

def load_config(config: dict):
    config = config.copy()
    config["env"] = dict()
    config["api_keys"] = dict()
    for cls in __loaded_modules.values():
        if hasattr(cls, 'load_config'):
            cls.load_config(config)
    return config


def tool_functions(tool_name: str) -> list[str]:
    if tool_name not in __loaded_modules:
        raise ValueError(f"Tool '{tool_name}' not found")
    main_class = __loaded_modules[tool_name]
    funcs = [
        name for name in dir(main_class)
        if not name.startswith('_') and callable(getattr(main_class, name))
    ]
    return funcs


def get_code(tool_name: str, function_name: str) -> str:
    if tool_name not in __loaded_modules:
        raise ValueError(f"Tool '{tool_name}' not found")
    main_class = __loaded_modules[tool_name]
    if function_name == "*":
        return inspect.getsource(inspect.getmodule(main_class))
    attr = getattr(main_class, function_name, None)
    if attr is None:
        raise ValueError(f"Function '{function_name}' not found in {tool_name}")
    func = attr.__func__ if hasattr(attr, '__func__') else attr
    return inspect.getsource(func)


def generate_default_config(file_name: str="default_config.json", include_tools="*") -> None:
    if include_tools == "*":
        tools_to_include = list(__loaded_modules.keys())
    else:
        tools_to_include = include_tools

    config = {}
    for tool_name in tools_to_include:
        if tool_name not in __loaded_modules:
            continue
        cls = __loaded_modules[tool_name]
        if not hasattr(cls, 'load_config'):
            continue

        tool_config = {}
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            if not attr_name.isupper():
                continue
            value = getattr(cls, attr_name)
            if callable(value):
                continue
            try:
                json.dumps(value)
                tool_config[attr_name] = value
            except (TypeError, ValueError):
                pass

        if tool_config:
            config[tool_name] = tool_config

    with open(file_name, 'w') as f:
        json.dump(config, f, indent=2)


def help() -> None:
    print("sylriekit.tool_functions(tool_name: str) -> list[str]:")
    print("  Returns all non-private functions from the tool's main class.")
    print("")
    print("sylriekit.get_code(tool_name: str, function_name: str) -> str:")
    print("  Returns the source code of the function.")
    print("  Use '*' as function_name to get the entire file's source code.")
    print("")
    print("sylriekit.generate_default_config(file_name: str, include_tools='*'):")
    print("  Generates a JSON config file with all configurable values and defaults.")
    print("  Use '*' for all tools or pass a list of tool names.")
    print("")
    print("Examples:")
    print("  >>> sylriekit.tool_functions('Files')")
    print("  ['describe', 'read', ...]")
    print("  >>> sylriekit.get_code('Files', 'read')")
    print("  def read(cls, file_path): ...")
    print("  >>> sylriekit.get_code('Files', '*')")
    print("  # Returns entire Files.py source")
    print("  >>> sylriekit.generate_default_config()")
    print("  >>> sylriekit.generate_default_config('custom_name.json', ['Files', 'LLM'])")
