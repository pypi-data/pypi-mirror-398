import os
import io
import threading
from datetime import datetime
from functools import wraps


class Log:
    BYTES_IN_KB = 1024
    MILLISECOND_DIVISOR = 1000
    MIN_LOG_SIZE_KB = 10

    DEFAULT_MAX_LOG_KB = 300
    DEFAULT_MAX_ENTRIES = 100
    DEFAULT_CHAR_LIMIT = 300
    MAX_CHAR_LIMIT = 5000
    DEFAULT_TAIL_BYTES = 128 * 1024
    LOG_MARKER = "[LOG\\ENTRY]"
    DEFAULT_LOG_NAME = "sylriekit.log"

    LOG_DIR = os.getcwd()
    LOG_FILE_NAME = DEFAULT_LOG_NAME
    MAX_LOG_FILE_SIZE_B = DEFAULT_MAX_LOG_KB * BYTES_IN_KB
    TAIL_BYTES_ON_TRIM = DEFAULT_TAIL_BYTES
    CHAR_LIMIT = DEFAULT_CHAR_LIMIT
    CHAR_LIMIT_ENABLED = True

    _log_lock = threading.Lock()

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Log" in config.keys():
            log_config = config["Log"]
            cls.LOG_DIR = log_config.get("LOG_DIR", cls.LOG_DIR)
            cls.LOG_FILE_NAME = log_config.get("LOG_FILE_NAME", cls.LOG_FILE_NAME)
            cls.TAIL_BYTES_ON_TRIM = log_config.get("TAIL_BYTES_ON_TRIM", cls.TAIL_BYTES_ON_TRIM)
            cls.CHAR_LIMIT = log_config.get("CHAR_LIMIT", cls.CHAR_LIMIT)
            cls.LOG_MARKER = log_config.get("LOG_MARKER", cls.LOG_MARKER)
            cls.CHAR_LIMIT_ENABLED = log_config.get("CHAR_LIMIT_ENABLED", cls.CHAR_LIMIT_ENABLED)
            cls._apply_max_size_config(log_config.get("MAX_LOG_KB"), log_config.get("MAX_LOG_FILE_SIZE_B"))

    @classmethod
    def configure(cls, log_dir: str = None, log_file_name: str = None, max_log_kb: int = None, tail_bytes: int = None, char_limit: int = None, char_limit_enabled: bool = None):
        if log_dir:
            cls.LOG_DIR = log_dir
        if log_file_name:
            cls.LOG_FILE_NAME = log_file_name
        if tail_bytes is not None:
            cls.TAIL_BYTES_ON_TRIM = cls._safe_int(tail_bytes, cls.TAIL_BYTES_ON_TRIM)
        if char_limit is not None:
            cls.CHAR_LIMIT = cls._safe_int(char_limit, cls.CHAR_LIMIT)
        if char_limit_enabled is not None:
            cls.CHAR_LIMIT_ENABLED = bool(char_limit_enabled)
        cls._apply_max_size_config(max_log_kb, None)

    @classmethod
    def log(cls, msg: str, log_file_name: str = None, char_limit: int = None, enable_char_limit: bool = None):
        path = cls._resolve_log_path(log_file_name)
        if not path:
            return
        entry_message = cls._apply_char_limit(msg, char_limit, enable_char_limit)
        entry_text = f"\n{cls.LOG_MARKER}[{cls._formatted_timestamp()}]: {entry_message}"
        entry_bytes = entry_text.encode("utf-8")
        with cls._log_lock:
            with open(path, "ab") as f:
                f.write(entry_bytes)
            cls._trim_log_if_needed(path)

    @classmethod
    def get_entries(cls, max_entries: int = None, char_limit: int = None, log_file_name: str = None, since_timestamp: float = None, enable_char_limit: bool = None) -> list:
        entries_to_return = cls._safe_int(max_entries, cls.DEFAULT_MAX_ENTRIES)
        if entries_to_return <= 0:
            return []
        path = cls._resolve_log_path(log_file_name)
        if not path or not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []
        entries = cls._parse_log_entries(content)
        if not entries:
            return []
        if since_timestamp is not None:
            entries = [e for e in entries if cls._entry_timestamp(e) >= since_timestamp]
        if not entries:
            return []
        recent_entries = entries[-entries_to_return:]
        output = []
        for entry in reversed(recent_entries):
            limited = cls._apply_char_limit(entry.strip(), char_limit, enable_char_limit)
            output.append(limited)
        return output

    @classmethod
    def change_max_log_size(cls, new_size_in_kb: int):
        cls._apply_max_size_config(new_size_in_kb, None)

    @classmethod
    def auto_log(cls, log_file_name: str = None, char_limit: int = None, enable_char_limit: bool = None):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                derived_limit = cls._derive_char_limit(char_limit)
                derived_enabled = cls._derive_char_limit_enabled(enable_char_limit)
                cls.log(cls._build_call_message(func.__name__, args, kwargs, derived_limit, derived_enabled), log_file_name, derived_limit, derived_enabled)
                try:
                    result = func(*args, **kwargs)
                    cls.log(cls._build_result_message(func.__name__, result, derived_limit, derived_enabled), log_file_name, derived_limit, derived_enabled)
                    return result
                except Exception as exc:
                    cls.log(cls._build_error_message(func.__name__, exc, derived_limit, derived_enabled), log_file_name, derived_limit, derived_enabled)
                    raise
            return wrapper
        return decorator

    ### PRIVATE UTILITIES START
    @classmethod
    def _apply_max_size_config(cls, size_in_kb, size_in_bytes):
        if size_in_bytes is not None:
            try:
                cls.MAX_LOG_FILE_SIZE_B = max(int(size_in_bytes), cls.MIN_LOG_SIZE_KB * cls.BYTES_IN_KB)
                return
            except Exception:
                return
        if size_in_kb is None:
            return
        try:
            kb = int(size_in_kb)
        except (TypeError, ValueError):
            return
        if kb < cls.MIN_LOG_SIZE_KB:
            kb = cls.MIN_LOG_SIZE_KB
        cls.MAX_LOG_FILE_SIZE_B = kb * cls.BYTES_IN_KB

    @classmethod
    def _resolve_log_path(cls, log_file_name: str = None) -> str:
        name = log_file_name or cls.LOG_FILE_NAME or cls.DEFAULT_LOG_NAME
        if not name:
            return None
        directory = cls.LOG_DIR or os.getcwd()
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception:
            return None
        return os.path.join(directory, name)

    @classmethod
    def _formatted_timestamp(cls) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // cls.MILLISECOND_DIVISOR:03d}"

    @classmethod
    def _trim_log_if_needed(cls, path: str):
        try:
            if not os.path.exists(path):
                return
            size = os.path.getsize(path)
            if size <= cls.MAX_LOG_FILE_SIZE_B:
                return
            bytes_to_keep = min(size, cls.TAIL_BYTES_ON_TRIM)
            with open(path, "rb") as f:
                f.seek(-bytes_to_keep, io.SEEK_END)
                tail = f.read()
            marker_bytes = ("\n" + cls.LOG_MARKER).encode("utf-8")
            marker_index = tail.find(marker_bytes)
            if marker_index != -1:
                trimmed_tail = tail[marker_index + 1:]
            else:
                trimmed_tail = tail
            with open(path, "wb") as f:
                f.write(trimmed_tail)
        except Exception:
            pass

    @classmethod
    def _parse_log_entries(cls, content: str) -> list:
        marker = "\n" + cls.LOG_MARKER
        parts = content.split(marker)
        entries = []
        for index, part in enumerate(parts):
            if not part:
                continue
            if index == 0:
                if part.startswith(cls.LOG_MARKER):
                    entries.append(part)
            else:
                entries.append(cls.LOG_MARKER + part)
        return entries

    @classmethod
    def _entry_timestamp(cls, entry: str) -> float:
        try:
            if not entry.startswith(cls.LOG_MARKER + "["):
                return 0
            start_index = len(cls.LOG_MARKER) + 1
            end_index = entry.find("]", start_index)
            if end_index == -1:
                return 0
            timestamp_str = entry[start_index:end_index]
            return datetime.fromisoformat(timestamp_str).timestamp()
        except Exception:
            return 0

    @classmethod
    def _apply_char_limit(cls, value, char_limit: int = None, enable_char_limit: bool = None) -> str:
        try:
            text = str(value)
        except Exception:
            text = "Error"
        if not cls._derive_char_limit_enabled(enable_char_limit):
            return text
        limit = cls._derive_char_limit(char_limit)
        if limit <= 0:
            return text
        if len(text) <= limit:
            return text
        return text[:limit] + "..."

    @classmethod
    def _derive_char_limit(cls, char_limit: int = None) -> int:
        if char_limit is None:
            char_limit = cls.CHAR_LIMIT
        limit = cls._safe_int(char_limit, cls.DEFAULT_CHAR_LIMIT)
        if limit > cls.MAX_CHAR_LIMIT:
            return cls.MAX_CHAR_LIMIT
        return limit

    @classmethod
    def _derive_char_limit_enabled(cls, enable_char_limit: bool = None) -> bool:
        if enable_char_limit is None:
            return bool(cls.CHAR_LIMIT_ENABLED)
        return bool(enable_char_limit)

    @classmethod
    def _safe_int(cls, value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _stringify_data(cls, value, char_limit: int, enable_char_limit: bool) -> str:
        return cls._apply_char_limit(value, char_limit, enable_char_limit)

    @classmethod
    def _build_call_message(cls, func_name: str, args, kwargs, char_limit: int, enable_char_limit: bool) -> str:
        return f"Calling {func_name} with args={cls._stringify_data(args, char_limit, enable_char_limit)} kwargs={cls._stringify_data(kwargs, char_limit, enable_char_limit)}"

    @classmethod
    def _build_result_message(cls, func_name: str, result, char_limit: int, enable_char_limit: bool) -> str:
        return f"{func_name} returned {cls._stringify_data(result, char_limit, enable_char_limit)}"

    @classmethod
    def _build_error_message(cls, func_name: str, exc: Exception, char_limit: int, enable_char_limit: bool) -> str:
        return f"{func_name} raised {cls._stringify_data(type(exc).__name__ + ': ' + str(exc), char_limit, enable_char_limit)}"
    ### PRIVATE UTILITIES END