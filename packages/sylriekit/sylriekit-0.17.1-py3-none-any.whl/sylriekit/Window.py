import ast
import inspect
import os
import re
import threading
import types
from typing import Callable, Optional

from webviewpy import Webview


class Window:
    HINT_NONE = 0
    HINT_MIN = 1
    HINT_MAX = 2
    HINT_FIXED = 3

    DEFAULT_INDEX = "index.html"
    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 600
    DEFAULT_TITLE = "Window"
    DEFAULT_DEBUG = False
    DEFAULT_SYNTAX = r"!python\.(\w+)\((.*?)\);"

    _WEBVIEW = None
    _BINDINGS = {}
    _RUNNING = False
    _THREAD = None
    _LOADED_HTML = None

    @classmethod
    def load_config(cls, config: dict):
        if "Window" in config.keys():
            window_config = config["Window"]
            cls.DEFAULT_INDEX = window_config.get("DEFAULT_INDEX", cls.DEFAULT_INDEX)
            cls.DEFAULT_WIDTH = window_config.get("DEFAULT_WIDTH", cls.DEFAULT_WIDTH)
            cls.DEFAULT_HEIGHT = window_config.get("DEFAULT_HEIGHT", cls.DEFAULT_HEIGHT)
            cls.DEFAULT_TITLE = window_config.get("DEFAULT_TITLE", cls.DEFAULT_TITLE)
            cls.DEFAULT_DEBUG = window_config.get("DEFAULT_DEBUG", cls.DEFAULT_DEBUG)
            cls.DEFAULT_SYNTAX = window_config.get("DEFAULT_SYNTAX", cls.DEFAULT_SYNTAX)

    @classmethod
    def load(cls, index: Optional[str] = None) -> bool:
        index = index or cls.DEFAULT_INDEX
        if not os.path.isabs(index):
            caller_frame = inspect.stack()[1]
            caller_dir = os.path.dirname(os.path.abspath(caller_frame.filename))
            index = os.path.join(caller_dir, index)
        if not os.path.isfile(index):
            raise FileNotFoundError(f"Index file not found: {index}")
        base_dir = os.path.dirname(os.path.abspath(index))
        html = cls._load_html_with_assets(index)
        html = cls._process_python_tags(html, base_dir)
        html = cls._process_python_calls(html)
        cls._WEBVIEW = Webview(debug=cls.DEFAULT_DEBUG)
        cls._WEBVIEW.set_title(cls.DEFAULT_TITLE)
        cls._WEBVIEW.set_size(cls.DEFAULT_WIDTH, cls.DEFAULT_HEIGHT, cls.HINT_NONE)
        for name, func in cls._BINDINGS.items():
            cls._WEBVIEW.bind(name, func)
        cls._WEBVIEW.set_html(html)
        cls._LOADED_HTML = html
        return True

    @classmethod
    def javascript(cls):
        def decorator(func: Callable) -> Callable:
            cls._BINDINGS[func.__name__] = func
            return func
        return decorator

    @classmethod
    def open(cls, threaded: bool = False) -> bool:
        if cls._WEBVIEW is None:
            raise RuntimeError("No window loaded. Call load() first.")
        if threaded:
            def run_thread():
                cls._RUNNING = True
                cls._WEBVIEW.run()
                cls._RUNNING = False
            cls._THREAD = threading.Thread(target=run_thread, daemon=True)
            cls._THREAD.start()
        else:
            cls._RUNNING = True
            cls._WEBVIEW.run()
            cls._RUNNING = False
        return True

    @classmethod
    def close(cls, window_id: int = 0) -> bool:
        if cls._WEBVIEW is None:
            return False
        cls._WEBVIEW.terminate()
        cls._RUNNING = False
        return True

    @classmethod
    def python_api_syntax(cls, syntax: str) -> bool:
        cls.DEFAULT_SYNTAX = syntax
        return True

    @classmethod
    def bind(cls, name: str, func: Callable) -> bool:
        cls._BINDINGS[name] = func
        if cls._WEBVIEW is not None:
            cls._WEBVIEW.bind(name, func)
        return True

    ### PRIVATE UTILITIES START
    @classmethod
    def _process_python_calls(cls, html: str) -> str:
        html = cls._process_js_declarations(html)
        html = cls._process_html_replacements(html)
        return html

    @classmethod
    def _process_python_tags(cls, html: str, base_dir: str) -> str:
        pattern = r'<python(?:\s+src=["\']([^"\']+)["\'])?\s*>(.*?)</python>'

        def process_tag(match):
            src = match.group(1)
            inline_code = match.group(2).strip()
            if src:
                if not os.path.isabs(src):
                    src = os.path.join(base_dir, src)
                if os.path.isfile(src):
                    with open(src, 'r', encoding='utf-8') as f:
                        code = f.read()
                    cls._execute_python_definitions(code)
            if inline_code:
                cls._execute_python_definitions(inline_code)
            return ''
        return re.sub(pattern, process_tag, html, flags=re.DOTALL | re.IGNORECASE)

    @classmethod
    def _execute_python_definitions(cls, code: str) -> None:
        namespace = {'Window': cls}
        exec(code, namespace)
        for name, obj in namespace.items():
            if name.startswith('_'):
                continue
            if name in ('Window',):
                continue
            if isinstance(obj, types.ModuleType):
                continue
            if isinstance(obj, type):
                continue
            if callable(obj):
                cls._BINDINGS[name] = obj

    @classmethod
    def _process_js_declarations(cls, html: str) -> str:
        script_pattern = r'(<script[^>]*>)(.*?)(</script>)'

        def process_script(match):
            open_tag = match.group(1)
            content = match.group(2)
            close_tag = match.group(3)
            content = re.sub(cls.DEFAULT_SYNTAX, '', content)
            return f'{open_tag}{content}{close_tag}'
        return re.sub(script_pattern, process_script, html, flags=re.DOTALL)

    @classmethod
    def _process_html_replacements(cls, html: str) -> str:
        def is_in_script(match, text):
            pos = match.start()
            before = text[:pos]
            open_scripts = len(re.findall(r'<script[^>]*>', before))
            close_scripts = len(re.findall(r'</script>', before))
            return open_scripts > close_scripts

        def replacer(match):
            if is_in_script(match, html):
                return match.group(0)
            func_name = match.group(1)
            args_str = match.group(2).strip()
            if func_name not in cls._BINDINGS:
                return match.group(0)
            try:
                if args_str:
                    args = ast.literal_eval(f"({args_str},)")
                else:
                    args = ()
                result = cls._BINDINGS[func_name](*args)
                return str(result) if result is not None else ""
            except Exception:
                return match.group(0)
        return re.sub(cls.DEFAULT_SYNTAX, replacer, html)

    @classmethod
    def _load_html_with_assets(cls, html_path: str) -> str:
        base_dir = os.path.dirname(os.path.abspath(html_path))
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        css_pattern = r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\'][^>]*>'
        css_pattern_alt = r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\'][^>]*>'

        def replace_css(match):
            href = match.group(1)
            if href.startswith(('http://', 'https://', '//')):
                return match.group(0)
            css_path = os.path.join(base_dir, href)
            if os.path.isfile(css_path):
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                return f'<style>\n{css_content}\n</style>'
            return match.group(0)
        html = re.sub(css_pattern, replace_css, html)
        html = re.sub(css_pattern_alt, replace_css, html)
        js_pattern = r'<script[^>]+src=["\']([^"\']+)["\'][^>]*></script>'

        def replace_js(match):
            src = match.group(1)
            if src.startswith(('http://', 'https://', '//')):
                return match.group(0)
            js_path = os.path.join(base_dir, src)
            if os.path.isfile(js_path):
                with open(js_path, 'r', encoding='utf-8') as f:
                    js_content = f.read()
                js_content = re.sub(cls.DEFAULT_SYNTAX, '', js_content)
                return f'<script>\n{js_content}\n</script>'
            return match.group(0)
        html = re.sub(js_pattern, replace_js, html)
        return html
    ### PRIVATE UTILITIES END