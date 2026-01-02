import os
import subprocess
import time


class Process:
    BYTES_IN_KB = 1024
    MILLISECONDS_IN_SECOND = 1000
    MIN_TIMEOUT_S = 1
    MIN_OUTPUT_KB = 1

    DEFAULT_TIMEOUT_S = 30
    DEFAULT_MAX_OUTPUT_KB = 512
    DEFAULT_CWD = None
    DEFAULT_ENV = None
    DEFAULT_SHELL = False
    DEFAULT_ENCODING = "utf-8"
    DEFAULT_DECODE_ERRORS = "replace"
    DEFAULT_CAPTURE_OUTPUT = True
    DEFAULT_TEXT = True
    DEFAULT_CHECK = False

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Process" in config.keys():
            process_config = config["Process"]
            cls.DEFAULT_TIMEOUT_S = cls._resolve_timeout(process_config.get("DEFAULT_TIMEOUT_S", cls.DEFAULT_TIMEOUT_S))
            cls.DEFAULT_MAX_OUTPUT_KB = cls._resolve_max_kb(process_config.get("DEFAULT_MAX_OUTPUT_KB", cls.DEFAULT_MAX_OUTPUT_KB))
            cls.DEFAULT_CWD = process_config.get("DEFAULT_CWD", cls.DEFAULT_CWD)
            cls.DEFAULT_ENV = process_config.get("DEFAULT_ENV", cls.DEFAULT_ENV)
            cls.DEFAULT_SHELL = cls._resolve_bool(process_config.get("DEFAULT_SHELL", cls.DEFAULT_SHELL), cls.DEFAULT_SHELL)
            cls.DEFAULT_ENCODING = process_config.get("DEFAULT_ENCODING", cls.DEFAULT_ENCODING)
            cls.DEFAULT_DECODE_ERRORS = process_config.get("DEFAULT_DECODE_ERRORS", cls.DEFAULT_DECODE_ERRORS)
            cls.DEFAULT_CAPTURE_OUTPUT = cls._resolve_bool(process_config.get("DEFAULT_CAPTURE_OUTPUT", cls.DEFAULT_CAPTURE_OUTPUT), cls.DEFAULT_CAPTURE_OUTPUT)
            cls.DEFAULT_TEXT = cls._resolve_bool(process_config.get("DEFAULT_TEXT", cls.DEFAULT_TEXT), cls.DEFAULT_TEXT)
            cls.DEFAULT_CHECK = cls._resolve_bool(process_config.get("DEFAULT_CHECK", cls.DEFAULT_CHECK), cls.DEFAULT_CHECK)

    @classmethod
    def configure(cls, timeout_s: int = None, max_output_kb: int = None, cwd: str = None, env: dict = None, shell: bool = None, encoding: str = None, decode_errors: str = None, capture_output: bool = None, text: bool = None, check: bool = None):
        if timeout_s is not None:
            cls.DEFAULT_TIMEOUT_S = cls._resolve_timeout(timeout_s)
        if max_output_kb is not None:
            cls.DEFAULT_MAX_OUTPUT_KB = cls._resolve_max_kb(max_output_kb)
        if cwd is not None:
            cls.DEFAULT_CWD = cwd
        if env is not None:
            cls.DEFAULT_ENV = env
        if shell is not None:
            cls.DEFAULT_SHELL = cls._resolve_bool(shell, cls.DEFAULT_SHELL)
        if encoding is not None:
            cls.DEFAULT_ENCODING = encoding
        if decode_errors is not None:
            cls.DEFAULT_DECODE_ERRORS = decode_errors
        if capture_output is not None:
            cls.DEFAULT_CAPTURE_OUTPUT = cls._resolve_bool(capture_output, cls.DEFAULT_CAPTURE_OUTPUT)
        if text is not None:
            cls.DEFAULT_TEXT = cls._resolve_bool(text, cls.DEFAULT_TEXT)
        if check is not None:
            cls.DEFAULT_CHECK = cls._resolve_bool(check, cls.DEFAULT_CHECK)

    @classmethod
    def run(cls, command, cwd: str = None, timeout_s: int = None, env: dict = None, shell: bool = None, capture_output: bool = None, text: bool = None, check: bool = None, max_output_kb: int = None) -> dict:
        resolved_timeout = cls._resolve_timeout(timeout_s if timeout_s is not None else cls.DEFAULT_TIMEOUT_S)
        resolved_max_kb = cls._resolve_max_kb(max_output_kb if max_output_kb is not None else cls.DEFAULT_MAX_OUTPUT_KB)
        resolved_max_bytes = cls._resolve_max_bytes(resolved_max_kb)
        resolved_shell = cls._resolve_bool(shell, cls.DEFAULT_SHELL)
        resolved_capture = cls._resolve_bool(capture_output, cls.DEFAULT_CAPTURE_OUTPUT)
        resolved_text = cls._resolve_bool(text, cls.DEFAULT_TEXT)
        resolved_check = cls._resolve_bool(check, cls.DEFAULT_CHECK)
        resolved_cwd = cwd if cwd is not None else cls.DEFAULT_CWD
        resolved_env = cls._merge_env(env)

        start_ts = cls._now()
        try:
            completed = cls._execute(command, resolved_cwd, resolved_env, resolved_shell, resolved_timeout, resolved_capture, resolved_text, resolved_check)
            duration_ms = cls._duration_ms(start_ts)
            return {
                "stdout": cls._trim_output(completed.stdout, resolved_max_bytes, resolved_text),
                "stderr": cls._trim_output(completed.stderr, resolved_max_bytes, resolved_text),
                "return_code": completed.returncode,
                "timed_out": False,
                "duration_ms": duration_ms,
                "command": cls._represent_command(command)
            }
        except subprocess.TimeoutExpired as exc:
            duration_ms = cls._duration_ms(start_ts)
            timeout_return_code = getattr(exc, "returncode", getattr(exc, "exit_status", None))
            return {
                "stdout": cls._trim_output(exc.stdout, resolved_max_bytes, resolved_text),
                "stderr": cls._trim_output(exc.stderr, resolved_max_bytes, resolved_text),
                "return_code": timeout_return_code,
                "timed_out": True,
                "duration_ms": duration_ms,
                "command": cls._represent_command(command),
                "error": str(exc)
            }
        except subprocess.CalledProcessError as exc:
            duration_ms = cls._duration_ms(start_ts)
            return {
                "stdout": cls._trim_output(exc.stdout, resolved_max_bytes, resolved_text),
                "stderr": cls._trim_output(exc.stderr, resolved_max_bytes, resolved_text),
                "return_code": exc.returncode,
                "timed_out": False,
                "duration_ms": duration_ms,
                "command": cls._represent_command(command),
                "error": str(exc)
            }

    ### PRIVATE UTILITIES START
    @classmethod
    def _execute(cls, command, cwd, env, shell, timeout_s, capture_output, text, check):
        kwargs = {
            "cwd": cwd,
            "env": env,
            "timeout": timeout_s,
            "shell": shell,
            "capture_output": capture_output,
            "text": text,
            "check": check
        }
        if text:
            kwargs["encoding"] = cls.DEFAULT_ENCODING
            kwargs["errors"] = cls.DEFAULT_DECODE_ERRORS
        return subprocess.run(command, **kwargs)

    @classmethod
    def _resolve_timeout(cls, value):
        seconds = cls._safe_int(value, cls.DEFAULT_TIMEOUT_S)
        if seconds is None:
            return None
        if seconds < cls.MIN_TIMEOUT_S:
            seconds = cls.MIN_TIMEOUT_S
        return seconds

    @classmethod
    def _resolve_max_kb(cls, value):
        kilobytes = cls._safe_int(value, cls.DEFAULT_MAX_OUTPUT_KB)
        if kilobytes is None:
            return None
        if kilobytes < cls.MIN_OUTPUT_KB:
            kilobytes = cls.MIN_OUTPUT_KB
        return kilobytes

    @classmethod
    def _resolve_max_bytes(cls, kilobytes):
        if kilobytes is None:
            return None
        return kilobytes * cls.BYTES_IN_KB

    @classmethod
    def _merge_env(cls, overrides: dict):
        if cls.DEFAULT_ENV is None and overrides is None:
            return None
        merged = dict(os.environ)
        if cls.DEFAULT_ENV is not None:
            try:
                merged.update(cls.DEFAULT_ENV)
            except Exception:
                pass
        if overrides is not None:
            try:
                merged.update(overrides)
            except Exception:
                pass
        return merged

    @classmethod
    def _trim_output(cls, data, max_bytes: int, is_text: bool):
        if max_bytes is None or data is None:
            return data
        raw = None
        if isinstance(data, str):
            try:
                raw = data.encode(cls.DEFAULT_ENCODING, errors=cls.DEFAULT_DECODE_ERRORS)
            except Exception:
                raw = None
        else:
            try:
                raw = bytes(data)
            except Exception:
                raw = None
        if raw is None:
            return data
        if len(raw) <= max_bytes:
            return data
        trimmed = raw[-max_bytes:]
        if is_text:
            try:
                return trimmed.decode(cls.DEFAULT_ENCODING, errors=cls.DEFAULT_DECODE_ERRORS)
            except Exception:
                return data
        return trimmed

    @classmethod
    def _represent_command(cls, command):
        if isinstance(command, (list, tuple)):
            try:
                return [str(part) for part in command]
            except Exception:
                return None
        try:
            return str(command)
        except Exception:
            return None

    @classmethod
    def _resolve_bool(cls, value, default_value: bool):
        if isinstance(value, bool):
            return value
        if value is None:
            return default_value
        return bool(value)

    @classmethod
    def _safe_int(cls, value, default_value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default_value

    @classmethod
    def _duration_ms(cls, start_ts: float) -> float:
        return (cls._now() - start_ts) * cls.MILLISECONDS_IN_SECOND

    @classmethod
    def _now(cls) -> float:
        return time.time()
    ### PRIVATE UTILITIES END