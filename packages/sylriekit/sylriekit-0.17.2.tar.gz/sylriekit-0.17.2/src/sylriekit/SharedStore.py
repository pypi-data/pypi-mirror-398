import json
import shutil
import subprocess
import sys
import time
import hashlib

import redis


class SharedStore:
    _PREFIX = "sylriekit"
    DEFAULT_SESSION_TTL = 3600
    DEFAULT_RATE_LIMIT_WINDOW = 5

    _redis = None
    HOST = "localhost"
    PORT = 6379
    DB = 0
    PASSWORD = None

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "SharedStore" in config.keys():
            store_config = config["SharedStore"]
            cls.HOST = store_config.get("HOST", cls.HOST)
            cls.PORT = store_config.get("PORT", cls.PORT)
            cls.DB = store_config.get("DB", cls.DB)
            cls.PASSWORD = store_config.get("PASSWORD", cls.PASSWORD)
            cls.DEFAULT_SESSION_TTL = store_config.get("DEFAULT_SESSION_TTL", cls.DEFAULT_SESSION_TTL)
            cls.DEFAULT_RATE_LIMIT_WINDOW = store_config.get("DEFAULT_RATE_LIMIT_WINDOW", cls.DEFAULT_RATE_LIMIT_WINDOW)


    @classmethod
    def ensure_redis(cls, host: str = None, port: int = None, db: int = None, password: str = None) -> dict:
        host = host or cls.HOST
        port = port or cls.PORT

        try:
            cls.connect(host=host, port=port, db=db, password=password)
            return {"success": True, "message": "Redis connected", "method": "existing"}
        except Exception:
            pass

        is_windows = sys.platform == "win32"

        if is_windows:
            if cls._try_docker_redis(port):
                try:
                    cls.connect(host=host, port=port, db=db, password=password)
                    return {"success": True, "message": "Redis started via Docker", "method": "docker"}
                except Exception:
                    pass

            if cls._try_wsl_redis():
                try:
                    cls.connect(host=host, port=port, db=db, password=password)
                    return {"success": True, "message": "Redis started via WSL", "method": "wsl"}
                except Exception:
                    pass

            if cls._try_memurai():
                try:
                    cls.connect(host=host, port=port, db=db, password=password)
                    return {"success": True, "message": "Redis started via Memurai", "method": "memurai"}
                except Exception:
                    pass

            return {
                "success": False,
                "message": cls._windows_install_instructions(),
                "method": None
            }

        else:
            if cls._try_systemctl_redis():
                try:
                    cls.connect(host=host, port=port, db=db, password=password)
                    return {"success": True, "message": "Redis started via systemctl", "method": "systemctl"}
                except Exception:
                    pass

            if cls._try_direct_redis(port):
                try:
                    import time
                    time.sleep(0.5)  # Give it a moment to start
                    cls.connect(host=host, port=port, db=db, password=password)
                    return {"success": True, "message": "Redis started directly", "method": "direct"}
                except Exception:
                    pass

            if cls._try_docker_redis(port):
                try:
                    cls.connect(host=host, port=port, db=db, password=password)
                    return {"success": True, "message": "Redis started via Docker", "method": "docker"}
                except Exception:
                    pass

            return {
                "success": False,
                "message": cls._linux_install_instructions(),
                "method": None
            }

    @classmethod
    def _try_docker_redis(cls, port: int = 6379) -> bool:
        if not shutil.which("docker"):
            return False

        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=redis", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=10
            )
            if "redis" in result.stdout:
                subprocess.run(["docker", "start", "redis"], capture_output=True, timeout=10)
                import time
                time.sleep(1)
                return True

            result = subprocess.run(
                ["docker", "run", "-d", "--name", "redis", "-p", f"{port}:6379", "redis"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                import time
                time.sleep(2)
                return True
        except Exception:
            pass
        return False

    @classmethod
    def _try_wsl_redis(cls) -> bool:
        if not shutil.which("wsl"):
            return False

        try:
            result = subprocess.run(
                ["wsl", "which", "redis-server"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return False

            subprocess.run(
                ["wsl", "sudo", "service", "redis-server", "start"],
                capture_output=True, timeout=10
            )
            import time
            time.sleep(1)
            return True
        except Exception:
            pass
        return False

    @classmethod
    def _try_memurai(cls) -> bool:
        try:
            result = subprocess.run(
                ["sc", "query", "Memurai"],
                capture_output=True, text=True, timeout=10
            )
            if "Memurai" in result.stdout:
                subprocess.run(["sc", "start", "Memurai"], capture_output=True, timeout=10)
                import time
                time.sleep(1)
                return True
        except Exception:
            pass
        return False

    @classmethod
    def _try_systemctl_redis(cls) -> bool:
        if not shutil.which("systemctl"):
            return False

        try:
            subprocess.run(
                ["sudo", "systemctl", "start", "redis-server"],
                capture_output=True, timeout=10
            )
            return True
        except Exception:
            pass

        try:
            subprocess.run(
                ["sudo", "systemctl", "start", "redis"],
                capture_output=True, timeout=10
            )
            return True
        except Exception:
            pass
        return False

    @classmethod
    def _try_direct_redis(cls, port: int = 6379) -> bool:
        if not shutil.which("redis-server"):
            return False

        try:
            subprocess.Popen(
                ["redis-server", "--port", str(port), "--daemonize", "yes"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            pass
        return False

    @classmethod
    def _windows_install_instructions(cls) -> str:
        return """
    Redis is not available. Install using one of these methods:

    1. DOCKER (Recommended):
       - Install Docker Desktop: https://www.docker.com/products/docker-desktop
       - Run: docker run -d --name redis -p 6379:6379 redis

    2. WSL (Windows Subsystem for Linux):
       - Enable WSL: wsl --install
       - In WSL terminal:
         sudo apt update
         sudo apt install redis-server
         sudo service redis-server start

    3. MEMURAI (Native Windows):
       - Download from: https://www.memurai.com/get-memurai
       - Install and it runs as a Windows service

    After installing, call SharedStore.ensure_redis() again.
    """.strip()

    @classmethod
    def _linux_install_instructions(cls) -> str:
        return """
    Redis is not available. Install using one of these methods:

    1. APT (Debian/Ubuntu):
       sudo apt update
       sudo apt install redis-server
       sudo systemctl start redis-server

    2. YUM (CentOS/RHEL):
       sudo yum install redis
       sudo systemctl start redis

    3. DOCKER:
       docker run -d --name redis -p 6379:6379 redis

    After installing, call SharedStore.ensure_redis() again.
    """.strip()
    @classmethod
    def connect(cls, host: str = None, port: int = None, db: int = None, password: str = None):
        cls._redis = redis.Redis(
            host=host or cls.HOST,
            port=port or cls.PORT,
            db=db or cls.DB,
            password=password or cls.PASSWORD,
            decode_responses=True
        )
        cls._redis.ping()

    @classmethod
    def is_connected(cls) -> bool:
        if cls._redis is None:
            return False
        try:
            cls._redis.ping()
            return True
        except Exception:
            return False

    ### SESSION STORAGE START
    @classmethod
    def get_session_data(cls, session_id: str, key: str = "*", ttl: int = None):
        if not session_id:
            return None if key != "*" else {}
        if not cls.is_connected():
            return None if key != "*" else {}

        ttl = ttl or cls.DEFAULT_SESSION_TTL
        redis_key = cls._key("session", session_id)

        if key == "*":
            data = cls._redis.hgetall(redis_key)
            return {k: cls._deserialize(v) for k, v in data.items()}
        else:
            value = cls._redis.hget(redis_key, key)
            return cls._deserialize(value) if value else None

    @classmethod
    def set_session_data(cls, session_id: str, key: str, value, ttl: int = None):
        if not session_id:
            return False
        if not cls.is_connected():
            return False

        ttl = ttl or cls.DEFAULT_SESSION_TTL
        redis_key = cls._key("session", session_id)
        cls._redis.hset(redis_key, key, cls._serialize(value))
        cls._redis.expire(redis_key, ttl)
        return True

    @classmethod
    def delete_session(cls, session_id: str):
        if not session_id:
            return
        if not cls.is_connected():
            return
        cls._redis.delete(cls._key("session", session_id))

    @classmethod
    def migrate_session(cls, old_id: str, new_id: str, ttl: int = None):
        if not old_id or not new_id:
            return False
        if not cls.is_connected():
            return False

        ttl = ttl or cls.DEFAULT_SESSION_TTL
        old_key = cls._key("session", old_id)
        new_key = cls._key("session", new_id)

        data = cls._redis.hgetall(old_key)
        if data:
            cls._redis.hset(new_key, mapping=data)
            cls._redis.expire(new_key, ttl)

        cls._redis.delete(old_key)
        return True

    @classmethod
    def session_exists(cls, session_id: str) -> bool:
        if not session_id:
            return False
        if not cls.is_connected():
            return False
        return cls._redis.exists(cls._key("session", session_id)) > 0
    ### SESSION STORAGE END

    ### RATE LIMITING START
    @classmethod
    def is_rate_limited(cls, func_name: str, max_calls: int, window: int = None) -> bool:
        if not cls.is_connected():
            return False

        window = window or cls.DEFAULT_RATE_LIMIT_WINDOW
        redis_key = cls._key("ratelimit", func_name)
        now = time.time()
        window_start = now - window

        pipe = cls._redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        results = pipe.execute()
        current_count = results[1]

        return current_count >= max_calls

    @classmethod
    def record_call(cls, func_name: str, window: int = None):
        if not cls.is_connected():
            return

        window = window or cls.DEFAULT_RATE_LIMIT_WINDOW
        redis_key = cls._key("ratelimit", func_name)
        now = time.time()

        unique_id = f"{now}:{hashlib.md5(str(now).encode()).hexdigest()[:8]}"
        cls._redis.zadd(redis_key, {unique_id: now})
        cls._redis.expire(redis_key, window + 1)

    @classmethod
    def check_and_record(cls, func_name: str, max_calls: int, window: int = None) -> bool:
        if cls.is_rate_limited(func_name, max_calls, window):
            return False
        cls.record_call(func_name, window)
        return True
    ### RATE LIMITING END

    ### FUNCTION CACHE START
    @classmethod
    def cache_function(cls, name: str, code: str, data: dict, ttl: int = 60):
        if not cls.is_connected():
            return

        redis_key = cls._key("func", name)
        cls._redis.hset(redis_key, mapping={
            "code": code,
            "data": cls._serialize(data),
            "cached_at": time.time()
        })
        cls._redis.expire(redis_key, ttl)

    @classmethod
    def get_cached_function(cls, name: str) -> dict | None:
        if not cls.is_connected():
            return None

        redis_key = cls._key("func", name)
        data = cls._redis.hgetall(redis_key)
        if not data:
            return None
        return {
            "name": name,
            "code": data.get("code", ""),
            "data": cls._deserialize(data.get("data", "{}")),
            "cached_at": float(data.get("cached_at", 0))
        }

    @classmethod
    def list_cached_functions(cls) -> list:
        if not cls.is_connected():
            return []

        pattern = cls._key("func", "*")
        keys = cls._redis.keys(pattern)
        prefix_len = len(cls._key("func", ""))
        return [k[prefix_len:] for k in keys]
    ### FUNCTION CACHE END

    ### PRIVATE UTILITIES START
    @classmethod
    def _key(cls, *parts) -> str:
        return f"{cls._PREFIX}:{':'.join(parts)}"

    @classmethod
    def _serialize(cls, value) -> str:
        return json.dumps(value)

    @classmethod
    def _deserialize(cls, value: str):
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    ### PRIVATE UTILITIES END
