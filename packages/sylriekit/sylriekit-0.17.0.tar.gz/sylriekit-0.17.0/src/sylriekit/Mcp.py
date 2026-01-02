import os
import sys
import time
import threading
import json
import importlib.util
from functools import wraps
from copy import deepcopy
import fastmcp

from sylriekit.Log import Log

class Mcp:
    DEFAULT_LOG_NAME = "mcp.log"
    MAX_LATENCIES = 2000
    MIN_LOG_SIZE_KB = 10
    MAX_CHAR_LIMIT = Log.MAX_CHAR_LIMIT
    DEFAULT_CHAR_LIMIT = 1000
    DEFAULT_MAX_ENTRIES = 100
    DEFAULT_TRUNCATE_LEN = 250
    PATH_TO_SELF_PLACEHOLDER = "{PATH_TO_SELF}"
    PY_FILE_PLACEHOLDER = "{PY_FILE}"
    NAME_PLACEHOLDER = "{NAME}"
    VERSION_PLACEHOLDER = "{VERSION}"

    ERRORS = []
    MCP_DIR = os.getcwd()
    MAX_LOG_FILE_SIZE_B = 300 * Log.BYTES_IN_KB
    TAIL_BYTES_ON_TRIM = Log.DEFAULT_TAIL_BYTES
    NAME = "unnamed-mcp-tool"
    VERSION = "1.0.0"
    LOG_LEVEL = 20
    STORAGE_FILENAME = "storage.json"

    _mcp_instance = None
    _errors_lock = threading.Lock()
    _lock = threading.Lock()
    _storage_lock = threading.RLock()
    _started_at = None
    _builtins_registered = False
    _metrics = {"calls": 0, "errors": 0, "latencies_ms": [], "tools_called": 0}
    DEBUG_TOOLS_ENABLED = True

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Mcp" in config.keys():
            mcp_config = config["Mcp"]
            cls.MCP_DIR = mcp_config.get("MCP_DIR", cls.MCP_DIR)
            cls.MAX_LOG_FILE_SIZE_B = mcp_config.get("MAX_LOG_FILE_SIZE_B", cls.MAX_LOG_FILE_SIZE_B)
            cls.TAIL_BYTES_ON_TRIM = mcp_config.get("TAIL_BYTES_ON_TRIM", cls.TAIL_BYTES_ON_TRIM)
            cls.NAME = mcp_config.get("NAME", cls.NAME)
            cls.VERSION = mcp_config.get("VERSION", cls.VERSION)
            cls.LOG_LEVEL = mcp_config.get("LOG_LEVEL", cls.LOG_LEVEL)
            cls.STORAGE_FILENAME = mcp_config.get("STORAGE_FILENAME", cls.STORAGE_FILENAME)
            
            old_debug = cls.DEBUG_TOOLS_ENABLED
            cls.DEBUG_TOOLS_ENABLED = mcp_config.get("DEBUG_TOOLS_ENABLED", cls.DEBUG_TOOLS_ENABLED)
            
            if cls.DEBUG_TOOLS_ENABLED != old_debug and cls._mcp_instance:
                if cls.DEBUG_TOOLS_ENABLED:
                    cls.add_debug_tools()
                else:
                    cls.remove_debug_tools()
        cls._configure_log_tool(cls.MAX_LOG_FILE_SIZE_B // Log.BYTES_IN_KB)

    ### MCP LIFECYCLE START
    @classmethod
    def configure(cls, name: str = None, version: str = None, mcp_dir: str = None, max_log_kb: int = None, log_level: int = None):
        if name:
            cls.NAME = name
        if version:
            cls.VERSION = version
        if mcp_dir:
            cls.MCP_DIR = mcp_dir
            try:
                os.makedirs(cls.MCP_DIR, exist_ok=True)
            except Exception:
                pass
        if isinstance(max_log_kb, int):
            cls.change_max_log_size(max_log_kb)
        if log_level is not None:
            cls.set_log_level(log_level)
        cls._configure_log_tool(max_log_kb)

    @classmethod
    def init(cls, override_name: str = None, override_version: str = None):
        if override_name:
            cls.NAME = override_name
        if override_version:
            cls.VERSION = override_version
        cls._mcp_instance = fastmcp.FastMCP(
            name=cls.NAME,
            version=cls.VERSION
        )
        if cls._started_at is None:
            cls._started_at = time.time()
        cls._ensure_builtins_registered()

    @classmethod
    def start(cls, transport_method: str = "stdio"):
        mcp = cls.ensure_initialized()
        cls.log(f"Starting MCP '{cls.NAME}' v{cls.VERSION} with transport={transport_method}")
        mcp.run(transport=transport_method)

    @classmethod
    def ensure_initialized(cls, name: str = None, version: str = None):
        if cls._mcp_instance is not None:
            cls._ensure_builtins_registered()
            return cls._mcp_instance
        with cls._lock:
            if cls._mcp_instance is None:
                cls.init(override_name=name or cls.NAME, override_version=version or cls.VERSION)
        return cls._mcp_instance

    @classmethod
    def get_instance(cls):
        return cls.ensure_initialized()

    @classmethod
    def connect_to(cls, config_file: str, mcp_template: dict, main_file: str = "main") -> dict:
        config_file = os.path.abspath(config_file)
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")

        main_file_path = cls._resolve_main_file(main_file)
        main_dir = os.path.dirname(main_file_path)
        main_filename = os.path.splitext(os.path.basename(main_file_path))[0]

        name, version = cls._extract_mcp_info(main_file_path)

        server_config = cls._process_template(mcp_template, main_dir, main_filename, name, version)

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "mcpServers" not in config:
            config["mcpServers"] = {}

        config["mcpServers"][name] = server_config

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        cls.log(f"Connected MCP '{name}' v{version} to {config_file}")

        return {
            "name": name,
            "version": version,
            "config_file": config_file,
            "server_config": server_config
        }

    @classmethod
    def disconnect_from(cls, config_file: str, name: str = None) -> bool:
        config_file = os.path.abspath(config_file)
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")

        server_name = name or cls.NAME

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "mcpServers" not in config:
            return False

        if server_name not in config["mcpServers"]:
            return False

        del config["mcpServers"][server_name]

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        cls.log(f"Disconnected MCP '{server_name}' from {config_file}")
        return True

    @classmethod
    def is_connected(cls, config_file: str, name: str = None) -> bool:
        config_file = os.path.abspath(config_file)
        if not os.path.exists(config_file):
            return False

        server_name = name or cls.NAME

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            return server_name in config.get("mcpServers", {})
        except Exception:
            return False
    ### MCP LIFECYCLE END

    ### TOOL DECORATOR START
    @classmethod
    def tool(cls, name: str = None, description: str = None, cache_ttl_s: int = None, ensure_output: bool = True):
        mcp = cls.ensure_initialized()

        def decorator(func):
            cache = {}

            @wraps(func)
            def wrapper(*args, **kwargs):
                key = None
                if cache_ttl_s:
                    try:
                        key = (args, tuple(sorted(kwargs.items())))
                        item = cache.get(key)
                        if item:
                            val, ts = item
                            if (time.time() - ts) < cache_ttl_s:
                                cls._log_level(10, f"[CACHE HIT] {func.__name__}{args}{kwargs}")
                                cls._record_invocation(func.__name__, from_cache=True)
                                return val
                    except Exception:
                        key = None

                t0 = time.time()
                cls._record_invocation(func.__name__, from_cache=False)

                try:
                    result = func(*args, **kwargs)
                    dt = (time.time() - t0) * 1000
                    cls._record_metrics(func.__name__, dt, error=False)
                    cls._log_level(10, f"[OK {dt:.1f}ms] {func.__name__}{args}{kwargs}")

                    normalized = result
                    if ensure_output and not isinstance(normalized, dict):
                        try:
                            normalized = {"result": str(normalized)}
                        except Exception:
                            normalized = {"result": "Error"}

                    if cache_ttl_s and key is not None:
                        cache[key] = (normalized, time.time())
                    return normalized

                except Exception as e:
                    dt = (time.time() - t0) * 1000
                    cls._record_metrics(func.__name__, dt, error=True)
                    tb = e.__traceback__
                    while tb and tb.tb_next:
                        tb = tb.tb_next
                    try:
                        file = tb.tb_frame.f_code.co_filename if tb else "<unknown>"
                        line = tb.tb_lineno if tb else -1
                    except Exception:
                        file = "<unknown>"
                        line = -1

                    log_msg = f"Error Name: `{type(e).__name__}: {e}`, Error File: `{file}`, Error Line: `{line}`"
                    with cls._errors_lock:
                        cls.ERRORS.append(log_msg)
                    cls.log(f"Error Occurred: {log_msg}")

                    if ensure_output:
                        error_obj = {
                            "type": cls._truncate(type(e).__name__),
                            "message": cls._truncate(str(e)),
                            "file": cls._truncate(file),
                            "line": int(line) if isinstance(line, int) else -1,
                        }
                        return {"error": error_obj}
                    raise

            register = mcp.tool(name=name, description=description)
            return register(wrapper)

        return decorator

    @classmethod
    def auto_error_handling(cls, default_return=None, max_len: int = 350):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    cls.log(f"Function {func.__name__} completed successfully with args: {args}, kwargs: {kwargs}. Result: {result}")
                    return result
                except Exception as e:
                    tb = e.__traceback__
                    while tb.tb_next:
                        tb = tb.tb_next
                    msg = f"Error Name: `{type(e).__name__}: {e}`, Error File: `{tb.tb_frame.f_code.co_filename}`, Error Line: `{tb.tb_lineno}`"
                    if len(msg) > max_len:
                        msg = msg[:max_len] + "..."
                    with cls._errors_lock:
                        cls.ERRORS.append(msg)
                    cls.log(f"Error Occurred: {msg}")
                    return default_return
            return wrapper
        return decorator
    ### TOOL DECORATOR END

    ### LOGGING START
    @classmethod
    def log(cls, msg: str):
        Log.log(msg, log_file_name=cls.DEFAULT_LOG_NAME, char_limit=cls.DEFAULT_CHAR_LIMIT, enable_char_limit=True)

    @classmethod
    def set_log_level(cls, level: int):
        try:
            cls.LOG_LEVEL = int(level)
        except Exception:
            pass

    @classmethod
    def change_max_log_size(cls, new_size_in_kb: int):
        try:
            kb = int(new_size_in_kb)
        except (TypeError, ValueError):
            return
        if kb < cls.MIN_LOG_SIZE_KB:
            kb = cls.MIN_LOG_SIZE_KB
        cls.MAX_LOG_FILE_SIZE_B = kb * Log.BYTES_IN_KB
        Log.change_max_log_size(kb)
        cls._configure_log_tool(kb)
        cls.log(f"Max log file size set to {kb} KB")

    @classmethod
    def get_log_entries(cls, max_entries: int = 100, char_limit: int = 1000) -> list:
        entries_limit = max_entries if max_entries is not None else cls.DEFAULT_MAX_ENTRIES
        char_limit_value = char_limit if char_limit is not None else cls.DEFAULT_CHAR_LIMIT
        return Log.get_entries(max_entries=entries_limit, char_limit=char_limit_value, log_file_name=cls.DEFAULT_LOG_NAME, since_timestamp=cls._started_at, enable_char_limit=True)
    ### LOGGING END

    ### ERROR HANDLING START
    @classmethod
    def get_errors(cls, max_entries: int = 100, char_limit: int = 1000) -> list:
        n = cls._safe_int(max_entries, cls.DEFAULT_MAX_ENTRIES)
        if n <= 0:
            return []
        limit = cls._safe_int(char_limit, cls.DEFAULT_CHAR_LIMIT)
        limit = max(1, min(limit, cls.MAX_CHAR_LIMIT))

        errors_snapshot = list(cls.ERRORS)
        recent = errors_snapshot[-n:]
        out = []
        for e in reversed(recent):
            s = str(e)
            if len(s) > limit:
                s = s[:limit] + "..."
            out.append(s)
        return out
    ### ERROR HANDLING END

    ### METRICS START
    @classmethod
    def health_snapshot(cls) -> dict:
        lat = cls._metrics["latencies_ms"]
        return {
            "name": cls.NAME,
            "version": cls.VERSION,
            "uptime_s": (time.time() - cls._started_at) if cls._started_at else None,
            "tools_called": cls._metrics.get("tools_called", 0),
            "calls": cls._metrics["calls"],
            "errors": cls._metrics["errors"],
            "p50_ms": cls._percentile(lat, 0.50),
            "p95_ms": cls._percentile(lat, 0.95),
        }
    ### METRICS END

    ### STORAGE START
    @classmethod
    def get_storage(cls) -> dict:
        path = cls._storage_path()
        if not path:
            return {}
        try:
            os.makedirs(cls.MCP_DIR, exist_ok=True)
        except Exception:
            return {}
        with cls._storage_lock:
            storage = cls._read_storage_locked(path)
        return deepcopy(storage)

    @classmethod
    def update_storage(cls, new_data: dict) -> dict:
        if not isinstance(new_data, dict):
            raise TypeError("update_storage expects a dict payload")
        path = cls._storage_path()
        if not path:
            return {}
        try:
            os.makedirs(cls.MCP_DIR, exist_ok=True)
        except Exception as exc:
            cls._log_level(20, f"Storage directory error: {exc}")
            return {}
        with cls._storage_lock:
            storage = deepcopy(cls._read_storage_locked(path))
            storage.update(deepcopy(new_data))
            cls._write_storage_locked(path, storage)
            return deepcopy(storage)
    ### STORAGE END

    ### PRIVATE UTILITIES START
    @classmethod
    def _log_level(cls, level: int, msg: str):
        if level >= cls.LOG_LEVEL:
            try:
                cls.log(msg)
            except Exception:
                pass

    @classmethod
    def _configure_log_tool(cls, max_log_kb):
        kb_value = None
        try:
            if max_log_kb is not None:
                kb_value = int(max_log_kb)
            else:
                kb_value = cls.MAX_LOG_FILE_SIZE_B // Log.BYTES_IN_KB
        except Exception:
            kb_value = None
        Log.configure(
            log_dir=cls.MCP_DIR,
            log_file_name=cls.DEFAULT_LOG_NAME,
            max_log_kb=kb_value,
            tail_bytes=cls.TAIL_BYTES_ON_TRIM,
            char_limit=cls.DEFAULT_CHAR_LIMIT,
            char_limit_enabled=True
        )

    @classmethod
    def _record_invocation(cls, tool_name: str, from_cache: bool):
        try:
            cls._metrics["tools_called"] += 1
        except Exception:
            pass

    @classmethod
    def _record_metrics(cls, tool_name: str, latency_ms: float, error: bool):
        m = cls._metrics
        m["calls"] += 1
        if error:
            m["errors"] += 1
        if len(m["latencies_ms"]) < cls.MAX_LATENCIES:
            m["latencies_ms"].append(latency_ms)

    @classmethod
    def _percentile(cls, data: list, p: float):
        if not data:
            return None
        d = sorted(data)
        k = int((len(d) - 1) * p)
        return d[k]

    @classmethod
    def _storage_path(cls):
        if not cls.MCP_DIR:
            return None
        return os.path.join(cls.MCP_DIR, cls.STORAGE_FILENAME)

    @classmethod
    def _read_storage_locked(cls, path: str) -> dict:
        if not os.path.exists(path):
            cls._write_storage_locked(path, {})
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            cls._log_level(20, f"Storage read error: {exc}")
        cls._write_storage_locked(path, {})
        return {}

    @classmethod
    def _write_storage_locked(cls, path: str, data: dict):
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data or {}, f, ensure_ascii=True, indent=2)
        os.replace(tmp_path, path)

    @classmethod
    def _truncate(cls, s: str, limit: int = None) -> str:
        if limit is None:
            limit = cls.DEFAULT_TRUNCATE_LEN
        try:
            s = str(s)
        except Exception:
            s = "Error"
        return s if len(s) <= limit else s[:limit] + "..."

    @classmethod
    def _safe_int(cls, value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _resolve_main_file(cls, main_file: str) -> str:
        if os.path.isabs(main_file):
            path = main_file
        else:
            caller_frame = sys._getframe(2)
            caller_file = caller_frame.f_globals.get("__file__")
            if caller_file:
                caller_dir = os.path.dirname(os.path.abspath(caller_file))
            else:
                caller_dir = os.getcwd()
            path = os.path.join(caller_dir, main_file)

        if not path.endswith(".py"):
            path = path + ".py"

        path = os.path.abspath(path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Main file not found: {path}")

        return path

    @classmethod
    def _extract_mcp_info(cls, main_file_path: str) -> tuple:
        try:
            spec = importlib.util.spec_from_file_location("_mcp_main_module", main_file_path)
            module = importlib.util.module_from_spec(spec)

            original_modules = dict(sys.modules)
            try:
                spec.loader.exec_module(module)
            finally:
                for key in list(sys.modules.keys()):
                    if key not in original_modules:
                        del sys.modules[key]

            name = getattr(module, "MCP_NAME", None) or getattr(module, "NAME", None) or cls.NAME
            version = getattr(module, "MCP_VERSION", None) or getattr(module, "VERSION", None) or cls.VERSION

            return name, version
        except Exception:
            return cls.NAME, cls.VERSION

    @classmethod
    def _process_template(cls, template: dict, main_dir: str, main_filename: str, name: str, version: str) -> dict:
        def replace_placeholders(value):
            if isinstance(value, str):
                result = value
                result = result.replace(cls.PATH_TO_SELF_PLACEHOLDER, main_dir)
                result = result.replace(cls.PY_FILE_PLACEHOLDER, main_filename)
                result = result.replace(cls.NAME_PLACEHOLDER, name)
                result = result.replace(cls.VERSION_PLACEHOLDER, version)
                return result
            elif isinstance(value, list):
                return [replace_placeholders(item) for item in value]
            elif isinstance(value, dict):
                return {k: replace_placeholders(v) for k, v in value.items()}
            return value

        return replace_placeholders(deepcopy(template))

    @classmethod
    def add_debug_tools(cls):
        mcp = cls._mcp_instance
        if not mcp:
            return

        @mcp.tool(name="health", description="Return a basic health snapshot of this MCP server including uptime, call counts, and latency percentiles.")
        def health() -> dict:
            return cls.health_snapshot()

        @mcp.tool(name="recent_logs", description="Return up to n recent log entries from this process only, newest-first.")
        def recent_logs(n: int = 50) -> list:
            return cls.get_log_entries(max_entries=n, char_limit=cls.DEFAULT_CHAR_LIMIT)

        @mcp.tool(name="recent_errors", description="Return up to n recent error messages collected during this process, newest-first.")
        def recent_errors(n: int = 50) -> list:
            return cls.get_errors(max_entries=n, char_limit=cls.DEFAULT_CHAR_LIMIT)

        @mcp.tool(name="check_previous_logs", description="Return logs from before the current session started.")
        def check_previous_logs(n: int = 50) -> list:
            entries = Log.get_entries(max_entries=5000, char_limit=cls.DEFAULT_CHAR_LIMIT, log_file_name=cls.DEFAULT_LOG_NAME, enable_char_limit=True)
            past = []
            for e in entries:
                if cls._started_at and Log._entry_timestamp(e) < cls._started_at:
                    past.append(e)
                    if len(past) >= n:
                        break
            return past

    @classmethod
    def remove_debug_tools(cls):
        mcp = cls._mcp_instance
        if not mcp:
            return

        for tool_name in ["health", "recent_logs", "recent_errors", "check_previous_logs"]:
            try:
                mcp.remove_tool(tool_name)
            except Exception:
                pass

    @classmethod
    def _ensure_builtins_registered(cls):
        if cls._builtins_registered or cls._mcp_instance is None:
            return

        if cls.DEBUG_TOOLS_ENABLED:
            cls.add_debug_tools()

        cls._builtins_registered = True
    ### PRIVATE UTILITIES END

