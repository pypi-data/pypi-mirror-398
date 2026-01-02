import ast
import io
import os
import re
import time
import inspect
from contextlib import redirect_stdout

from sylriekit.SharedStore import SharedStore


class InlinePython:
    START_TOKEN = "<?py"
    END_TOKEN = "?>"
    HTML_TAG_PATTERN = r"<python(\s+[^>]*)?\s*>(.*?)</python>"

    PRESERVE_NAMESPACE = True
    DEFAULT_CACHE_TTL = 600
    DEFAULT_RATE_LIMIT_WINDOW = 5
    _ARG_HANDLERS = []
    DEFAULT_PARAMS = []
    _CACHE_FUNCTIONS = []
    _ATTR_HANDLERS = {}
    GLOBAL = {}
    INJECT_CACHED_FUNCTIONS = True
    JS_BRIDGE_ENABLED = True
    JS_BRIDGE_ENDPOINT = "/api/cache"
    BASE_DIR = None

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "InlinePython" in config.keys():
            tool_config = config["InlinePython"]
            cls.START_TOKEN = tool_config.get("START_TOKEN", cls.START_TOKEN)
            cls.END_TOKEN = tool_config.get("END_TOKEN", cls.END_TOKEN)
            cls.HTML_TAG_PATTERN = tool_config.get("HTML_TAG_PATTERN", cls.HTML_TAG_PATTERN)
            cls.PRESERVE_NAMESPACE = tool_config.get("PRESERVE_NAMESPACE", cls.PRESERVE_NAMESPACE)
            cls.DEFAULT_CACHE_TTL = tool_config.get("DEFAULT_CACHE_TTL", cls.DEFAULT_CACHE_TTL)
            cls.DEFAULT_RATE_LIMIT_WINDOW = tool_config.get("DEFAULT_RATE_LIMIT_WINDOW", cls.DEFAULT_RATE_LIMIT_WINDOW)
            cls.INJECT_CACHED_FUNCTIONS = tool_config.get("INJECT_CACHED_FUNCTIONS", cls.INJECT_CACHED_FUNCTIONS)
            default_params = tool_config.get("DEFAULT_PARAMS", None)
            if default_params is not None:
                if not isinstance(default_params, dict):
                    raise ValueError("InlinePython DEFAULT_PARAMS must be a dict")
                cls.DEFAULT_PARAMS = []
                cls.set_default_params(default_params)

    @classmethod
    def render(cls, text: str):
        if not isinstance(text, str):
            raise ValueError("Text must be a string")

        namespace = {}
        pattern = re.compile(re.escape(cls.START_TOKEN) + r"(.*?)" + re.escape(cls.END_TOKEN), re.DOTALL)

        rendered_parts = []
        last_end = 0

        for match in pattern.finditer(text):
            start, end = match.span()
            rendered_parts.append(text[last_end:start])

            code_block = match.group(1)
            inline_params, code = cls._parse_block(code_block)
            params = cls._merge_params(inline_params)

            code = cls._apply_arg_handlers(code, params)

            output, namespace = cls._run_block(code, namespace, params)
            if params.get("no_output", False):
                rendered_parts.append("")
            else:
                rendered_parts.append(output)

            last_end = end

        rendered_parts.append(text[last_end:])

        return "".join(rendered_parts)

    @classmethod
    def args(cls, key: str):
        def decorator(func):
            cls._register_arg_handler(key, func)
            return func

        return decorator

    @classmethod
    def set_default_params(cls, default: dict):
        if not isinstance(default, dict):
            raise ValueError("Default params must be a dict")
        for key, value in default.items():
            cls.DEFAULT_PARAMS.append((key, value))

    @classmethod
    def tag(cls, attr_name: str):
        def decorator(func):
            cls._register_attr_handler(attr_name, func)
            return func

        return decorator

    @classmethod
    def render_html(cls, text: str, session_token: str = None, base_dir: str = None) -> str:
        if not isinstance(text, str):
            raise ValueError("Text must be a string")

        namespace = {}

        if base_dir is None:
            base_dir = cls.BASE_DIR or os.getcwd()

        pattern = re.compile(cls.HTML_TAG_PATTERN, re.DOTALL)

        rendered_parts = []
        last_end = 0

        for match in pattern.finditer(text):
            start, end = match.span()
            rendered_parts.append(text[last_end:start])

            attrs_text = match.group(1) or ""
            inline_code = match.group(2)

            params = cls._parse_html_attrs(attrs_text)
            params = cls._merge_params(params)

            code_block = ""
            src = params.pop("src", None)
            if src:
                src_path = src if os.path.isabs(src) else os.path.join(base_dir, src)
                if os.path.isfile(src_path):
                    with open(src_path, "r", encoding="utf-8") as f:
                        code_block = f.read()
                else:
                    rendered_parts.append(f"<!-- Python src file not found: {src} -->")

            if inline_code and inline_code.strip():
                if code_block:
                    code_block += "\n" + inline_code
                else:
                    code_block = inline_code

            if not code_block.strip():
                last_end = end
                continue

            req_data = params.get("req-data")
            if req_data:
                try:
                    from sylriekit.Website import Website
                    from flask import request, g
                    session_id = None
                    if hasattr(g, "pending_cookies") and "SessionID" in g.pending_cookies:
                        session_id = g.pending_cookies["SessionID"]
                    else:
                        session_id = request.cookies.get("SessionID")
                    if session_id:
                        data_value = Website.get_session_data(req_data, session_id)
                        if data_value is not True:
                            last_end = end
                            continue
                    else:
                        last_end = end
                        continue
                except Exception:
                    last_end = end
                    continue

            function_entries = cls._extract_functions_with_metadata(code_block, params)
            function_entries = cls._apply_attr_handlers(function_entries, params)
            for entry in function_entries:
                cls._add_or_update_cache(entry)

            code_block = cls._apply_arg_handlers(code_block, params)

            output, namespace = cls._run_block(code_block, namespace, params)
            if params.get("no_output", False):
                rendered_parts.append("")
            else:
                rendered_parts.append(output)

            last_end = end

        rendered_parts.append(text[last_end:])

        result = "".join(rendered_parts)

        if cls.JS_BRIDGE_ENABLED and session_token:
            bridge_script = cls._generate_js_bridge(session_token)
            if "</body>" in result.lower():
                result = result.replace("</body>", f"{bridge_script}\n</body>", 1)
                result = result.replace("</BODY>", f"{bridge_script}\n</BODY>", 1)
            elif "</html>" in result.lower():
                result = result.replace("</html>", f"{bridge_script}\n</html>", 1)
                result = result.replace("</HTML>", f"{bridge_script}\n</HTML>", 1)
            else:
                result += f"\n{bridge_script}"

        return result

    @classmethod
    def get_cache_functions(cls) -> list:
        if SharedStore.is_connected():
            names = SharedStore.list_cached_functions()
            result = []
            for name in names:
                cached = SharedStore.get_cached_function(name)
                if cached:
                    result.append({
                        "name": cached["name"],
                        "code": cached["code"],
                        "data": cached["data"],
                        "expire": cached["cached_at"] + cls.DEFAULT_CACHE_TTL,
                        "ttl": cls.DEFAULT_CACHE_TTL
                    })
            return result
        return cls._CACHE_FUNCTIONS.copy()

    @classmethod
    def get_valid_cache_functions(cls, check_req_data: bool = True) -> list:
        current_time = time.time()

        if SharedStore.is_connected():
            names = SharedStore.list_cached_functions()
            valid = []
            for name in names:
                cached = SharedStore.get_cached_function(name)
                if cached:
                    entry = {
                        "name": cached["name"],
                        "code": cached["code"],
                        "data": cached["data"],
                        "expire": cached["cached_at"] + cls.DEFAULT_CACHE_TTL,
                        "ttl": cls.DEFAULT_CACHE_TTL
                    }
                    if entry["expire"] > current_time:
                        valid.append(entry)
        else:
            valid = [entry for entry in cls._CACHE_FUNCTIONS if entry["expire"] > current_time]

        if not check_req_data:
            return valid

        filtered = []
        for entry in valid:
            req_data = entry.get("data", {}).get("req-data")
            if req_data:
                try:
                    from sylriekit.Website import Website
                    from flask import request, g
                    session_id = None
                    if hasattr(g, "pending_cookies") and "SessionID" in g.pending_cookies:
                        session_id = g.pending_cookies["SessionID"]
                    else:
                        session_id = request.cookies.get("SessionID")
                    if session_id:
                        data_value = Website.get_session_data(req_data, session_id)
                        if data_value is True:
                            filtered.append(entry)
                except Exception:
                    pass
            else:
                filtered.append(entry)

        return filtered

    @classmethod
    def clear_cache(cls) -> None:
        if SharedStore.is_connected():
            for name in SharedStore.list_cached_functions():
                SharedStore._redis.delete(SharedStore._key("func", name))
        cls._CACHE_FUNCTIONS = []

    @classmethod
    def clear_expired_cache(cls) -> None:
        current_time = time.time()
        if SharedStore.is_connected():
            for name in SharedStore.list_cached_functions():
                cached = SharedStore.get_cached_function(name)
                if cached and cached["cached_at"] + cls.DEFAULT_CACHE_TTL <= current_time:
                    SharedStore._redis.delete(SharedStore._key("func", name))
        cls._CACHE_FUNCTIONS = [entry for entry in cls._CACHE_FUNCTIONS if entry["expire"] > current_time]

    @classmethod
    def hit_cache(cls, function_name: str, function_args: dict = None):
        cls._clean_cache()
        cls._clean_rate_limit_tracker()
        if function_args is None:
            function_args = {}

        entry = None
        if SharedStore.is_connected():
            cached = SharedStore.get_cached_function(function_name)
            if cached:
                entry = {
                    "name": cached["name"],
                    "code": cached["code"],
                    "data": cached["data"],
                    "expire": cached["cached_at"] + cls.DEFAULT_CACHE_TTL,
                    "ttl": cls.DEFAULT_CACHE_TTL
                }
                if entry["expire"] <= time.time():
                    entry = None

        if entry is None:
            for local_entry in cls._CACHE_FUNCTIONS:
                if local_entry["name"] == function_name:
                    entry = local_entry
                    break

        if entry is None:
            return {"error": True, "message": f"Function '{function_name}' not found in cache"}

        if entry.get("error", False):
            cls._remove_from_cache(function_name)
            return {"error": True, "message": "Function has error flag set"}
        code = entry.get("code", "")
        if not code:
            cls._remove_from_cache(function_name)
            return {"error": True, "message": "Function code is empty"}

        req_data = entry.get("data", {}).get("req-data")
        if req_data:
            try:
                from sylriekit.Website import Website
                from flask import request, g
                session_id = None
                if hasattr(g, "pending_cookies") and "SessionID" in g.pending_cookies:
                    session_id = g.pending_cookies["SessionID"]
                else:
                    session_id = request.cookies.get("SessionID")
                if session_id:
                    data_value = Website.get_session_data(req_data, session_id)
                    if data_value is not True:
                        return {"error": True, "message": f"Function '{function_name}' not found in cache"}
                else:
                    return {"error": True, "message": f"Function '{function_name}' not found in cache"}
            except Exception:
                return {"error": True, "message": f"Function '{function_name}' not found in cache"}

        max_calls = entry.get("data", {}).get("max-calls")
        if max_calls is not None:
            if cls._is_rate_limited(function_name, max_calls):
                return {"error": True, "message": f"Rate limit exceeded for '{function_name}'",
                        "rate_limited": True}
        try:
            namespace = {}
            exec(code, namespace, namespace)
            func = namespace.get(function_name)
            if func is None:
                cls._remove_from_cache(function_name)
                return {"error": True, "message": f"Function '{function_name}' not found in executed code"}
            if not callable(func):
                cls._remove_from_cache(function_name)
                return {"error": True, "message": f"'{function_name}' is not callable"}
            if max_calls is not None:
                cls._record_call(function_name)

            sig = inspect.signature(func)
            call_args = function_args.copy()

            if "Website" in sig.parameters:
                try:
                    from sylriekit.Website import Website
                    call_args["Website"] = Website
                except Exception:
                    pass

            if "SessionID" in sig.parameters:
                try:
                    from flask import request
                    call_args["SessionID"] = request.cookies.get("SessionID")
                except Exception:
                    call_args["SessionID"] = None

            result = func(**call_args)
            ttl = entry.get("ttl", cls.DEFAULT_CACHE_TTL)
            if SharedStore.is_connected():
                SharedStore.cache_function(function_name, code, entry.get("data", {}), ttl)
            entry["expire"] = time.time() + ttl
            return {"error": False, "result": result, "data": entry.get("data", {})}
        except Exception as error:
            return {"error": True, "message": str(error)}

    @classmethod
    def get_cached_callable(cls, function_name: str):
        def wrapper(**kwargs):
            result = cls.hit_cache(function_name, kwargs)
            if result.get("error"):
                raise RuntimeError(result.get("message", "Cache hit failed"))
            return result.get("result")

        wrapper.__name__ = function_name
        wrapper.__doc__ = f"Cached function wrapper for '{function_name}'"
        return wrapper

    @classmethod
    def inject_cached_into_namespace(cls, namespace: dict) -> dict:
        cls._clean_cache()

        if SharedStore.is_connected():
            for name in SharedStore.list_cached_functions():
                cached = SharedStore.get_cached_function(name)
                if cached and cached["code"]:
                    namespace[name] = cls.get_cached_callable(name)

        for entry in cls._CACHE_FUNCTIONS:
            func_name = entry.get("name")
            if func_name and not entry.get("error", False):
                namespace[func_name] = cls.get_cached_callable(func_name)
        return namespace

    ### PRIVATE UTILITIES START
    @classmethod
    def _generate_js_bridge(cls, session_token: str) -> str:
        cls._clean_cache()

        functions = []

        if SharedStore.is_connected():
            for name in SharedStore.list_cached_functions():
                cached = SharedStore.get_cached_function(name)
                if cached and cached["code"]:
                    functions.append({
                        "name": cached["name"],
                        "data": cached["data"]
                    })

        for entry in cls._CACHE_FUNCTIONS:
            if entry.get("error"):
                continue
            func_name = entry.get("name")
            func_data = entry.get("data", {})
            if func_name and not any(f["name"] == func_name for f in functions):
                functions.append({
                    "name": func_name,
                    "data": func_data
                })

        js_functions = []
        for func in functions:
            name = func["name"]
            js_functions.append(f'''
    window.{name} = async function(...args) {{
        const argNames = __pyfunc_args["{name}"] || [];
        const kwargs = {{}};

        if (args.length === 1 && typeof args[0] === 'object' && !Array.isArray(args[0]) && args[0] !== null) {{
            Object.assign(kwargs, args[0]);
        }} else {{
            args.forEach((arg, i) => {{
                if (i < argNames.length) {{
                    kwargs[argNames[i]] = arg;
                }} else {{
                    kwargs[`arg${{i}}`] = arg;
                }}
            }});
        }}

        const response = await fetch(`${{__pybridge_endpoint}}/{name}`, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Session-Token': __pybridge_token
            }},
            body: JSON.stringify(kwargs)
        }});

        const data = await response.json();

        if (data.error) {{
            if (data.rate_limited) {{
                throw new Error(`Rate limit exceeded for {name}`);
            }}
            throw new Error(data.message || 'Function call failed');
        }}

        return data.result;
    }};''')

        arg_names_js = cls._extract_js_arg_names()

        bridge_script = f'''<script>
(function() {{
    "use strict";

    const __pybridge_token = "{session_token}";
    const __pybridge_endpoint = "{cls.JS_BRIDGE_ENDPOINT}";
    const __pyfunc_args = {arg_names_js};

    {"".join(js_functions)}

    window.__pycall = async function(funcName, kwargs) {{
        const response = await fetch(`${{__pybridge_endpoint}}/${{funcName}}`, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Session-Token': __pybridge_token
            }},
            body: JSON.stringify(kwargs || {{}})
        }});
        const data = await response.json();
        if (data.error) throw new Error(data.message);
        return data.result;
    }};

    window.__pylist = async function() {{
        const response = await fetch(__pybridge_endpoint, {{
            headers: {{ 'X-Session-Token': __pybridge_token }}
        }});
        return await response.json();
    }};

    console.log('[SylrieKit] Python bridge initialized with functions:', {[f["name"] for f in functions]});
}})();
</script>'''

        return bridge_script

    @classmethod
    def _extract_js_arg_names(cls) -> str:
        import json

        auto_injected = {"Website", "SessionID"}

        arg_map = {}

        def extract_args(func_name, code):
            if not func_name or not code:
                return
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                        args = []
                        for arg in node.args.args:
                            if arg.arg != 'self' and arg.arg not in auto_injected:
                                args.append(arg.arg)
                        arg_map[func_name] = args
                        break
            except:
                pass

        if SharedStore.is_connected():
            for name in SharedStore.list_cached_functions():
                cached = SharedStore.get_cached_function(name)
                if cached and cached["code"]:
                    extract_args(cached["name"], cached["code"])

        for entry in cls._CACHE_FUNCTIONS:
            if entry.get("error"):
                continue
            func_name = entry.get("name")
            if func_name not in arg_map:
                extract_args(func_name, entry.get("code", ""))

        return json.dumps(arg_map)

    @classmethod
    def _parse_block(cls, code_block: str) -> tuple[dict, str]:
        stripped = code_block.lstrip()
        if stripped.startswith("("):
            closing_index = cls._find_matching_parenthesis(stripped)
            if closing_index is None:
                raise ValueError("Invalid InlinePython parameters: missing closing parenthesis")
            params_text = stripped[1:closing_index].strip()
            code = stripped[closing_index + 1:].strip()
            params = cls._parse_params(params_text) if params_text else {}
            return params, code
        return {}, stripped.strip()

    @classmethod
    def _find_matching_parenthesis(cls, text: str) -> int | None:
        depth = 0
        in_string = False
        string_char = ""
        escaped = False
        for index, char in enumerate(text):
            if escaped:
                escaped = False
                continue
            if in_string:
                if char == "\\":
                    escaped = True
                    continue
                if char == string_char:
                    in_string = False
                continue
            if char in ("'", '"'):
                in_string = True
                string_char = char
                continue
            if char == "(":
                depth += 1
                continue
            if char == ")":
                depth -= 1
                if depth == 0:
                    return index
        return None

    @classmethod
    def _apply_arg_handlers(cls, code: str, params: dict) -> str:
        updated_code = code
        handler_map = {}
        for handler_key, handler in cls._ARG_HANDLERS:
            if handler_key not in handler_map:
                handler_map[handler_key] = handler
        for param_key, param_value in params.items():
            if param_key not in handler_map:
                continue
            updated_code = cls._run_arg_handler(handler_map[param_key], param_value, updated_code)
        return updated_code

    @classmethod
    def _run_arg_handler(cls, handler, value, code: str) -> str:
        result = handler(value, code)
        if not isinstance(result, str):
            raise ValueError("InlinePython arg handler must return a string")
        return result

    @classmethod
    def _run_block(cls, code: str, namespace: dict, params: dict) -> tuple[str, dict]:
        current_namespace = namespace if cls.PRESERVE_NAMESPACE else {}
        current_namespace["PARAMS"] = params
        current_namespace["GLOBAL"] = cls.GLOBAL

        current_namespace["call_cached"] = cls._create_call_cached_helper()
        current_namespace["hit_cache"] = cls.hit_cache
        current_namespace["get_cached"] = cls.get_cached_callable

        if cls.INJECT_CACHED_FUNCTIONS or params.get("inject_cached", False):
            cls.inject_cached_into_namespace(current_namespace)

        buffer = io.StringIO()
        try:
            with redirect_stdout(buffer):
                exec(code, current_namespace, current_namespace)
        except Exception as error:
            raise RuntimeError(f"InlinePython execution failed: {error}") from error
        return buffer.getvalue(), current_namespace

    @classmethod
    def _create_call_cached_helper(cls):
        def call_cached(function_name: str, **kwargs):
            result = cls.hit_cache(function_name, kwargs)
            if result.get("error"):
                raise RuntimeError(result.get("message", f"Failed to call cached function '{function_name}'"))
            return result.get("result")

        return call_cached

    @classmethod
    def _register_arg_handler(cls, key: str, handler) -> None:
        if not isinstance(key, str):
            raise ValueError("InlinePython arg handler key must be a string")
        if not callable(handler):
            raise ValueError("InlinePython arg handler must be callable")
        cls._ARG_HANDLERS.append((key, handler))

    @classmethod
    def _merge_params(cls, inline_params: dict) -> dict:
        merged = {}
        for key, value in cls.DEFAULT_PARAMS:
            if key not in merged:
                merged[key] = value
        for key, value in inline_params.items():
            if key in merged:
                continue
            merged[key] = value
        return merged

    @classmethod
    def _parse_params(cls, params_text: str) -> dict:
        if not params_text.strip():
            return {}
        try:
            expression = ast.parse(f"_f({params_text})", mode="eval")
        except SyntaxError as error:
            raise ValueError(f"Invalid InlinePython parameters: {error.msg}") from error
        if not isinstance(expression.body, ast.Call):
            raise ValueError("Invalid InlinePython parameters")
        call = expression.body
        if call.args:
            raise ValueError("InlinePython parameters must be keyword-only")
        params = {}
        for keyword in call.keywords:
            if keyword.arg is None:
                raise ValueError("InlinePython parameters do not support **expansion")
            params[keyword.arg] = cls._literal_value(keyword.value)
        return params

    @classmethod
    def _literal_value(cls, node: ast.AST):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            name = node.id.lower()
            if name == "true":
                return True
            if name == "false":
                return False
            if name == "null":
                return None
            raise ValueError(f"Unsupported name '{node.id}' in parameters")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            value = cls._literal_value(node.operand)
            if not isinstance(value, (int, float, complex)):
                raise ValueError("Unary minus only supported for numeric values")
            return -value
        if isinstance(node, ast.Dict):
            keys = [cls._literal_value(k) for k in node.keys]
            values = [cls._literal_value(v) for v in node.values]
            return dict(zip(keys, values))
        if isinstance(node, ast.List):
            return [cls._literal_value(elem) for elem in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(cls._literal_value(elem) for elem in node.elts)
        raise ValueError("Unsupported parameter value")

    @classmethod
    def _parse_html_attrs(cls, attrs_text: str) -> dict:
        if not attrs_text or not attrs_text.strip():
            return {}
        params = {}
        pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))')
        for match in pattern.finditer(attrs_text):
            key = match.group(1)
            value = match.group(2) or match.group(3) or match.group(4)
            params[key] = cls._convert_html_attr_value(value)
        standalone_pattern = re.compile(r'(?<!\=)\b([a-zA-Z_][a-zA-Z0-9_-]*)(?!\s*=)(?=\s|$)')
        for match in standalone_pattern.finditer(attrs_text):
            key = match.group(1)
            if key not in params:
                params[key] = True
        return params

    @classmethod
    def _convert_html_attr_value(cls, value: str):
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() in ("null", "none"):
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    @classmethod
    def _extract_functions_with_metadata(cls, code: str, params: dict) -> list:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        lines = code.splitlines(keepends=True)
        ttl = params.get("cache-ttl", cls.DEFAULT_CACHE_TTL)
        expire_time = time.time() + ttl
        data = {k: v for k, v in params.items() if k != "cache-ttl" and k != "no_output"}
        entries = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno - 1
                end_line = node.end_lineno
                node_lines = lines[start_line:end_line]
                function_code = "".join(node_lines)
                entries.append({
                    "name": node.name,
                    "expire": expire_time,
                    "ttl": ttl,
                    "data": data,
                    "code": function_code
                })
        return entries

    @classmethod
    def _register_attr_handler(cls, attr_name: str, handler) -> None:
        if not isinstance(attr_name, str):
            raise ValueError("InlinePython attribute name must be a string")
        if not callable(handler):
            raise ValueError("InlinePython attribute handler must be callable")
        cls._ATTR_HANDLERS[attr_name] = handler

    @classmethod
    def _apply_attr_handlers(cls, function_entries: list, params: dict) -> list:
        result = function_entries
        for attr_name, attr_value in params.items():
            if attr_name not in cls._ATTR_HANDLERS:
                continue
            handler = cls._ATTR_HANDLERS[attr_name]
            try:
                result = handler(result, attr_value, params, cls.GLOBAL)
                if not isinstance(result, list):
                    raise ValueError("InlinePython attribute handler must return a list")
            except Exception as error:
                raise RuntimeError(f"InlinePython attribute handler '{attr_name}' failed: {error}") from error
        for entry in result:
            if entry.get("code", "") == "" or entry.get("code") is None:
                entry["error"] = True
        return result

    @classmethod
    def _add_or_update_cache(cls, entry: dict) -> None:
        function_name = entry.get("name")
        ttl = entry.get("ttl", cls.DEFAULT_CACHE_TTL)

        if SharedStore.is_connected():
            SharedStore.cache_function(
                function_name,
                entry.get("code", ""),
                entry.get("data", {}),
                ttl
            )

        for index, existing in enumerate(cls._CACHE_FUNCTIONS):
            if existing.get("name") == function_name:
                cls._CACHE_FUNCTIONS[index]["expire"] = entry.get("expire")
                return
        cls._CACHE_FUNCTIONS.append(entry)

    @classmethod
    def _clean_cache(cls) -> None:
        current_time = time.time()
        cls._CACHE_FUNCTIONS = [
            entry for entry in cls._CACHE_FUNCTIONS
            if entry.get("expire", 0) > current_time
               and entry.get("code", "") != ""
               and entry.get("code") is not None
               and not entry.get("error", False)
        ]

    @classmethod
    def _remove_from_cache(cls, function_name: str) -> None:
        if SharedStore.is_connected():
            SharedStore._redis.delete(SharedStore._key("func", function_name))

        cls._CACHE_FUNCTIONS = [
            entry for entry in cls._CACHE_FUNCTIONS
            if entry.get("name") != function_name
        ]

    @classmethod
    def _clean_rate_limit_tracker(cls) -> None:
        pass

    @classmethod
    def _is_rate_limited(cls, function_name: str, max_calls: int) -> bool:
        return SharedStore.is_rate_limited(function_name, max_calls, cls.DEFAULT_RATE_LIMIT_WINDOW)

    @classmethod
    def _record_call(cls, function_name: str) -> None:
        SharedStore.record_call(function_name, cls.DEFAULT_RATE_LIMIT_WINDOW)
    ### PRIVATE UTILITIES END

