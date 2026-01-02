import time
import threading
import tracemalloc
from functools import wraps


class Profiler:
    MILLISECONDS_IN_SECOND = 1000
    BYTES_IN_KB = 1024
    MIN_ENTRIES = 1
    MIN_CHAR_LIMIT = 1
    DEFAULT_NAME = "profile"
    DEFAULT_ERROR_PLACEHOLDER = "<error>"

    ENABLED = True
    TRACK_MEMORY = True
    CAPTURE_RESULT = False
    RESULT_CHAR_LIMIT = 400
    MAX_ENTRIES = 200

    _records = []
    _lock = threading.Lock()

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Profile" in config.keys():
            profile_config = config["Profile"]
            cls.ENABLED = profile_config.get("ENABLED", cls.ENABLED)
            cls.TRACK_MEMORY = profile_config.get("TRACK_MEMORY", cls.TRACK_MEMORY)
            cls.CAPTURE_RESULT = profile_config.get("CAPTURE_RESULT", cls.CAPTURE_RESULT)
            cls.RESULT_CHAR_LIMIT = cls._normalize_char_limit(profile_config.get("RESULT_CHAR_LIMIT", cls.RESULT_CHAR_LIMIT))
            cls.MAX_ENTRIES = cls._normalize_entries(profile_config.get("MAX_ENTRIES", cls.MAX_ENTRIES))

    @classmethod
    def configure(cls, enabled: bool = None, track_memory: bool = None, capture_result: bool = None, result_char_limit: int = None, max_entries: int = None):
        if enabled is not None:
            cls.ENABLED = bool(enabled)
        if track_memory is not None:
            cls.TRACK_MEMORY = bool(track_memory)
        if capture_result is not None:
            cls.CAPTURE_RESULT = bool(capture_result)
        if result_char_limit is not None:
            cls.RESULT_CHAR_LIMIT = cls._normalize_char_limit(result_char_limit)
        if max_entries is not None:
            cls.MAX_ENTRIES = cls._normalize_entries(max_entries)

    @classmethod
    def context(cls, name: str = None, track_memory: bool = None, capture_result: bool = None, result_char_limit: int = None):
        if not cls.ENABLED:
            return _Profile_NoOp()
        derived_name = cls._derive_name(name)
        derived_track_memory = cls._derive_flag(track_memory, cls.TRACK_MEMORY)
        derived_capture = cls._derive_flag(capture_result, cls.CAPTURE_RESULT)
        limit = cls._normalize_char_limit(result_char_limit if result_char_limit is not None else cls.RESULT_CHAR_LIMIT)
        return _Profile_Session(cls, derived_name, derived_track_memory, derived_capture, limit)

    @classmethod
    def profile(cls, name: str = None, track_memory: bool = None, capture_result: bool = None, result_char_limit: int = None):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                session = cls.context(name or func.__name__, track_memory, capture_result, result_char_limit)
                if isinstance(session, _Profile_NoOp):
                    return func(*args, **kwargs)
                with session as handle:
                    result = func(*args, **kwargs)
                    if handle.capture_result:
                        handle.set_result(result)
                return result

            return wrapper

        return decorator

    @classmethod
    def measure(cls, func, args: tuple = None, kwargs: dict = None, name: str = None, track_memory: bool = None, capture_result: bool = None, result_char_limit: int = None):
        call_args = args if args is not None else tuple()
        call_kwargs = kwargs if kwargs is not None else {}
        session = cls.context(name or getattr(func, "__name__", cls.DEFAULT_NAME), track_memory, capture_result, result_char_limit)
        if isinstance(session, _Profile_NoOp):
            return {"result": func(*call_args, **call_kwargs), "record": None}
        with session as handle:
            result = func(*call_args, **call_kwargs)
            if handle.capture_result:
                handle.set_result(result)
        return {"result": result, "record": handle.record}

    @classmethod
    def get_records(cls, max_entries: int = None) -> list:
        limit = cls._normalize_entries(max_entries if max_entries is not None else cls.MAX_ENTRIES)
        with cls._lock:
            subset = list(cls._records[-limit:])
        return list(reversed(subset))

    ### PRIVATE UTILITIES START
    @classmethod
    def _derive_flag(cls, value, default_value: bool) -> bool:
        if value is None:
            return bool(default_value)
        return bool(value)

    @classmethod
    def _derive_name(cls, name: str) -> str:
        if name is None or str(name).strip() == "":
            return cls.DEFAULT_NAME
        return str(name)

    @classmethod
    def _normalize_entries(cls, value) -> int:
        normalized = cls._safe_int(value, cls.MAX_ENTRIES)
        if normalized < cls.MIN_ENTRIES:
            normalized = cls.MIN_ENTRIES
        return normalized

    @classmethod
    def _normalize_char_limit(cls, value) -> int:
        normalized = cls._safe_int(value, cls.RESULT_CHAR_LIMIT)
        if normalized < cls.MIN_CHAR_LIMIT:
            normalized = cls.MIN_CHAR_LIMIT
        return normalized

    @classmethod
    def _store_record(cls, record: dict):
        with cls._lock:
            cls._records.append(record)
            overflow = len(cls._records) - cls.MAX_ENTRIES
            if overflow > 0:
                del cls._records[0:overflow]

    @classmethod
    def _build_record(cls, name: str, started_at: float, ended_at: float, duration_ms: float, memory_kb, peak_memory_kb, result_preview: str, error_preview: str) -> dict:
        return {
            "name": name,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_ms": duration_ms,
            "memory_kb": memory_kb,
            "peak_memory_kb": peak_memory_kb,
            "result": result_preview,
            "error": error_preview,
        }

    @classmethod
    def _truncate_text(cls, value, limit: int):
        if value is None:
            return None
        text = cls._stringify(value)
        maximum = cls._normalize_char_limit(limit)
        if len(text) <= maximum:
            return text
        return text[:maximum] + "..."

    @classmethod
    def _safe_int(cls, value, default_value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default_value

    @classmethod
    def _stringify(cls, value) -> str:
        try:
            return str(value)
        except Exception:
            return cls.DEFAULT_ERROR_PLACEHOLDER
    ### PRIVATE UTILITIES END


class _Profile_Session:
    def __init__(self, owner: Profiler, name: str, track_memory: bool, capture_result: bool, result_char_limit: int):
        self.owner = owner
        self.name = name
        self.track_memory = track_memory
        self.capture_result = capture_result
        self.result_char_limit = result_char_limit
        self.started_at = None
        self.ended_at = None
        self.record = None
        self._start_perf = None
        self._start_memory = None
        self._tracemalloc_started = False
        self._result_value = None

    def __enter__(self):
        self.started_at = time.time()
        self._start_perf = time.perf_counter()
        if self.track_memory:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
                self._tracemalloc_started = True
            self._start_memory, _ = tracemalloc.get_traced_memory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ended_at = time.time()
        duration_ms = (time.perf_counter() - self._start_perf) * self.owner.MILLISECONDS_IN_SECOND
        memory_kb = None
        peak_memory_kb = None
        if self.track_memory:
            current, peak = tracemalloc.get_traced_memory()
            memory_kb = max(current - (self._start_memory or 0), 0) / self.owner.BYTES_IN_KB
            peak_memory_kb = max(peak - (self._start_memory or 0), 0) / self.owner.BYTES_IN_KB
            if self._tracemalloc_started:
                tracemalloc.stop()
        result_preview = None
        if self.capture_result:
            result_preview = self.owner._truncate_text(self._result_value, self.result_char_limit)
        error_preview = None
        if exc_val is not None:
            error_preview = self.owner._truncate_text(exc_val, self.result_char_limit)
        self.record = self.owner._build_record(self.name, self.started_at, self.ended_at, duration_ms, memory_kb, peak_memory_kb, result_preview, error_preview)
        self.owner._store_record(self.record)
        return False

    def set_result(self, value):
        self._result_value = value


class _Profile_NoOp:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False