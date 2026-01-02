import json
import time

import requests


class API:
    BYTES_IN_KB = 1024
    MILLISECONDS_IN_SECOND = 1000
    MIN_TIMEOUT_S = 1
    MIN_RESPONSE_KB = 1

    DEFAULT_TIMEOUT_S = 30
    DEFAULT_MAX_RESPONSE_KB = 512
    DEFAULT_VERIFY_SSL = True
    DEFAULT_METHOD = "GET"
    DEFAULT_BASE_URL = None
    DEFAULT_HEADERS = {}
    DEFAULT_PARAMS = {}
    DEFAULT_API_KEY_HEADER = "Authorization"
    DEFAULT_API_KEY_PREFIX = "Bearer "
    DEFAULT_API_KEY_QUERY = None

    API_KEYS = {}
    PRESETS = {}

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config.get("api_keys") or config.get("api_key", {})
        env_variables = config.get("env", {})
        api_config = None
        if "API" in config.keys():
            api_config = config["API"]
        elif "Api" in config.keys():
            api_config = config["Api"]
        cls.API_KEYS = api_keys if isinstance(api_keys, dict) else {}
        if api_config is None:
            return
        cls.DEFAULT_TIMEOUT_S = cls._resolve_timeout(api_config.get("DEFAULT_TIMEOUT_S", cls.DEFAULT_TIMEOUT_S))
        cls.DEFAULT_MAX_RESPONSE_KB = cls._resolve_max_kb(api_config.get("DEFAULT_MAX_RESPONSE_KB", cls.DEFAULT_MAX_RESPONSE_KB))
        cls.DEFAULT_VERIFY_SSL = cls._resolve_bool(api_config.get("DEFAULT_VERIFY_SSL", cls.DEFAULT_VERIFY_SSL), cls.DEFAULT_VERIFY_SSL)
        cls.DEFAULT_METHOD = cls._resolve_method(api_config.get("DEFAULT_METHOD", cls.DEFAULT_METHOD))
        cls.DEFAULT_BASE_URL = api_config.get("DEFAULT_BASE_URL", cls.DEFAULT_BASE_URL)
        cls.DEFAULT_HEADERS = cls._clone_map(api_config.get("DEFAULT_HEADERS", cls.DEFAULT_HEADERS))
        cls.DEFAULT_PARAMS = cls._clone_map(api_config.get("DEFAULT_PARAMS", cls.DEFAULT_PARAMS))
        cls.DEFAULT_API_KEY_HEADER = api_config.get("DEFAULT_API_KEY_HEADER", cls.DEFAULT_API_KEY_HEADER)
        cls.DEFAULT_API_KEY_PREFIX = api_config.get("DEFAULT_API_KEY_PREFIX", cls.DEFAULT_API_KEY_PREFIX)
        cls.DEFAULT_API_KEY_QUERY = api_config.get("DEFAULT_API_KEY_QUERY", cls.DEFAULT_API_KEY_QUERY)
        cls.PRESETS = {}
        presets_config = api_config.get("PRESETS", {})
        if isinstance(presets_config, dict):
            for name, preset in presets_config.items():
                cls._load_preset_from_config(name, preset)

    @classmethod
    def configure(cls, default_timeout_s: int = None, default_max_response_kb: int = None, default_verify_ssl: bool = None, default_method: str = None, default_base_url: str = None, default_headers: dict = None, default_params: dict = None, default_api_key_header: str = None, default_api_key_prefix: str = None, default_api_key_query: str = None, api_keys: dict = None):
        if default_timeout_s is not None:
            cls.DEFAULT_TIMEOUT_S = cls._resolve_timeout(default_timeout_s)
        if default_max_response_kb is not None:
            cls.DEFAULT_MAX_RESPONSE_KB = cls._resolve_max_kb(default_max_response_kb)
        if default_verify_ssl is not None:
            cls.DEFAULT_VERIFY_SSL = cls._resolve_bool(default_verify_ssl, cls.DEFAULT_VERIFY_SSL)
        if default_method is not None:
            cls.DEFAULT_METHOD = cls._resolve_method(default_method)
        if default_base_url is not None:
            cls.DEFAULT_BASE_URL = default_base_url
        if default_headers is not None:
            cls.DEFAULT_HEADERS = cls._clone_map(default_headers)
        if default_params is not None:
            cls.DEFAULT_PARAMS = cls._clone_map(default_params)
        if default_api_key_header is not None:
            cls.DEFAULT_API_KEY_HEADER = default_api_key_header
        if default_api_key_prefix is not None:
            cls.DEFAULT_API_KEY_PREFIX = default_api_key_prefix
        if default_api_key_query is not None:
            cls.DEFAULT_API_KEY_QUERY = default_api_key_query
        if api_keys is not None and isinstance(api_keys, dict):
            cls.API_KEYS = cls._clone_map(api_keys)

    @classmethod
    def add(cls, name: str, base_url: str = None, endpoints: dict = None, headers: dict = None, params: dict = None, api_key: str = None, api_key_name: str = None, api_key_header: str = None, api_key_prefix: str = None, api_key_query: str = None, method: str = None, timeout_s: int = None, verify_ssl: bool = None, max_response_kb: int = None):
        preset_name = cls._normalize_name(name)
        if not preset_name:
            raise ValueError("Preset name is required")
        preset = {
            "base_url": base_url if base_url is not None else cls.DEFAULT_BASE_URL,
            "endpoints": cls._clone_map(endpoints) if endpoints is not None else {},
            "headers": cls._clone_map(headers) if headers is not None else {},
            "params": cls._clone_map(params) if params is not None else {},
            "api_key": cls._resolve_api_key(api_key, api_key_name),
            "api_key_header": api_key_header if api_key_header is not None else cls.DEFAULT_API_KEY_HEADER,
            "api_key_prefix": api_key_prefix if api_key_prefix is not None else cls.DEFAULT_API_KEY_PREFIX,
            "api_key_query": api_key_query if api_key_query is not None else cls.DEFAULT_API_KEY_QUERY,
            "method": cls._resolve_method(method if method is not None else cls.DEFAULT_METHOD),
            "timeout_s": cls._resolve_timeout(timeout_s if timeout_s is not None else cls.DEFAULT_TIMEOUT_S),
            "verify_ssl": cls._resolve_bool(verify_ssl, cls.DEFAULT_VERIFY_SSL),
            "max_response_kb": cls._resolve_max_kb(max_response_kb if max_response_kb is not None else cls.DEFAULT_MAX_RESPONSE_KB),
        }
        cls.PRESETS[preset_name] = preset
        return preset_name

    @classmethod
    def remove(cls, name: str):
        preset_name = cls._normalize_name(name)
        if preset_name in cls.PRESETS:
            del cls.PRESETS[preset_name]
            return True
        return False

    @classmethod
    def list_presets(cls) -> list:
        return sorted(list(cls.PRESETS.keys()))

    @classmethod
    def call(cls, name: str, tool: str = None, path: str = None, method: str = None, params: dict = None, headers: dict = None, data=None, json_body=None, timeout_s: int = None, verify_ssl: bool = None, max_response_kb: int = None, url: str = None) -> dict:
        preset_name = cls._normalize_name(name)
        if preset_name not in cls.PRESETS:
            raise ValueError(f"Preset '{name}' not found")
        preset = cls.PRESETS[preset_name]
        resolved_method = cls._resolve_method(method if method is not None else preset["method"])
        resolved_timeout = cls._resolve_timeout(timeout_s if timeout_s is not None else preset["timeout_s"])
        resolved_verify = cls._resolve_bool(verify_ssl, preset["verify_ssl"])
        resolved_max_kb = cls._resolve_max_kb(max_response_kb if max_response_kb is not None else preset["max_response_kb"])
        max_bytes = cls._resolve_max_bytes(resolved_max_kb)

        target_url = url if url is not None else cls._build_url(preset, tool, path)
        if not target_url:
            raise ValueError("A target URL could not be resolved for this call")

        merged_headers = cls._merge_maps(cls.DEFAULT_HEADERS, preset["headers"])
        merged_params = cls._merge_maps(cls.DEFAULT_PARAMS, preset["params"])
        if headers is not None:
            merged_headers.update(cls._clone_map(headers))
        if params is not None:
            merged_params.update(cls._clone_map(params))
        cls._apply_api_key(preset, merged_headers, merged_params)

        start = cls._now()
        try:
            response = requests.request(
                method=resolved_method,
                url=target_url,
                params=merged_params if merged_params else None,
                headers=merged_headers if merged_headers else None,
                timeout=resolved_timeout,
                verify=resolved_verify,
                json=json_body,
                data=data
            )
            duration_ms = cls._duration_ms(start)
            content_bytes = response.content if response.content is not None else b""
            trimmed_bytes = cls._trim_body(content_bytes, max_bytes)
            encoding = response.encoding or "utf-8"
            body_text = cls._decode_body(trimmed_bytes, encoding)
            parsed_json = None
            content_type = response.headers.get("Content-Type", "") if response.headers else ""
            if "json" in content_type.lower():
                parsed_json = cls._parse_json(trimmed_bytes, encoding)
            return {
                "url": target_url,
                "method": resolved_method,
                "status_code": response.status_code,
                "ok": response.ok,
                "duration_ms": duration_ms,
                "headers": dict(response.headers),
                "body": body_text,
                "json": parsed_json,
            }
        except requests.exceptions.Timeout as exc:
            duration_ms = cls._duration_ms(start)
            return {
                "url": target_url,
                "method": resolved_method,
                "status_code": None,
                "ok": False,
                "duration_ms": duration_ms,
                "error": str(exc),
                "timeout": True
            }
        except requests.exceptions.RequestException as exc:
            duration_ms = cls._duration_ms(start)
            return {
                "url": target_url,
                "method": resolved_method,
                "status_code": getattr(exc.response, "status_code", None),
                "ok": False,
                "duration_ms": duration_ms,
                "error": str(exc),
                "timeout": False
            }

    ### PRIVATE UTILITIES START
    @classmethod
    def _load_preset_from_config(cls, name: str, preset_config: dict):
        api_key = None
        api_key_name = None
        if isinstance(preset_config, dict):
            api_key = preset_config.get("API_KEY")
            api_key_name = preset_config.get("API_KEY_NAME")
        cls.add(
            name=name,
            base_url=preset_config.get("BASE_URL") if isinstance(preset_config, dict) else None,
            endpoints=preset_config.get("ENDPOINTS") if isinstance(preset_config, dict) else None,
            headers=preset_config.get("HEADERS") if isinstance(preset_config, dict) else None,
            params=preset_config.get("PARAMS") if isinstance(preset_config, dict) else None,
            api_key=api_key,
            api_key_name=api_key_name,
            api_key_header=preset_config.get("API_KEY_HEADER") if isinstance(preset_config, dict) else None,
            api_key_prefix=preset_config.get("API_KEY_PREFIX") if isinstance(preset_config, dict) else None,
            api_key_query=preset_config.get("API_KEY_QUERY") if isinstance(preset_config, dict) else None,
            method=preset_config.get("METHOD") if isinstance(preset_config, dict) else None,
            timeout_s=preset_config.get("TIMEOUT_S") if isinstance(preset_config, dict) else None,
            verify_ssl=preset_config.get("VERIFY_SSL") if isinstance(preset_config, dict) else None,
            max_response_kb=preset_config.get("MAX_RESPONSE_KB") if isinstance(preset_config, dict) else None,
        )

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        if name is None:
            return None
        try:
            return str(name).strip()
        except Exception:
            return None

    @classmethod
    def _resolve_api_key(cls, api_key: str, api_key_name: str):
        if api_key is not None:
            return api_key
        if api_key_name and isinstance(cls.API_KEYS, dict):
            return cls.API_KEYS.get(api_key_name)
        return None

    @classmethod
    def _build_url(cls, preset: dict, tool: str, path: str):
        base = preset.get("base_url") or cls.DEFAULT_BASE_URL
        if path:
            return cls._join_url(base, path)
        if tool:
            endpoints = preset.get("endpoints", {})
            endpoint = endpoints.get(tool)
            if endpoint:
                return cls._join_url(base, endpoint)
        return base

    @classmethod
    def _join_url(cls, base: str, endpoint: str):
        if not base:
            return endpoint
        if endpoint is None:
            return base
        base_trimmed = base[:-1] if base.endswith("/") else base
        endpoint_trimmed = endpoint[1:] if endpoint.startswith("/") else endpoint
        return base_trimmed + "/" + endpoint_trimmed

    @classmethod
    def _merge_maps(cls, first: dict, second: dict) -> dict:
        merged = cls._clone_map(first)
        merged.update(cls._clone_map(second))
        return merged

    @classmethod
    def _clone_map(cls, value):
        if isinstance(value, dict):
            return dict(value)
        return {}

    @classmethod
    def _apply_api_key(cls, preset: dict, headers: dict, params: dict):
        key = preset.get("api_key")
        if not key:
            return
        header_name = preset.get("api_key_header")
        query_param = preset.get("api_key_query")
        prefix = preset.get("api_key_prefix") or ""
        if query_param:
            params[query_param] = key
            return
        if header_name:
            headers[header_name] = f"{prefix}{key}" if prefix else key

    @classmethod
    def _trim_body(cls, content: bytes, max_bytes: int):
        if max_bytes is None or content is None:
            return content
        if len(content) <= max_bytes:
            return content
        return content[:max_bytes]

    @classmethod
    def _decode_body(cls, content: bytes, encoding: str) -> str:
        if content is None:
            return ""
        try:
            return content.decode(encoding or "utf-8", errors="replace")
        except Exception:
            return ""

    @classmethod
    def _parse_json(cls, content: bytes, encoding: str):
        try:
            text = cls._decode_body(content, encoding)
            return json.loads(text)
        except Exception:
            return None

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
        kilobytes = cls._safe_int(value, cls.DEFAULT_MAX_RESPONSE_KB)
        if kilobytes is None:
            return None
        if kilobytes < cls.MIN_RESPONSE_KB:
            kilobytes = cls.MIN_RESPONSE_KB
        return kilobytes

    @classmethod
    def _resolve_max_bytes(cls, kilobytes):
        if kilobytes is None:
            return None
        return kilobytes * cls.BYTES_IN_KB

    @classmethod
    def _resolve_method(cls, value: str):
        if not value:
            return cls.DEFAULT_METHOD
        try:
            return str(value).upper()
        except Exception:
            return cls.DEFAULT_METHOD

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