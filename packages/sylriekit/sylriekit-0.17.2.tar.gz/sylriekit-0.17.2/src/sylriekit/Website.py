import os
import signal
import subprocess
import sys
import tempfile
import time
import secrets
import hashlib
import inspect
import dill

from sylriekit.Constants import Constants
from sylriekit.InlinePython import InlinePython
from sylriekit.SharedStore import SharedStore

_WEBSITE_PROTECTED_ATTRS = {
    "HOST", "PORT", "WORKERS", "TIMEOUT"
}


class Website(metaclass=Constants.protect_class_meta(_WEBSITE_PROTECTED_ATTRS, "WEBSITE_CONFIG_LOCKED")):
    HOST = "127.0.0.1"
    PORT = 5000
    WORKERS = 4
    TIMEOUT = 30

    _URL_PROCESSOR = None
    _RENDERER = None
    _PROCESS = None
    _PID_FILE = None
    PYTHON_RENDER_ENABLED = False
    PYTHON_RENDER_MODE = "html"
    CACHE_API_ENABLED = True
    CACHE_API_PATH = "/api/cache"
    BASE_DIR = None
    _API_FUNCTIONS = {}
    SESSION_TTL = 3600
    COOKIE_SECURE = True
    _SESSION_GENERATOR = None
    _SESSION_VERIFIER = None

    @classmethod
    def load_config(cls, config: dict):
        cls._check_config_lock()
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Website" in config.keys():
            website_config = config["Website"]
            cls.HOST = website_config.get("HOST", cls.HOST)
            cls.PORT = website_config.get("PORT", cls.PORT)
            cls.WORKERS = website_config.get("WORKERS", cls.WORKERS)
            cls.TIMEOUT = website_config.get("TIMEOUT", cls.TIMEOUT)
            cls._PID_FILE = website_config.get("PID_FILE", cls._PID_FILE)
            cls.PYTHON_RENDER_ENABLED = website_config.get("PYTHON_RENDER_ENABLED", cls.PYTHON_RENDER_ENABLED)
            cls.PYTHON_RENDER_MODE = website_config.get("PYTHON_RENDER_MODE", cls.PYTHON_RENDER_MODE)
            cls.CACHE_API_ENABLED = website_config.get("CACHE_API_ENABLED", cls.CACHE_API_ENABLED)
            cls.CACHE_API_PATH = website_config.get("CACHE_API_PATH", cls.CACHE_API_PATH)
            cls.SESSION_TTL = website_config.get("SESSION_TTL", cls.SESSION_TTL)
            cls.COOKIE_SECURE = website_config.get("COOKIE_SECURE", cls.COOKIE_SECURE)


    @classmethod
    def api(cls):
        def decorator(func):
            cls._API_FUNCTIONS[func.__name__] = {
                "func": func
            }

            return func

        return decorator

    @classmethod
    def call_api(cls, func_name: str, kwargs: dict) -> dict:
        if func_name not in cls._API_FUNCTIONS:
            return {"error": True, "message": "Function not found"}

        entry = cls._API_FUNCTIONS[func_name]

        try:
            func = entry["func"]
            result = func(**kwargs)
            return {"error": False, "result": result}
        except Exception as e:
            return {"error": True, "message": str(e)}

    @classmethod
    def get_api_functions(cls) -> list:
        return list(cls._API_FUNCTIONS.keys())


    @classmethod
    def enable_python_render(cls, mode: str = "html"):
        if mode not in ("html", "template"):
            raise ValueError(f"Invalid mode '{mode}'. Must be 'html' or 'template'")
        cls.PYTHON_RENDER_ENABLED = True
        cls.PYTHON_RENDER_MODE = mode

    @classmethod
    def disable_python_render(cls):
        cls.PYTHON_RENDER_ENABLED = False

    @classmethod
    def url_processing(cls, func=None):
        def decorator(f):
            cls._URL_PROCESSOR = f
            return f

        if func is not None:
            return decorator(func)
        return decorator

    @classmethod
    def render(cls, func=None):
        def decorator(f):
            cls._RENDERER = f
            return f

        if func is not None:
            return decorator(func)
        return decorator

    @classmethod
    def generate_session(cls, func=None):
        def decorator(f):
            cls._SESSION_GENERATOR = f
            return f

        if func is not None:
            return decorator(func)
        return decorator

    @classmethod
    def verify_session(cls, func=None):
        def decorator(f):
            cls._SESSION_VERIFIER = f
            return f

        if func is not None:
            return decorator(func)
        return decorator

    @classmethod
    def python_render(cls, text: str, mode: str = None) -> str:
        if not isinstance(text, str):
            raise ValueError("Text must be a string")

        render_mode = mode if mode is not None else cls.PYTHON_RENDER_MODE

        if render_mode == "html":
            return InlinePython.render_html(text, session_token="placeholder")
        elif render_mode == "template":
            return InlinePython.render(text)
        else:
            raise ValueError(f"Invalid mode '{render_mode}'. Must be 'html' or 'template'")

    @classmethod
    def hit_cache(cls, function_name: str, function_args: dict = None):
        return InlinePython.hit_cache(function_name, function_args)

    @classmethod
    def get_cached_function(cls, function_name: str):
        return InlinePython.get_cached_callable(function_name)

    @classmethod
    def list_cached_functions(cls) -> list:
        return [entry["name"] for entry in InlinePython.get_valid_cache_functions()]

    @classmethod
    def clear_function_cache(cls) -> None:
        InlinePython.clear_cache()

    @classmethod
    def get_local_storage(cls, key: str="*"):
        try:
            from flask import request
            if key == "*":
                return dict(request.cookies)
            return request.cookies.get(key)
        except Exception:
            return None if key != "*" else {}

    @classmethod
    def set_local_storage(cls, key: str, val: str):
        try:
            from flask import g
            if not hasattr(g, "pending_cookies"):
                g.pending_cookies = {}
            g.pending_cookies[key] = val
        except Exception:
            pass

    @classmethod
    def get_session_data(cls, key: str="*", session_id: str = None):
        if session_id is None:
            try:
                from flask import request
                session_id = request.cookies.get("SessionID")
            except Exception:
                pass
        if session_id is None:
            return None if key != "*" else {}
        return SharedStore.get_session_data(session_id, key, cls.SESSION_TTL)

    @classmethod
    def set_session_data(cls, key: str, value, session_id: str = None):
        if session_id is None:
            try:
                from flask import request
                session_id = request.cookies.get("SessionID")
            except Exception:
                pass
        if session_id is None:
            return
        SharedStore.set_session_data(session_id, key, value, cls.SESSION_TTL)

    @classmethod
    def delete_session(cls, session_id: str = None):
        if session_id is None:
            try:
                from flask import request
                session_id = request.cookies.get("SessionID")
            except Exception:
                pass
        if session_id is None:
            return
        SharedStore.delete_session(session_id)

    @classmethod
    def session_exists(cls, session_id: str = None) -> bool:
        if session_id is None:
            try:
                from flask import request
                session_id = request.cookies.get("SessionID")
            except Exception:
                pass
        if session_id is None:
            return False
        return SharedStore.session_exists(session_id)

    @classmethod
    def update_session(cls, old_session_id: str = None):
        if old_session_id is None:
            try:
                from flask import request
                old_session_id = request.cookies.get("SessionID")
            except Exception:
                pass
        if old_session_id is None:
            return None

        new_token = secrets.token_hex(16)
        new_timestamp = str(int(time.time() * 1000))
        new_session_id = f"{new_token}.{new_timestamp}.{secrets.token_hex(8)}"

        SharedStore.migrate_session(old_session_id, new_session_id, cls.SESSION_TTL)

        cls.set_local_storage("SessionID", new_session_id)

        return new_session_id

    @classmethod
    def status(cls) -> dict:
        pid = cls._get_running_pid()
        if pid is None:
            return {
                "running": False,
                "pid": None,
                "host": cls.HOST,
                "port": cls.PORT
            }

        if cls._is_process_alive(pid):
            return {
                "running": True,
                "pid": pid,
                "host": cls.HOST,
                "port": cls.PORT
            }

        cls._cleanup_pid_file()
        return {
            "running": False,
            "pid": None,
            "host": cls.HOST,
            "port": cls.PORT
        }

    @classmethod
    def start(cls) -> dict:
        status = cls.status()
        if status["running"]:
            return {
                "success": False,
                "message": f"Website already running on PID {status['pid']}",
                "pid": status["pid"]
            }


        server_data = {
            "host": cls.HOST,
            "port": cls.PORT,
            "workers": cls.WORKERS,
            "timeout": cls.TIMEOUT,
            "url_processor": cls._URL_PROCESSOR,
            "renderer": cls._RENDERER,
            "python_render_enabled": cls.PYTHON_RENDER_ENABLED,
            "python_render_mode": cls.PYTHON_RENDER_MODE,
            "cache_api_enabled": cls.CACHE_API_ENABLED,
            "cache_api_path": cls.CACHE_API_PATH,
            "base_dir": cls.BASE_DIR,
            "api_functions": cls._API_FUNCTIONS.copy(),
            "session_generator": cls._SESSION_GENERATOR,
            "session_verifier": cls._SESSION_VERIFIER,
            "pid_file": cls._get_pid_file_path(),
            "redis_host": SharedStore.HOST,
            "redis_port": SharedStore.PORT,
            "redis_db": SharedStore.DB,
            "redis_password": SharedStore.PASSWORD,
            "session_ttl": cls.SESSION_TTL,
            "cookie_secure": cls.COOKIE_SECURE
        }

        data_file = tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".pkl",
            delete=False
        )
        dill.dump(server_data, data_file)
        data_file.close()

        server_script = cls._generate_server_script()

        script_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        )
        script_file.write(server_script)
        script_file.close()

        if sys.platform == "win32":
            creationflags = (
                    subprocess.CREATE_NEW_PROCESS_GROUP |
                    subprocess.DETACHED_PROCESS |
                    subprocess.CREATE_NO_WINDOW
            )
            process = subprocess.Popen(
                [sys.executable, script_file.name, data_file.name],
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
        else:
            process = subprocess.Popen(
                [sys.executable, script_file.name, data_file.name],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

        time.sleep(1.5)

        if cls._is_process_alive(process.pid):
            return {
                "success": True,
                "message": f"Website started on {cls.HOST}:{cls.PORT}",
                "pid": process.pid
            }

        return {
            "success": False,
            "message": "Failed to start website server",
            "pid": None
        }

    @classmethod
    def stop(cls) -> dict:
        status = cls.status()
        if not status["running"]:
            return {
                "success": False,
                "message": "No website is currently running",
                "pid": None
            }

        pid = status["pid"]

        try:
            if sys.platform == "win32":
                import subprocess
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True
                )
            else:
                os.kill(pid, signal.SIGTERM)

                for _ in range(10):
                    time.sleep(0.5)
                    if not cls._is_process_alive(pid):
                        break

                if cls._is_process_alive(pid):
                    os.kill(pid, signal.SIGKILL)

            cls._cleanup_pid_file()
            cls._PROCESS = None

            return {
                "success": True,
                "message": f"Website stopped (PID {pid})",
                "pid": pid
            }
        except ProcessLookupError:
            cls._cleanup_pid_file()
            return {
                "success": True,
                "message": "Website process already terminated",
                "pid": pid
            }
        except PermissionError:
            return {
                "success": False,
                "message": f"Permission denied to stop process {pid}",
                "pid": pid
            }

    @classmethod
    def reboot(cls) -> dict:
        stop_result = cls.stop()

        time.sleep(1)

        start_result = cls.start()

        return {
            "success": start_result["success"],
            "message": f"Reboot: {stop_result['message']} -> {start_result['message']}",
            "pid": start_result["pid"]
        }

    @classmethod
    def lock_config(cls):
        cls._check_config_lock()
        Constants.define("WEBSITE_CONFIG_LOCKED", True)

    ### PRIVATE UTILITIES START
    @classmethod
    def _check_config_lock(cls):
        if Constants.get("WEBSITE_CONFIG_LOCKED", False):
            raise PermissionError("Config is locked and cannot be modified")


    @classmethod
    def _get_pid_file_path(cls) -> str:
        if cls._PID_FILE:
            return cls._PID_FILE
        return os.path.join(os.getcwd(), ".sylriekit_website.pid")

    @classmethod
    def _get_running_pid(cls):
        pid_file = cls._get_pid_file_path()
        if not os.path.exists(pid_file):
            return None
        try:
            with open(pid_file, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None

    @classmethod
    def _save_pid(cls, pid: int):
        pid_file = cls._get_pid_file_path()
        with open(pid_file, "w") as f:
            f.write(str(pid))

    @classmethod
    def _cleanup_pid_file(cls):
        pid_file = cls._get_pid_file_path()
        if os.path.exists(pid_file):
            os.remove(pid_file)

    @classmethod
    def _is_process_alive(cls, pid: int) -> bool:
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                os.kill(pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False

    @staticmethod
    def _generate_server_script() -> str:
        return '''
import os
import sys
import traceback
import hashlib
import secrets
import time

import dill

def run_server(data_file_path):
    error_log = "error_log"

    try:
        with open(data_file_path, "rb") as f:
            data = dill.load(f)

        host = data["host"]
        port = data["port"]
        workers = data["workers"]
        timeout = data["timeout"]
        url_processor = data.get("url_processor")
        renderer = data.get("renderer")
        python_render_enabled = data.get("python_render_enabled", False)
        python_render_mode = data.get("python_render_mode", "html")
        cache_api_enabled = data.get("cache_api_enabled", True)
        cache_api_path = data.get("cache_api_path", "/api/cache")
        base_dir = data.get("base_dir")
        api_functions = data.get("api_functions", {})
        session_generator = data.get("session_generator")
        session_verifier = data.get("session_verifier")
        pid_file = data["pid_file"]
        redis_host = data.get("redis_host", "localhost")
        redis_port = data.get("redis_port", 6379)
        redis_db = data.get("redis_db", 0)
        redis_password = data.get("redis_password")
        session_ttl = data.get("session_ttl", 3600)
        cookie_secure = data.get("cookie_secure", True)

        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))

        try:
            os.remove(data_file_path)
        except:
            pass

        from flask import Flask, request, Response, jsonify
        from sylriekit.InlinePython import InlinePython
        from sylriekit.Website import Website
        from sylriekit.SharedStore import SharedStore
        import inspect

        app = Flask(__name__)

        try:
            SharedStore.connect(host=redis_host, port=redis_port, db=redis_db, password=redis_password)
        except Exception as e:
            with open(error_log, "a") as f:
                f.write(f"SharedStore connection failed: {e}\\n")
                f.write(traceback.format_exc() + "\\n")

        Website.SESSION_TTL = session_ttl

        InlinePython.JS_BRIDGE_ENDPOINT = cache_api_path
        if base_dir:
            InlinePython.BASE_DIR = base_dir

        _session_secret = secrets.token_hex(32)

        def default_session_generator(cookies, Website=None, SessionID=None):
            from sylriekit.SharedStore import SharedStore
            existing = cookies.get("SessionID")
            old_session_to_migrate = None
            
            if existing:
                parts = existing.split(".")
                if len(parts) == 3:
                    token_part, timestamp_part, sig_part = parts
                    expected_sig = hashlib.sha256(f"{token_part}.{timestamp_part}.{_session_secret}".encode()).hexdigest()[:32]
                    if sig_part == expected_sig:
                        return existing
                    else:
                        old_session_to_migrate = existing
            
            token_part = secrets.token_hex(16)
            timestamp_part = str(int(time.time() * 1000))
            signature = hashlib.sha256(f"{token_part}.{timestamp_part}.{_session_secret}".encode()).hexdigest()[:32]
            new_session_id = f"{token_part}.{timestamp_part}.{signature}"
            
            if old_session_to_migrate and Website is not None:
                SharedStore.migrate_session(old_session_to_migrate, new_session_id, Website.SESSION_TTL)
            
            return new_session_id

        def default_session_verifier(session_id, Website=None, SessionID=None):
            if not session_id:
                return ""
            parts = session_id.split(".")
            if len(parts) != 3:
                return ""
            token_part, timestamp_part, sig_part = parts
            expected_sig = hashlib.sha256(f"{token_part}.{timestamp_part}.{_session_secret}".encode()).hexdigest()[:32]
            if sig_part != expected_sig:
                return ""
            return ""

        def default_url_processor(request_data, Website=None, SessionID=None):
            return ""

        def default_renderer(result, Website=None, SessionID=None):
            return result

        if session_generator is None:
            session_generator = default_session_generator
        if session_verifier is None:
            session_verifier = default_session_verifier
        if url_processor is None:
            url_processor = default_url_processor
        if renderer is None:
            renderer = default_renderer

        def call_with_injection(func, *args, **kwargs):
            sig = inspect.signature(func)
            if "Website" in sig.parameters and "Website" not in kwargs:
                kwargs["Website"] = Website
            if "SessionID" in sig.parameters and "SessionID" not in kwargs:
                try:
                    kwargs["SessionID"] = request.cookies.get("SessionID")
                except Exception:
                    kwargs["SessionID"] = None
            return func(*args, **kwargs)

        def do_python_render(content):
            if not isinstance(content, str):
                return content

            if python_render_mode == "html":
                return InlinePython.render_html(content, session_token="placeholder")
            elif python_render_mode == "template":
                return InlinePython.render(content)
            return content

        def handle_cache_api(function_name):
            from flask import g
            try:
                if request.method == "POST":
                    if not request.is_json:
                        return jsonify({"error": True, "message": "JSON required"}), 400
                    func_args = request.get_json() or {}
                else:
                    func_args = dict(request.args)
            except Exception as e:
                return jsonify({"error": True, "message": "Invalid request arguments"}), 400

            if function_name in api_functions:
                try:
                    entry = api_functions[function_name]
                    func = entry["func"]

                    from sylriekit.Website import Website
                    import inspect

                    g.pending_cookies = {}

                    sig = inspect.signature(func)
                    call_args = func_args.copy()

                    if "Website" in sig.parameters:
                        call_args["Website"] = Website

                    if "SessionID" in sig.parameters:
                        try:
                            call_args["SessionID"] = request.cookies.get("SessionID")
                        except Exception:
                            call_args["SessionID"] = None

                    result = func(**call_args)

                    resp = jsonify({
                        "error": False,
                        "result": result
                    })

                    if hasattr(g, "pending_cookies"):
                        for k, v in g.pending_cookies.items():
                            if v is None or v == "":
                                resp.delete_cookie(k)
                            else:
                                resp.set_cookie(k, str(v), httponly=True, secure=cookie_secure, samesite='Lax')

                    return resp
                except Exception as e:
                    with open(error_log, "a") as f:
                        f.write(f"API function error for '{function_name}': {e}\\n")
                        f.write(traceback.format_exc() + "\\n")
                    return jsonify({"error": True, "message": "Function call failed"}), 500

            try:
                g.pending_cookies = {}
                result = InlinePython.hit_cache(function_name, func_args)
            except Exception as e:
                with open(error_log, "a") as f:
                    f.write(f"Cache API error for '{function_name}': {e}\\n")
                    f.write(traceback.format_exc() + "\\n")
                return jsonify({"error": True, "message": "Internal error"}), 500

            if result.get("rate_limited"):
                return jsonify({
                    "error": True, 
                    "message": "Rate limit exceeded",
                    "rate_limited": True
                }), 429

            if result.get("error"):
                msg = result.get("message", "Unknown error")
                return jsonify({"error": True, "message": msg}), 400

            resp = jsonify({
                "error": False,
                "result": result.get("result"),
                "data": result.get("data", {})
            })

            if hasattr(g, "pending_cookies"):
                for k, v in g.pending_cookies.items():
                    if v is None or v == "":
                        resp.delete_cookie(k)
                    else:
                        resp.set_cookie(k, str(v), httponly=True, secure=cookie_secure, samesite='Lax')

            return resp

        @app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        @app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        def catch_all(path):
            from flask import g, make_response
            full_path = f"/{path}"
            g.pending_cookies = {}

            if cache_api_enabled and full_path.startswith(cache_api_path + "/"):
                function_name = full_path[len(cache_api_path) + 1:]
                if function_name and not function_name.startswith("__"):
                    return handle_cache_api(function_name)

            if cache_api_enabled and full_path == cache_api_path:
                cached = InlinePython.get_valid_cache_functions()
                available = []
                for entry in cached:
                    available.append({
                        "name": entry.get("name"),
                        "data": entry.get("data", {}),
                        "expire": entry.get("expire"),
                        "ttl": entry.get("expire", 0) - time.time()
                    })

                for name in api_functions:
                    available.append({
                        "name": name,
                        "data": {},
                        "expire": None,
                        "ttl": -1
                    })

                return jsonify({
                    "error": False,
                    "functions": available,
                    "endpoint": cache_api_path
                })

            # Session handling
            session_id = None
            try:
                cookies = dict(request.cookies)
                session_id = call_with_injection(session_generator, cookies)
                if session_id and session_id != cookies.get("SessionID"):
                    g.pending_cookies["SessionID"] = session_id
            except Exception as e:
                with open(error_log, "a") as f:
                    f.write(f"Session generator error: {e}\\n")
                    f.write(traceback.format_exc() + "\\n")

            try:
                verify_result = call_with_injection(session_verifier, session_id, SessionID=session_id)
                if verify_result and verify_result != "":
                    resp = make_response(verify_result)
                    if hasattr(g, "pending_cookies"):
                        for k, v in g.pending_cookies.items():
                            if v is None or v == "":
                                resp.delete_cookie(k)
                            else:
                                resp.set_cookie(k, str(v), httponly=True, secure=cookie_secure, samesite='Lax')
                    return resp
            except Exception as e:
                with open(error_log, "a") as f:
                    f.write(f"Session verifier error: {e}\\n")
                    f.write(traceback.format_exc() + "\\n")

            request_data = {
                "path": full_path,
                "method": request.method,
                "remote_addr": request.remote_addr,
                "args": dict(request.args),
                "headers": dict(request.headers),
                "data": request.get_data(as_text=True),
                "json": request.get_json(silent=True),
                "form": dict(request.form),
                "cookies": dict(request.cookies),
                "session_id": session_id
            }

            try:
                result = call_with_injection(url_processor, request_data, SessionID=session_id)
            except Exception as e:
                with open(error_log, "a") as f:
                    f.write(f"URL Processor error: {e}\\n")
                    f.write(traceback.format_exc() + "\\n")
                return f"""<html><body>
                    <h1>URL Processor Error</h1>
                    <p><b>Path:</b> {path}</p>
                    <p>An internal error occurred. Check error_log for details.</p>
                </body></html>""", 500

            if python_render_enabled and isinstance(result, str):
                try:
                    result = do_python_render(result)
                except Exception as e:
                    with open(error_log, "a") as f:
                        f.write(f"Python Render error: {e}\\n")
                        f.write(traceback.format_exc() + "\\n")
                    return f"""<html><body>
                        <h1>Python Render Error</h1>
                        <p><b>Path:</b> {path}</p>
                        <p>An internal error occurred. Check error_log for details.</p>
                    </body></html>""", 500

            try:
                result = call_with_injection(renderer, result, SessionID=session_id)
            except Exception as e:
                with open(error_log, "a") as f:
                    f.write(f"Renderer error: {e}\\n")
                    f.write(traceback.format_exc() + "\\n")
                return f"""<html><body>
                    <h1>Renderer Error</h1>
                    <p><b>Path:</b> {path}</p>
                    <p>An internal error occurred. Check error_log for details.</p>
                </body></html>""", 500

            try:
                resp = None
                if isinstance(result, Response):
                    resp = result
                elif isinstance(result, dict):
                    resp = make_response(jsonify(result))
                elif isinstance(result, tuple):
                    if len(result) == 2 and isinstance(result[1], int):
                        content, status = result
                        if isinstance(content, dict):
                            resp = make_response(jsonify(content), status)
                        else:
                            resp = make_response(str(content), status)
                    else:
                        resp = make_response(result)
                else:
                    resp = make_response(str(result))
                
                if hasattr(g, "pending_cookies"):
                    for k, v in g.pending_cookies.items():
                        if v is None or v == "":
                            resp.delete_cookie(k)
                        else:
                            resp.set_cookie(k, str(v), httponly=True, secure=cookie_secure, samesite='Lax')
                
                return resp
            except Exception as e:
                with open(error_log, "a") as f:
                    f.write(f"Response error: {e}\\n")
                    f.write(traceback.format_exc() + "\\n")
                return f"""<html><body>
                    <h1>Response Error</h1>
                    <p>An internal error occurred. Check error_log for details.</p>
                </body></html>""", 500

        try:
            from gunicorn.app.base import BaseApplication

            class GunicornApp(BaseApplication):
                def __init__(self, application, options=None):
                    self.options = options or {}
                    self.application = application
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                "bind": f"{host}:{port}",
                "workers": workers,
                "timeout": timeout
            }
            GunicornApp(app, options).run()
        except ImportError:
            app.run(host=host, port=port, debug=False, use_reloader=False)
    except Exception as e:
        with open(error_log, "a") as f:
            f.write(f"Startup error: {e}\\n")
            f.write(traceback.format_exc() + "\\n")
        raise

if __name__ == "__main__":
    run_server(sys.argv[1])
'''
    ### PRIVATE UTILITIES END



