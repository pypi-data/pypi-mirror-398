import os
import json
import time
import subprocess
import threading
import urllib.request
import urllib.error
import re
from typing import Optional, Callable, Any
from copy import deepcopy


class LLM:
    PROVIDER_OPENAI = "openai"
    PROVIDER_ANTHROPIC = "anthropic"
    PROVIDER_XAI = "xai"
    PROVIDER_GEMINI = "gemini"
    PROVIDER_OPENROUTER = "openrouter"
    SUPPORTED_PROVIDERS = [PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_XAI, PROVIDER_GEMINI, PROVIDER_OPENROUTER]
    DEFAULT_MODELS = {
        PROVIDER_OPENAI: "gpt-4o",
        PROVIDER_ANTHROPIC: "claude-sonnet-4-20250514",
        PROVIDER_XAI: "grok-3-latest",
        PROVIDER_GEMINI: "gemini-2.0-flash",
        PROVIDER_OPENROUTER: "openai/gpt-4o",
    }
    API_ENDPOINTS = {
        PROVIDER_OPENAI: "https://api.openai.com/v1/chat/completions",
        PROVIDER_ANTHROPIC: "https://api.anthropic.com/v1/messages",
        PROVIDER_XAI: "https://api.x.ai/v1/chat/completions",
        PROVIDER_GEMINI: "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        PROVIDER_OPENROUTER: "https://openrouter.ai/api/v1/chat/completions",
    }
    REQUEST_TIMEOUT: int = 120

    API_KEY: str = ""
    PROVIDER: str = PROVIDER_OPENAI
    MODEL: str = ""
    SYSTEM_PROMPT: str = "You are a helpful assistant."
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    CHAT_STORAGE_DIR: str = os.getcwd()
    CHAT_STORAGE_FILENAME: str = "llm_chats.json"
    MAX_TOOL_ITERATIONS: int = 10

    _chats: dict = {}
    _mcp_servers: dict = {}
    _mcp_tools: dict = {}
    _mcp_processes: dict = {}
    _lock = threading.RLock()
    _mcp_lock = threading.RLock()

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config.get("api_keys", {})
        if "LLM" in config:
            llm_config = config["LLM"]
            cls.API_KEY = llm_config.get("API_KEY", cls.API_KEY)
            cls.PROVIDER = llm_config.get("PROVIDER", cls.PROVIDER)
            cls.MODEL = llm_config.get("MODEL", cls.MODEL)
            cls.SYSTEM_PROMPT = llm_config.get("SYSTEM_PROMPT", cls.SYSTEM_PROMPT)
            cls.MAX_TOKENS = llm_config.get("MAX_TOKENS", cls.MAX_TOKENS)
            cls.TEMPERATURE = llm_config.get("TEMPERATURE", cls.TEMPERATURE)
            cls.CHAT_STORAGE_DIR = llm_config.get("CHAT_STORAGE_DIR", cls.CHAT_STORAGE_DIR)
            cls.CHAT_STORAGE_FILENAME = llm_config.get("CHAT_STORAGE_FILENAME", cls.CHAT_STORAGE_FILENAME)
            cls.MAX_TOOL_ITERATIONS = llm_config.get("MAX_TOOL_ITERATIONS", cls.MAX_TOOL_ITERATIONS)

        provider_key_map = {
            cls.PROVIDER_OPENAI: "openai",
            cls.PROVIDER_ANTHROPIC: "anthropic",
            cls.PROVIDER_XAI: "xai",
            cls.PROVIDER_GEMINI: "gemini",
            cls.PROVIDER_OPENROUTER: "openrouter",
        }
        if cls.PROVIDER in provider_key_map:
            key_name = provider_key_map[cls.PROVIDER]
            if key_name in api_keys and not cls.API_KEY:
                cls.API_KEY = api_keys[key_name]

    ### CONFIGURATION START
    @classmethod
    def configure(
        cls,
        api_key: str = None,
        provider: str = None,
        model: str = None,
        system_prompt: str = None,
        max_tokens: int = None,
        temperature: float = None,
        chat_storage_dir: str = None,
    ):
        if api_key is not None:
            cls.API_KEY = api_key
        if provider is not None:
            if provider not in cls.SUPPORTED_PROVIDERS:
                raise ValueError(f"Unsupported provider: {provider}. Supported: {cls.SUPPORTED_PROVIDERS}")
            cls.PROVIDER = provider
        if model is not None:
            cls.MODEL = model
        if system_prompt is not None:
            cls.SYSTEM_PROMPT = system_prompt
        if max_tokens is not None:
            cls.MAX_TOKENS = max_tokens
        if temperature is not None:
            cls.TEMPERATURE = temperature
        if chat_storage_dir is not None:
            cls.CHAT_STORAGE_DIR = chat_storage_dir
            os.makedirs(cls.CHAT_STORAGE_DIR, exist_ok=True)

    @classmethod
    def get_model(cls) -> str:
        if cls.MODEL:
            return cls.MODEL
        return cls.DEFAULT_MODELS.get(cls.PROVIDER, "")
    ### CONFIGURATION END

    ### CHAT MANAGEMENT START
    @classmethod
    def send_message(cls, msg: str, chat_id: int = 0, use_tools: bool = True) -> str:
        if not cls.API_KEY:
            raise ValueError("API_KEY not configured. Use LLM.configure(api_key='...') first.")

        cls._ensure_chat_exists(chat_id)

        with cls._lock:
            cls._chats[chat_id]["messages"].append({
                "role": "user",
                "content": msg
            })
            cls._save_chats()

        response = cls._call_llm(chat_id, use_tools=use_tools)

        with cls._lock:
            cls._chats[chat_id]["messages"].append({
                "role": "assistant",
                "content": response
            })
            cls._save_chats()

        return response

    @classmethod
    def get_chat(cls, chat_id: int = 0) -> list:
        cls._load_chats()
        with cls._lock:
            if chat_id not in cls._chats:
                return []
            return deepcopy(cls._chats[chat_id]["messages"])

    @classmethod
    def clear_chat(cls, chat_id: int = 0):
        with cls._lock:
            if chat_id in cls._chats:
                cls._chats[chat_id]["messages"] = []
                cls._save_chats()

    @classmethod
    def delete_chat(cls, chat_id: int = 0):
        with cls._lock:
            if chat_id in cls._chats:
                del cls._chats[chat_id]
                cls._save_chats()

    @classmethod
    def list_chats(cls) -> list:
        cls._load_chats()
        with cls._lock:
            return list(cls._chats.keys())

    @classmethod
    def set_system_prompt(cls, prompt: str, chat_id: int = None):
        if chat_id is not None:
            cls._ensure_chat_exists(chat_id)
            with cls._lock:
                cls._chats[chat_id]["system_prompt"] = prompt
                cls._save_chats()
        else:
            cls.SYSTEM_PROMPT = prompt
    ### CHAT MANAGEMENT END

    ### MCP INTEGRATION START
    @classmethod
    def load_mcp_file(cls, file: str):
        file = os.path.abspath(file)
        if not os.path.exists(file):
            raise FileNotFoundError(f"MCP config file not found: {file}")

        with open(file, "r", encoding="utf-8") as f:
            config = json.load(f)

        mcp_servers = config.get("mcpServers", {})

        for name, server_config in mcp_servers.items():
            cls.add_mcp_server(name, server_config)

    @classmethod
    def add_mcp_server(cls, name: str, config: dict):
        with cls._mcp_lock:
            cls._mcp_servers[name] = config
            cls._start_mcp_server(name)

    @classmethod
    def remove_mcp_server(cls, name: str):
        with cls._mcp_lock:
            if name in cls._mcp_servers:
                del cls._mcp_servers[name]
            if name in cls._mcp_processes:
                try:
                    cls._mcp_processes[name].terminate()
                except Exception:
                    pass
                del cls._mcp_processes[name]

            tools_to_remove = []
            removed_original_names = set()

            for key, info in list(cls._mcp_tools.items()):
                if info.get("server") == name:
                    tools_to_remove.append(key)
                    removed_original_names.add(info.get("original_name"))

            for tool_key in tools_to_remove:
                del cls._mcp_tools[tool_key]

            # Revert namespacing if a tool becomes unique
            for original_name in removed_original_names:
                remaining_keys = [k for k, v in cls._mcp_tools.items() if v.get("original_name") == original_name]
                if len(remaining_keys) == 1:
                    current_key = remaining_keys[0]
                    if current_key != original_name:
                        info = cls._mcp_tools.pop(current_key)
                        cls._mcp_tools[original_name] = info

    @classmethod
    def list_mcp_tools(cls) -> list:
        with cls._mcp_lock:
            return list(cls._mcp_tools.keys())

    @classmethod
    def get_mcp_tools_schema(cls) -> list:
        with cls._mcp_lock:
            tools = []
            for name, tool_info in cls._mcp_tools.items():
                tools.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool_info.get("description", ""),
                        "parameters": tool_info.get("inputSchema", {"type": "object", "properties": {}})
                    }
                })
            return tools

    @classmethod
    def call_mcp_tool(cls, tool_name: str, arguments: dict) -> Any:
        with cls._mcp_lock:
            if tool_name not in cls._mcp_tools:
                raise ValueError(f"MCP tool not found: {tool_name}")

            tool_info = cls._mcp_tools[tool_name]
            server_name = tool_info.get("server")
            real_tool_name = tool_info.get("original_name", tool_name)

            if server_name not in cls._mcp_processes:
                raise RuntimeError(f"MCP server not running: {server_name}")

        return cls._invoke_mcp_tool(server_name, real_tool_name, arguments)

    @classmethod
    def shutdown_mcp_servers(cls):
        with cls._mcp_lock:
            for name, proc in list(cls._mcp_processes.items()):
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            cls._mcp_processes.clear()
            cls._mcp_tools.clear()
    ### MCP INTEGRATION END

    ### PROVIDER API CALLS START
    @classmethod
    def _call_llm(cls, chat_id: int, use_tools: bool = True) -> str:
        provider = cls.PROVIDER

        if provider == cls.PROVIDER_OPENAI:
            return cls._call_openai(chat_id, use_tools)
        elif provider == cls.PROVIDER_ANTHROPIC:
            return cls._call_anthropic(chat_id, use_tools)
        elif provider == cls.PROVIDER_XAI:
            return cls._call_xai(chat_id, use_tools)
        elif provider == cls.PROVIDER_GEMINI:
            return cls._call_gemini(chat_id, use_tools)
        elif provider == cls.PROVIDER_OPENROUTER:
            return cls._call_openrouter(chat_id, use_tools)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @classmethod
    def _call_openrouter(cls, chat_id: int, use_tools: bool = True) -> str:
        messages = cls._build_messages(chat_id)
        tools = cls.get_mcp_tools_schema() if use_tools and cls._mcp_tools else None

        payload = {
            "model": cls.get_model(),
            "messages": messages,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.API_KEY}",
        }

        return cls._openai_style_request(
            cls.API_ENDPOINTS[cls.PROVIDER_OPENROUTER],
            payload,
            headers,
            chat_id,
            use_tools
        )

    @classmethod
    def _call_openai(cls, chat_id: int, use_tools: bool = True) -> str:
        messages = cls._build_messages(chat_id)
        tools = cls.get_mcp_tools_schema() if use_tools and cls._mcp_tools else None

        payload = {
            "model": cls.get_model(),
            "messages": messages,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.API_KEY}",
        }

        return cls._openai_style_request(
            cls.API_ENDPOINTS[cls.PROVIDER_OPENAI],
            payload,
            headers,
            chat_id,
            use_tools
        )

    @classmethod
    def _call_xai(cls, chat_id: int, use_tools: bool = True) -> str:
        messages = cls._build_messages(chat_id)
        tools = cls.get_mcp_tools_schema() if use_tools and cls._mcp_tools else None

        payload = {
            "model": cls.get_model(),
            "messages": messages,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.API_KEY}",
        }

        return cls._openai_style_request(
            cls.API_ENDPOINTS[cls.PROVIDER_XAI],
            payload,
            headers,
            chat_id,
            use_tools
        )

    @classmethod
    def _openai_style_request(cls, url: str, payload: dict, headers: dict, chat_id: int, use_tools: bool) -> str:
        iterations = 0
        while iterations < cls.MAX_TOOL_ITERATIONS:
            iterations += 1

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=cls.REQUEST_TIMEOUT) as resp:
                    response = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8") if e.fp else ""
                raise RuntimeError(f"API Error {e.code}: {error_body}")

            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})

            tool_calls = message.get("tool_calls", [])
            if tool_calls and use_tools:
                payload["messages"].append(message)
                for tool_call in tool_calls:
                    func = tool_call.get("function", {})
                    tool_name = func.get("name", "")
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}

                    try:
                        result = cls.call_mcp_tool(tool_name, args)
                        result_str = json.dumps(result) if not isinstance(result, str) else result
                    except Exception as e:
                        result_str = json.dumps({"error": str(e)})

                    payload["messages"].append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "content": result_str
                    })

                continue

            content = message.get("content", "")
            return content if content else ""

        return "[Max tool iterations reached]"

    @classmethod
    def _call_anthropic(cls, chat_id: int, use_tools: bool = True) -> str:
        messages = cls._build_messages_anthropic(chat_id)
        tools = cls._get_anthropic_tools_schema() if use_tools and cls._mcp_tools else None

        payload = {
            "model": cls.get_model(),
            "messages": messages,
            "max_tokens": cls.MAX_TOKENS,
            "system": cls._get_system_prompt(chat_id),
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
            "x-api-key": cls.API_KEY,
            "anthropic-version": "2023-06-01",
        }

        iterations = 0
        while iterations < cls.MAX_TOOL_ITERATIONS:
            iterations += 1

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                cls.API_ENDPOINTS[cls.PROVIDER_ANTHROPIC],
                data=data,
                headers=headers,
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=cls.REQUEST_TIMEOUT) as resp:
                    response = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8") if e.fp else ""
                raise RuntimeError(f"API Error {e.code}: {error_body}")

            content_blocks = response.get("content", [])
            stop_reason = response.get("stop_reason", "")

            tool_use_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]

            if tool_use_blocks and use_tools:
                payload["messages"].append({
                    "role": "assistant",
                    "content": content_blocks
                })

                tool_results = []
                for tool_block in tool_use_blocks:
                    tool_name = tool_block.get("name", "")
                    tool_id = tool_block.get("id", "")
                    args = tool_block.get("input", {})

                    try:
                        result = cls.call_mcp_tool(tool_name, args)
                        result_str = json.dumps(result) if not isinstance(result, str) else result
                        is_error = False
                    except Exception as e:
                        result_str = str(e)
                        is_error = True

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_str,
                        "is_error": is_error
                    })

                payload["messages"].append({
                    "role": "user",
                    "content": tool_results
                })
                continue

            text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            return "".join(text_parts)

        return "[Max tool iterations reached]"

    @classmethod
    def _call_gemini(cls, chat_id: int, use_tools: bool = True) -> str:
        model = cls.get_model()
        url = cls.API_ENDPOINTS[cls.PROVIDER_GEMINI].format(model=model)
        url = f"{url}?key={cls.API_KEY}"

        contents = cls._build_messages_gemini(chat_id)
        tools = cls._get_gemini_tools_schema() if use_tools and cls._mcp_tools else None

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": cls.MAX_TOKENS,
                "temperature": cls.TEMPERATURE,
            },
        }

        system_prompt = cls._get_system_prompt(chat_id)
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
        }

        iterations = 0
        while iterations < cls.MAX_TOOL_ITERATIONS:
            iterations += 1

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=cls.REQUEST_TIMEOUT) as resp:
                    response = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8") if e.fp else ""
                raise RuntimeError(f"API Error {e.code}: {error_body}")

            candidates = response.get("candidates", [])
            if not candidates:
                return ""

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            function_calls = [p for p in parts if "functionCall" in p]

            if function_calls and use_tools:
                payload["contents"].append(content)

                function_responses = []
                for fc_part in function_calls:
                    fc = fc_part.get("functionCall", {})
                    func_name = fc.get("name", "")
                    args = fc.get("args", {})

                    try:
                        result = cls.call_mcp_tool(func_name, args)
                        if not isinstance(result, dict):
                            result = {"result": result}
                    except Exception as e:
                        result = {"error": str(e)}

                    function_responses.append({
                        "functionResponse": {
                            "name": func_name,
                            "response": result
                        }
                    })

                payload["contents"].append({
                    "role": "user",
                    "parts": function_responses
                })
                continue

            text_parts = [p.get("text", "") for p in parts if "text" in p]
            return "".join(text_parts)

        return "[Max tool iterations reached]"
    ### PROVIDER API CALLS END

    ### MESSAGE BUILDING START
    @classmethod
    def _build_messages(cls, chat_id: int) -> list:
        messages = []
        system_prompt = cls._get_system_prompt(chat_id)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        with cls._lock:
            chat_messages = cls._chats.get(chat_id, {}).get("messages", [])
            for m in chat_messages:
                messages.append({"role": m["role"], "content": m["content"]})

        return messages

    @classmethod
    def _build_messages_anthropic(cls, chat_id: int) -> list:
        messages = []
        with cls._lock:
            chat_messages = cls._chats.get(chat_id, {}).get("messages", [])
            for m in chat_messages:
                messages.append({"role": m["role"], "content": m["content"]})
        return messages

    @classmethod
    def _build_messages_gemini(cls, chat_id: int) -> list:
        contents = []
        role_map = {"user": "user", "assistant": "model"}

        with cls._lock:
            chat_messages = cls._chats.get(chat_id, {}).get("messages", [])
            for m in chat_messages:
                role = role_map.get(m["role"], "user")
                contents.append({
                    "role": role,
                    "parts": [{"text": m["content"]}]
                })

        return contents

    @classmethod
    def _get_system_prompt(cls, chat_id: int) -> str:
        with cls._lock:
            chat = cls._chats.get(chat_id, {})
            return chat.get("system_prompt", cls.SYSTEM_PROMPT)
    ### MESSAGE BUILDING END

    ### TOOL SCHEMA CONVERSION START
    @classmethod
    def _get_anthropic_tools_schema(cls) -> list:
        tools = []
        with cls._mcp_lock:
            for name, tool_info in cls._mcp_tools.items():
                tools.append({
                    "name": name,
                    "description": tool_info.get("description", ""),
                    "input_schema": tool_info.get("inputSchema", {"type": "object", "properties": {}})
                })
        return tools

    @classmethod
    def _get_gemini_tools_schema(cls) -> list:
        function_declarations = []
        with cls._mcp_lock:
            for name, tool_info in cls._mcp_tools.items():
                schema = tool_info.get("inputSchema", {"type": "object", "properties": {}})
                function_declarations.append({
                    "name": name,
                    "description": tool_info.get("description", ""),
                    "parameters": schema
                })
        return [{"functionDeclarations": function_declarations}] if function_declarations else []
    ### TOOL SCHEMA CONVERSION END

    ### MCP SERVER MANAGEMENT START
    @classmethod
    def _start_mcp_server(cls, name: str):
        config = cls._mcp_servers.get(name)
        if not config:
            return

        command = config.get("command", "")
        args = config.get("args", [])
        env = config.get("env", {})

        full_cmd = [command] + args

        proc_env = os.environ.copy()
        proc_env.update(env)

        try:
            proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=proc_env,
                bufsize=0
            )
            cls._mcp_processes[name] = proc

            cls._mcp_initialize(name)
            cls._mcp_discover_tools(name)

        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server '{name}': {e}")

    @classmethod
    def _mcp_initialize(cls, server_name: str):
        proc = cls._mcp_processes.get(server_name)
        if not proc:
            return

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "sylriekit-llm",
                    "version": "1.0.0"
                }
            }
        }

        response = cls._mcp_send_request(server_name, request)

        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        cls._mcp_send_notification(server_name, notification)

    @classmethod
    def _sanitize_server_name(cls, name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)

    @classmethod
    def _mcp_discover_tools(cls, server_name: str):
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        response = cls._mcp_send_request(server_name, request)

        if response and "result" in response:
            tools = response["result"].get("tools", [])
            for tool in tools:
                tool_name = tool.get("name", "")
                if tool_name:
                    conflict_found = False
                    existing_conflict_key = None

                    for key, info in cls._mcp_tools.items():
                        if info.get("original_name") == tool_name:
                            conflict_found = True
                            existing_conflict_key = key
                            break

                    tool_info = {
                        "server": server_name,
                        "original_name": tool_name,
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {"type": "object", "properties": {}})
                    }

                    if conflict_found:
                        if existing_conflict_key == tool_name:
                            # Rename existing tool to namespaced version
                            existing_info = cls._mcp_tools.pop(existing_conflict_key)
                            existing_server = existing_info["server"]
                            sanitized_existing = cls._sanitize_server_name(existing_server)
                            new_key = f"{sanitized_existing}__{tool_name}"
                            cls._mcp_tools[new_key] = existing_info

                        sanitized_server = cls._sanitize_server_name(server_name)
                        unique_name = f"{sanitized_server}__{tool_name}"
                        cls._mcp_tools[unique_name] = tool_info
                    else:
                        cls._mcp_tools[tool_name] = tool_info

    @classmethod
    def _invoke_mcp_tool(cls, server_name: str, tool_name: str, arguments: dict) -> Any:
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = cls._mcp_send_request(server_name, request)

        if response and "result" in response:
            content = response["result"].get("content", [])
            texts = []
            for item in content:
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
            return "\n".join(texts) if texts else response["result"]
        elif response and "error" in response:
            error = response["error"]
            raise RuntimeError(f"MCP tool error: {error.get('message', 'Unknown error')}")

        return None

    @classmethod
    def _mcp_send_request(cls, server_name: str, request: dict) -> Optional[dict]:
        proc = cls._mcp_processes.get(server_name)
        if not proc or proc.poll() is not None:
            raise RuntimeError(f"MCP server '{server_name}' is not running")

        try:
            request_str = json.dumps(request) + "\n"
            proc.stdin.write(request_str.encode("utf-8"))
            proc.stdin.flush()

            response_line = proc.stdout.readline()
            if response_line:
                return json.loads(response_line.decode("utf-8"))
            return None
        except Exception as e:
            raise RuntimeError(f"MCP communication error: {e}")

    @classmethod
    def _mcp_send_notification(cls, server_name: str, notification: dict):
        proc = cls._mcp_processes.get(server_name)
        if not proc or proc.poll() is not None:
            return

        try:
            notification_str = json.dumps(notification) + "\n"
            proc.stdin.write(notification_str.encode("utf-8"))
            proc.stdin.flush()
        except Exception:
            pass
    ### MCP SERVER MANAGEMENT END

    ### CHAT PERSISTENCE START
    @classmethod
    def _storage_path(cls) -> str:
        return os.path.join(cls.CHAT_STORAGE_DIR, cls.CHAT_STORAGE_FILENAME)

    @classmethod
    def _load_chats(cls):
        path = cls._storage_path()
        if not os.path.exists(path):
            return

        with cls._lock:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cls._chats = {int(k): v for k, v in data.items()}
            except Exception:
                cls._chats = {}

    @classmethod
    def _save_chats(cls):
        os.makedirs(cls.CHAT_STORAGE_DIR, exist_ok=True)
        path = cls._storage_path()

        try:
            data = {str(k): v for k, v in cls._chats.items()}
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            pass

    @classmethod
    def _ensure_chat_exists(cls, chat_id: int):
        cls._load_chats()
        with cls._lock:
            if chat_id not in cls._chats:
                cls._chats[chat_id] = {
                    "messages": [],
                    "system_prompt": None,
                    "created_at": time.time()
                }
                cls._save_chats()
    ### CHAT PERSISTENCE END

