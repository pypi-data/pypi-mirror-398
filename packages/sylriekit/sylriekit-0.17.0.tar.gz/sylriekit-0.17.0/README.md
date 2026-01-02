## Sylriekit
A personal toolset I made for myself to speed up the creation of some random personal projects.

**Warning**: This is a personal project and may contain bugs or incomplete features. It is mainly coded for convenience over optimization. Use at your own risk.

---
## Tools
+ ### PHP-like tools:
  #### Constants
  - Immutable constants manager. Define values that cannot be modified or deleted after creation.
  #### InlinePython:
  - Python renderer for inline code blocks in files. (similar to php with `<?py ... ?>`)

+ ### AI-related tools:
  #### LLM
  - LLM API client supports OpenAI, Anthropic, xAI, and Gemini. Handles chat sessions, tool calling, and MCP server integration.
  #### MCP
  - A simple FastAPI extension/wrapper. Adds some logging and error handling built-in tools for convenience. 

+ ### Execution and Automation:
  #### LimitedScript
  - Executes Python scripts in a partially sandboxed environment with restricted builtins and controlled access to tools/classes.
  #### Schedule
  - Scheduler for interval, daily, and file-watch tasks with registry management.
  #### Process
  - Subprocess wrapper for running commands with configurable timeouts, environment, shell usage, and output trimming while returning structured results.

+ ### Development Support:
  #### Log
  - Simple logging tool with Log.log(...) or automatic logging with decorators for functions.
  #### Cache
  - A simple function-based cache using decorators.
  #### Profile
  - Timing and profiling helper with context managers, decorators, and direct measurements plus optional memory tracking and stored records.

+ ### Web and GUI:
  #### Website
  - Flask web server with Gunicorn support. Features `<python>` tag rendering, function caching with JS bridge, session management, and API endpoints. Uses Redis for cross-worker session/rate-limit storage.
  #### Window
  - Desktop GUI applications using webviewpy. Supports HTML/CSS/JS with `<python>` tags for defining Python functions callable from JavaScript. Enables hybrid desktop apps with web technologies.
  #### SharedStore
  - Redis-backed storage for cross-worker data sharing. Handles sessions, rate limiting, and function caching. Used internally by Website but can be used standalone.

+ ### Other Tools:
  #### Files
  - File system utilities with searching, reading, editing, directory operations, grep, etc.
  #### API
  - HTTP request helper with configurable presets for headers, endpoints, API keys, and quick call execution returning structured responses.
  #### Git
  - Local git wrapper for managing repositories, branches, commits, and remotes.
  #### Security
  - Cryptography helper for RSA/Symmetric encryption, hashing, and JWT management.
  #### Database
  - Unified interface for interacting with SQLite, PostgreSQL, MySQL, and DynamoDB.

---

## Config
Each tool has class-level defaults that can be overridden via `load_config()`. Pass a dictionary/JSON where keys are tool names and values are dictionaries of settings (Settings/Variables not provided will use the tool's built-in defaults.)

Example config structure:
```
{
  "Files": {
    "MAX_DEPTH_DEFAULT": 42,
    "PATH_SEP": "/"
  }
}
``` 
using `sylriekit.load_config(config:dict)` will load the config for all tools, to centeralize the configuration of multiple tools.

and using `sylriekit.generate_default_config(file_name: str, include_tools="*")` will generate a file that will contain all (or just selected ones with `include_tools=["ToolName1", ...]`) of the configurable values and their defaults.


---

#### Other Stuff
- `sylriekit.tool_functions(tool_name: str) -> list[str]`: Returns all public functions available in a tool.
- `sylriekit.get_code(tool_name: str, function_name: str) -> str`: Returns the source code of a specific tool's function. Use `"*"` as the function name to get the entire source code of the tool.
- `sylriekit.help()`: Prints a short message for how to use the sylriekit's help-related functions.

---

### Change Log:
**0.17.0**:
 - Created a Window tool for creating GUI applications using webviewpy as a base and html/css/js + custom <python> tags for python code execution.
 - Updated the InlinePython tool to support <python> blocks and added dynamic cache for functions (mostly for the Website tools to use).
 - Created a SharedStore tool as a helper for the Website tool, that uses redis for persistent storage.
 - Updated the Website tool to support the <python> blocks and use a custom caching system + api for dynamic content.

**0.15.9**:
 - Tested on linux platforms.
 - Added OpenRouter support for the LLM tool.

**0.15.8**:
 - Added remote_addr for IP address tracking in the Website tool.
 - Fixed the toml to correctly list dependencies.


**Previous change log entries are visible in the description of older versions**