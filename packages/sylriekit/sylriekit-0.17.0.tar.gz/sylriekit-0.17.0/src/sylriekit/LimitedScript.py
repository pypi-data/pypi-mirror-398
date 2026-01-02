
import ast
import builtins
import importlib

from sylriekit.Constants import Constants


_LIMITED_SCRIPT_PROTECTED_ATTRS = {
    "CWD", "PATH_SEP", "USE_WHITELIST", "BLACKLISTED_DIRECTORIES",
    "WHITELISTED_DIRECTORIES", "FORCED_DIRECTORY", "MAX_DEPTH_DEFAULT",
    "MAX_FILES_DEFAULT", "MIN_FILES", "HIDDEN_PREFIX"
}


class LimitedScript(metaclass=Constants.protect_class_meta(_LIMITED_SCRIPT_PROTECTED_ATTRS, "LIMITED_SCRIPT_CONFIG_LOCKED")):
    

    ALLOWED_TOOLS = []

    @classmethod
    def load_config(cls, config:dict):
        cls._check_config_lock()
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "LimitedScript" in config.keys():
            config = config["LimitedScript"]
            cls.ALLOWED_TOOLS = config.get("ALLOWED_TOOLS", cls.ALLOWED_TOOLS)

    @classmethod
    def run(cls, py_script: str, context: dict = None) -> dict:
        tree = ast.parse(py_script, filename="<limited_script>")
        transformer = _LimitedScript_NoImportTransformer()
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        code = compile(new_tree, filename="<limited_script>", mode="exec")

        DANGEROUS_BUILTINS = frozenset([
            "eval", "exec", "compile", "open", "file", "__import__",
            "input", "raw_input", "help", "breakpoint", "exit", "quit"
        ])
        safe_builtins = {k: v for k, v in builtins.__dict__.items() if k not in DANGEROUS_BUILTINS}
        safe_globals = {"__builtins__": safe_builtins}

        for tool_name in cls.ALLOWED_TOOLS:
            try:
                tool_module = importlib.import_module(f"sylriekit.{tool_name}")
                tool_class = getattr(tool_module, tool_name, None)
                if tool_class:
                    safe_globals[tool_name] = tool_class
            except Exception:
                pass

        local_namespace = {}

        if context is not None:
            if not isinstance(context, dict):
                raise ValueError("Context must be a dict")
            local_namespace["CONTEXT"] = context
        else:
            local_namespace["CONTEXT"] = {}

        local_namespace["OUTPUT_CONTEXT"] = {}

        exec(code, safe_globals, local_namespace)

        result = {
            "namespace": local_namespace,
            "output_context": local_namespace.get("OUTPUT_CONTEXT", {})
        }
        return result

    @classmethod
    def allow_tool(cls, tool_name: str):
        cls._check_config_lock()
        if tool_name in cls.ALLOWED_TOOLS:
            return
        cls.ALLOWED_TOOLS.append(tool_name)

    @classmethod
    def lock_config(cls):
        cls._check_config_lock()
        cls.ALLOWED_TOOLS = tuple(cls.ALLOWED_TOOLS)
        Constants.define("LIMITED_SCRIPT_CONFIG_LOCKED", True)


    ### PRIVATE UTILITIES START
    @classmethod
    def _check_config_lock(cls):
        if Constants.get("LIMITED_SCRIPT_CONFIG_LOCKED", False):
            raise PermissionError("Config is locked and cannot be modified")
    ### PRIVATE UTILITIES END

class _LimitedScript_NoImportTransformer(ast.NodeTransformer):
    def visit_Import(self, node):
        raise SyntaxError("Import statements are not allowed in LimitedScript")

    def visit_ImportFrom(self, node):
        raise SyntaxError("Import statements are not allowed in LimitedScript")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            raise SyntaxError("Direct use of open() is not allowed; use allowed tools like Files instead")
        self.generic_visit(node)
        return node
