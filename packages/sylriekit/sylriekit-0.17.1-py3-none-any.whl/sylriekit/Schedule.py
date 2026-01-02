import os
import time
import threading
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    Observer = None
    FileSystemEventHandler = None


class Schedule:
    HOURS_IN_DAY = 24
    MINUTES_IN_HOUR = 60
    SECONDS_IN_MINUTE = 60
    SECONDS_IN_DAY = HOURS_IN_DAY * MINUTES_IN_HOUR * SECONDS_IN_MINUTE
    MIN_INTERVAL_S = 1
    MIN_POLL_INTERVAL_S = 1
    MIN_DAILY_FIELDS = 2
    MAX_TIME_FIELDS = 3
    TIME_SEPARATOR = ":"
    MAX_NAME_LENGTH = 128

    ENABLED = True
    TICK_INTERVAL_S = 1
    FILE_POLL_INTERVAL_S = 2
    MAX_SCHEDULES = 128
    WATCHDOG_ENABLED = True

    _schedules = {}
    _lock = threading.RLock()
    _runner_thread = None
    _stop_event = threading.Event()
    _watchdog_handlers = {}

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Schedule" in config.keys():
            schedule_config = config["Schedule"]
            cls.ENABLED = schedule_config.get("ENABLED", cls.ENABLED)
            cls.TICK_INTERVAL_S = cls._resolve_positive(schedule_config.get("TICK_INTERVAL_S", cls.TICK_INTERVAL_S), cls.TICK_INTERVAL_S, cls.MIN_INTERVAL_S)
            cls.FILE_POLL_INTERVAL_S = cls._resolve_positive(schedule_config.get("FILE_POLL_INTERVAL_S", cls.FILE_POLL_INTERVAL_S), cls.FILE_POLL_INTERVAL_S, cls.MIN_POLL_INTERVAL_S)
            cls.MAX_SCHEDULES = cls._resolve_positive(schedule_config.get("MAX_SCHEDULES", cls.MAX_SCHEDULES), cls.MAX_SCHEDULES, cls.MIN_INTERVAL_S)
            cls.WATCHDOG_ENABLED = schedule_config.get("WATCHDOG_ENABLED", cls.WATCHDOG_ENABLED)

    @classmethod
    def configure(cls, enabled: bool = None, tick_interval_s: int = None, file_poll_interval_s: int = None, max_schedules: int = None, watchdog_enabled: bool = None):
        if enabled is not None:
            cls.ENABLED = bool(enabled)
        if tick_interval_s is not None:
            cls.TICK_INTERVAL_S = cls._resolve_positive(tick_interval_s, cls.TICK_INTERVAL_S, cls.MIN_INTERVAL_S)
        if file_poll_interval_s is not None:
            cls.FILE_POLL_INTERVAL_S = cls._resolve_positive(file_poll_interval_s, cls.FILE_POLL_INTERVAL_S, cls.MIN_POLL_INTERVAL_S)
        if max_schedules is not None:
            cls.MAX_SCHEDULES = cls._resolve_positive(max_schedules, cls.MAX_SCHEDULES, cls.MIN_INTERVAL_S)
        if watchdog_enabled is not None:
            cls.WATCHDOG_ENABLED = bool(watchdog_enabled)

    @classmethod
    def schedule_interval(cls, name: str, func, interval_s: int, args: tuple = None, kwargs: dict = None, start_immediately: bool = True):
        if not cls.ENABLED:
            return False
        cls._validate_name(name)
        cls._validate_callable(func)
        interval = cls._normalize_interval(interval_s)
        args_value = tuple(args) if args is not None else tuple()
        kwargs_value = dict(kwargs) if kwargs is not None else {}
        now = cls._now()
        next_run = now if start_immediately else now + interval
        entry = {
            "name": name,
            "type": "interval",
            "func": func,
            "args": args_value,
            "kwargs": kwargs_value,
            "interval_s": interval,
            "target_seconds": None,
            "next_run": next_run,
            "last_run": None,
            "enabled": True,
            "directory": None,
            "pattern": None,
            "known_files": None,
            "last_poll": None,
            "use_watchdog": False
        }
        cls._store_schedule(entry)
        cls._ensure_worker()
        return True

    @classmethod
    def schedule_daily(cls, name: str, func, time_of_day: str, args: tuple = None, kwargs: dict = None):
        if not cls.ENABLED:
            return False
        cls._validate_name(name)
        cls._validate_callable(func)
        target_seconds = cls._time_string_to_seconds(time_of_day)
        args_value = tuple(args) if args is not None else tuple()
        kwargs_value = dict(kwargs) if kwargs is not None else {}
        now = cls._now()
        next_run = cls._next_daily_run(target_seconds, now)
        entry = {
            "name": name,
            "type": "daily",
            "func": func,
            "args": args_value,
            "kwargs": kwargs_value,
            "interval_s": None,
            "target_seconds": target_seconds,
            "next_run": next_run,
            "last_run": None,
            "enabled": True,
            "directory": None,
            "pattern": None,
            "known_files": None,
            "last_poll": None,
            "use_watchdog": False
        }
        cls._store_schedule(entry)
        cls._ensure_worker()
        return True

    @classmethod
    def schedule_file_watch(cls, name: str, func, directory: str, pattern: str = None, args: tuple = None, kwargs: dict = None, use_watchdog: bool = None):
        if not cls.ENABLED:
            return False
        cls._validate_name(name)
        cls._validate_callable(func)
        resolved_dir = cls._normalize_directory(directory)
        args_value = tuple(args) if args is not None else tuple()
        kwargs_value = dict(kwargs) if kwargs is not None else {}
        use_watchdog_value = cls._resolve_watchdog_flag(use_watchdog)
        if use_watchdog_value and cls._watchdog_supported():
            entry = cls._build_watchdog_entry(name, func, resolved_dir, pattern, args_value, kwargs_value)
            cls._store_schedule(entry)
            cls._start_watchdog(name, resolved_dir, pattern)
        else:
            snapshot = cls._directory_snapshot(resolved_dir)
            now = cls._now()
            entry = {
                "name": name,
                "type": "file_poll",
                "func": func,
                "args": args_value,
                "kwargs": kwargs_value,
                "interval_s": None,
                "target_seconds": None,
                "next_run": None,
                "last_run": None,
                "enabled": True,
                "directory": resolved_dir,
                "pattern": pattern,
                "known_files": snapshot,
                "last_poll": now,
                "use_watchdog": False
            }
            cls._store_schedule(entry)
            cls._ensure_worker()
        return True

    @classmethod
    def has_schedule(cls, name: str) -> bool:
        with cls._lock:
            return name in cls._schedules

    @classmethod
    def list_schedules(cls) -> list:
        with cls._lock:
            out = []
            for entry in cls._schedules.values():
                out.append(cls._public_snapshot(entry))
            return out

    @classmethod
    def get_schedule(cls, name: str) -> dict:
        with cls._lock:
            entry = cls._schedules.get(name)
            if entry is None:
                return None
            return cls._public_snapshot(entry)

    @classmethod
    def update_schedule(cls, name: str, interval_s: int = None, time_of_day: str = None, enabled: bool = None, directory: str = None, pattern: str = None, args: tuple = None, kwargs: dict = None):
        with cls._lock:
            if name not in cls._schedules:
                return False
            entry = cls._schedules[name]
            now = cls._now()
            if enabled is not None:
                entry["enabled"] = bool(enabled)
            if args is not None:
                entry["args"] = tuple(args)
            if kwargs is not None:
                entry["kwargs"] = dict(kwargs)
            if entry["type"] == "interval" and interval_s is not None:
                entry["interval_s"] = cls._normalize_interval(interval_s)
                entry["next_run"] = now + entry["interval_s"]
            if entry["type"] == "daily" and time_of_day is not None:
                entry["target_seconds"] = cls._time_string_to_seconds(time_of_day)
                entry["next_run"] = cls._next_daily_run(entry["target_seconds"], now)
            if entry["type"] == "file_poll":
                if directory is not None:
                    entry["directory"] = cls._normalize_directory(directory)
                    entry["known_files"] = cls._directory_snapshot(entry["directory"])
                if pattern is not None:
                    entry["pattern"] = pattern
            if entry["type"] == "file_watchdog":
                restart_needed = False
                if directory is not None:
                    entry["directory"] = cls._normalize_directory(directory)
                    restart_needed = True
                if pattern is not None:
                    entry["pattern"] = pattern
                    restart_needed = True
                if restart_needed:
                    cls._restart_watchdog(name)
            return True

    @classmethod
    def remove_schedule(cls, name: str) -> bool:
        with cls._lock:
            entry = cls._schedules.pop(name, None)
        if entry is None:
            return False
        if entry["type"] == "file_watchdog":
            cls._stop_watchdog(name)
        cls._stop_worker_if_idle()
        return True

    @classmethod
    def stop_all(cls):
        with cls._lock:
            cls._schedules.clear()
        cls._stop_all_watchdogs()
        cls._stop_worker()

    ### PRIVATE UTILITIES START
    @classmethod
    def _store_schedule(cls, entry: dict):
        with cls._lock:
            if len(cls._schedules) >= cls.MAX_SCHEDULES:
                raise ValueError("Maximum schedules reached")
            if entry["name"] in cls._schedules:
                raise ValueError("Schedule name already exists")
            cls._schedules[entry["name"]] = entry

    @classmethod
    def _ensure_worker(cls):
        with cls._lock:
            if cls._runner_thread is not None and cls._runner_thread.is_alive():
                return
            cls._stop_event.clear()
            cls._runner_thread = threading.Thread(target=cls._run_loop, daemon=True)
            cls._runner_thread.start()

    @classmethod
    def _stop_worker_if_idle(cls):
        with cls._lock:
            active = any(entry["type"] in ("interval", "daily", "file_poll") for entry in cls._schedules.values())
        if not active:
            cls._stop_worker()

    @classmethod
    def _stop_worker(cls):
        cls._stop_event.set()
        thread = cls._runner_thread
        if thread is not None:
            thread.join(timeout=cls.TICK_INTERVAL_S * 2)
        cls._runner_thread = None

    @classmethod
    def _run_loop(cls):
        while not cls._stop_event.is_set():
            now = cls._now()
            cls._process_time_based(now)
            cls._process_file_polls(now)
            wait_time = cls._resolve_positive(cls.TICK_INTERVAL_S, cls.TICK_INTERVAL_S, cls.MIN_INTERVAL_S)
            cls._stop_event.wait(wait_time)

    @classmethod
    def _process_time_based(cls, now: float):
        to_run = []
        with cls._lock:
            for entry in cls._schedules.values():
                if not entry["enabled"]:
                    continue
                if entry["type"] == "interval" and entry["next_run"] is not None and now >= entry["next_run"]:
                    entry["last_run"] = now
                    entry["next_run"] = now + entry["interval_s"]
                    to_run.append(cls._copy_entry(entry))
                if entry["type"] == "daily" and entry["next_run"] is not None and now >= entry["next_run"]:
                    entry["last_run"] = now
                    entry["next_run"] = cls._next_daily_run(entry["target_seconds"], now)
                    to_run.append(cls._copy_entry(entry))
        for entry in to_run:
            cls._execute_entry(entry, None)

    @classmethod
    def _process_file_polls(cls, now: float):
        triggers = []
        with cls._lock:
            for entry in cls._schedules.values():
                if entry["type"] != "file_poll" or not entry["enabled"]:
                    continue
                if now - entry["last_poll"] < cls.FILE_POLL_INTERVAL_S:
                    continue
                entry["last_poll"] = now
                new_files = cls._detect_new_files(entry["directory"], entry["pattern"], entry["known_files"])
                if new_files:
                    entry["known_files"].update(new_files)
                    entry_copy = cls._copy_entry(entry)
                    entry_copy["new_files"] = list(new_files)
                    triggers.append(entry_copy)
        for entry in triggers:
            for name in entry.get("new_files", []):
                path = os.path.join(entry["directory"], name)
                cls._execute_entry(entry, path)

    @classmethod
    def _execute_entry(cls, entry: dict, file_path: str):
        def runner():
            kwargs = dict(entry.get("kwargs") or {})
            args = tuple(entry.get("args") or tuple())
            if file_path is not None:
                kwargs["file_path"] = file_path
            entry["func"](*args, **kwargs)

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()

    @classmethod
    def _copy_entry(cls, entry: dict) -> dict:
        return {
            "name": entry["name"],
            "type": entry["type"],
            "func": entry["func"],
            "args": tuple(entry.get("args") or tuple()),
            "kwargs": dict(entry.get("kwargs") or {}),
            "interval_s": entry.get("interval_s"),
            "target_seconds": entry.get("target_seconds"),
            "next_run": entry.get("next_run"),
            "last_run": entry.get("last_run"),
            "enabled": entry.get("enabled", True),
            "directory": entry.get("directory"),
            "pattern": entry.get("pattern"),
            "known_files": set(entry.get("known_files") or set()),
            "last_poll": entry.get("last_poll"),
            "use_watchdog": entry.get("use_watchdog", False)
        }

    @classmethod
    def _public_snapshot(cls, entry: dict) -> dict:
        return {
            "name": entry["name"],
            "type": entry["type"],
            "next_run": entry.get("next_run"),
            "last_run": entry.get("last_run"),
            "enabled": entry.get("enabled", True),
            "directory": entry.get("directory"),
            "pattern": entry.get("pattern"),
            "use_watchdog": entry.get("use_watchdog", False)
        }

    @classmethod
    def _normalize_interval(cls, value) -> int:
        interval = cls._resolve_positive(value, cls.MIN_INTERVAL_S, cls.MIN_INTERVAL_S)
        return interval

    @classmethod
    def _time_string_to_seconds(cls, value: str) -> int:
        if not isinstance(value, str) or not value:
            raise ValueError("time_of_day must be a non-empty string")
        parts = value.split(cls.TIME_SEPARATOR)
        if len(parts) < cls.MIN_DAILY_FIELDS or len(parts) > cls.MAX_TIME_FIELDS:
            raise ValueError("time_of_day must be in HH:MM or HH:MM:SS format")
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2]) if len(parts) == cls.MAX_TIME_FIELDS else 0
        except (TypeError, ValueError):
            raise ValueError("time_of_day components must be integers")
        if hours < 0 or hours >= cls.HOURS_IN_DAY or minutes < 0 or minutes >= cls.MINUTES_IN_HOUR or seconds < 0 or seconds >= cls.SECONDS_IN_MINUTE:
            raise ValueError("time_of_day components out of range")
        total_seconds = (hours * cls.MINUTES_IN_HOUR * cls.SECONDS_IN_MINUTE) + (minutes * cls.SECONDS_IN_MINUTE) + seconds
        return total_seconds

    @classmethod
    def _next_daily_run(cls, target_seconds: int, now: float) -> float:
        today = datetime.fromtimestamp(now)
        midnight = datetime(year=today.year, month=today.month, day=today.day)
        target_time = midnight.timestamp() + target_seconds
        if target_time <= now:
            target_time += cls.SECONDS_IN_DAY
        return target_time

    @classmethod
    def _now(cls) -> float:
        return time.time()

    @classmethod
    def _validate_callable(cls, func):
        if not callable(func):
            raise TypeError("func must be callable")

    @classmethod
    def _validate_name(cls, name: str):
        if not isinstance(name, str) or not name:
            raise ValueError("Schedule name must be a non-empty string")
        if len(name) > cls.MAX_NAME_LENGTH:
            raise ValueError("Schedule name too long")

    @classmethod
    def _resolve_positive(cls, value, default_value, minimum_value):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default_value
        if number < minimum_value:
            return minimum_value
        return number

    @classmethod
    def _normalize_directory(cls, directory: str) -> str:
        if not isinstance(directory, str) or not directory:
            raise ValueError("directory must be a non-empty string")
        path = os.path.abspath(directory)
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def _directory_snapshot(cls, directory: str) -> set:
        try:
            return set(os.listdir(directory))
        except Exception:
            return set()

    @classmethod
    def _detect_new_files(cls, directory: str, pattern: str, known_files: set) -> set:
        current = cls._directory_snapshot(directory)
        new_files = set()
        for name in current:
            if name in known_files:
                continue
            if pattern is not None and pattern not in name:
                continue
            new_files.add(name)
        return new_files

    @classmethod
    def _resolve_watchdog_flag(cls, use_watchdog):
        if use_watchdog is None:
            return cls.WATCHDOG_ENABLED
        return bool(use_watchdog)

    @classmethod
    def _watchdog_supported(cls) -> bool:
        return Observer is not None and FileSystemEventHandler is not None

    @classmethod
    def _start_watchdog(cls, name: str, directory: str, pattern: str):
        if not cls._watchdog_supported():
            return
        handler = _Schedule_FileHandler(name, directory, pattern)
        observer = Observer()
        observer.daemon = True
        observer.schedule(handler, directory, recursive=False)
        observer.start()
        with cls._lock:
            cls._watchdog_handlers[name] = observer

    @classmethod
    def _restart_watchdog(cls, name: str):
        cls._stop_watchdog(name)
        with cls._lock:
            entry = cls._schedules.get(name)
            if entry is None:
                return
            directory = entry.get("directory")
            pattern = entry.get("pattern")
        cls._start_watchdog(name, directory, pattern)

    @classmethod
    def _stop_watchdog(cls, name: str):
        with cls._lock:
            observer = cls._watchdog_handlers.pop(name, None)
        if observer is not None:
            observer.stop()
            observer.join(timeout=cls.FILE_POLL_INTERVAL_S * 2)

    @classmethod
    def _stop_all_watchdogs(cls):
        names = list(cls._watchdog_handlers.keys())
        for name in names:
            cls._stop_watchdog(name)

    @classmethod
    def _watchdog_trigger(cls, name: str, path: str):
        with cls._lock:
            entry = cls._schedules.get(name)
            if entry is None or not entry.get("enabled", True):
                return
            entry_copy = cls._copy_entry(entry)
        cls._execute_entry(entry_copy, path)

    @classmethod
    def _build_watchdog_entry(cls, name: str, func, directory: str, pattern: str, args: tuple, kwargs: dict) -> dict:
        return {
            "name": name,
            "type": "file_watchdog",
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "interval_s": None,
            "target_seconds": None,
            "next_run": None,
            "last_run": None,
            "enabled": True,
            "directory": directory,
            "pattern": pattern,
            "known_files": None,
            "last_poll": None,
            "use_watchdog": True
        }
    ### PRIVATE UTILITIES END


class _Schedule_FileHandler(FileSystemEventHandler if FileSystemEventHandler is not None else object):
    def __init__(self, schedule_name: str, directory: str, pattern: str):
        self.schedule_name = schedule_name
        self.directory = directory
        self.pattern = pattern

    def on_created(self, event):
        if getattr(event, "is_directory", False):
            return
        path = getattr(event, "src_path", None)
        if path is None:
            return
        if self.pattern is not None and self.pattern not in os.path.basename(path):
            return
        Schedule._watchdog_trigger(self.schedule_name, path)