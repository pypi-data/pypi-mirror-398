import time
import threading
from functools import wraps


class Cache:
    MIN_CACHE_SIZE = 1
    NO_EXPIRATION = 0

    DEFAULT_TTL_S = 60
    DEFAULT_MAX_CACHE_SIZE = 256
    ENABLED = True

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Cache" in config.keys():
            cache_config = config["Cache"]
            cls.ENABLED = cache_config.get("ENABLED", cls.ENABLED)
            cls.DEFAULT_TTL_S = cls._resolve_ttl_value(cache_config.get("DEFAULT_TTL_S", cls.DEFAULT_TTL_S))
            cls.DEFAULT_MAX_CACHE_SIZE = cls._resolve_size_value(cache_config.get("DEFAULT_MAX_CACHE_SIZE", cls.DEFAULT_MAX_CACHE_SIZE))

    @classmethod
    def cache(cls, ttl_s: int = None, max_size: int = None, match_condition=None):
        def decorator(func):
            cache_entries = []
            lock = threading.Lock()

            @wraps(func)
            def wrapper(*args, **kwargs):
                if not cls.ENABLED:
                    return func(*args, **kwargs)
                effective_ttl = cls._resolve_ttl_value(ttl_s if ttl_s is not None else cls.DEFAULT_TTL_S)
                effective_size = cls._resolve_size_value(max_size if max_size is not None else cls.DEFAULT_MAX_CACHE_SIZE)
                key = cls._make_key(args, kwargs)
                now = cls._now()
                with lock:
                    cls._purge_expired(cache_entries, now, effective_ttl)
                    hit = cls._get_cached(cache_entries, key, match_condition, args, kwargs)
                    if hit is not None:
                        return hit
                result = func(*args, **kwargs)
                with lock:
                    cls._store(cache_entries, key, result, now, effective_size)
                return result

            return wrapper

        return decorator

    ### PRIVATE UTILITIES START
    @classmethod
    def _resolve_ttl_value(cls, value):
        seconds = cls._safe_int(value, cls.DEFAULT_TTL_S)
        if seconds is None:
            seconds = cls.DEFAULT_TTL_S
        if seconds < cls.NO_EXPIRATION:
            seconds = cls.NO_EXPIRATION
        return seconds

    @classmethod
    def _resolve_size_value(cls, value):
        size = cls._safe_int(value, cls.DEFAULT_MAX_CACHE_SIZE)
        if size is None:
            size = cls.DEFAULT_MAX_CACHE_SIZE
        if size < cls.MIN_CACHE_SIZE:
            size = cls.MIN_CACHE_SIZE
        return size

    @classmethod
    def _make_key(cls, args, kwargs) -> tuple:
        args_repr = tuple(cls._stringify(arg) for arg in args)
        kwargs_repr = tuple((k, cls._stringify(v)) for k, v in sorted(kwargs.items()))
        return (args_repr, kwargs_repr)

    @classmethod
    def _now(cls) -> float:
        return time.time()

    @classmethod
    def _purge_expired(cls, entries: list, now: float, ttl_s: int):
        if ttl_s == cls.NO_EXPIRATION:
            return
        valid_entries = []
        for entry in entries:
            _, _, ts = entry
            if (now - ts) <= ttl_s:
                valid_entries.append(entry)
        entries[:] = valid_entries

    @classmethod
    def _get_cached(cls, entries: list, key: tuple, match_condition, args, kwargs):
        for cached_key, value, ts in reversed(entries):
            if cached_key != key:
                continue
            if not cls._matches(match_condition, args, kwargs, value, ts):
                continue
            return value
        return None

    @classmethod
    def _store(cls, entries: list, key: tuple, value, now: float, max_size: int):
        entries.append((key, value, now))
        if len(entries) > max_size:
            overflow = len(entries) - max_size
            del entries[0:overflow]

    @classmethod
    def _matches(cls, match_condition, args, kwargs, value, cached_at: float) -> bool:
        if match_condition is None:
            return True
        try:
            return bool(match_condition(args, kwargs, value, cached_at))
        except Exception:
            return False

    @classmethod
    def _stringify(cls, obj) -> str:
        try:
            return repr(obj)
        except Exception:
            return str(type(obj))

    @classmethod
    def _safe_int(cls, value, default_value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default_value
    ### PRIVATE UTILITIES END