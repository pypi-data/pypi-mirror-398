import os
import re
import shutil
from collections import deque

from sylriekit.Constants import Constants


_FILES_PROTECTED_ATTRS = {
    "CWD", "PATH_SEP", "USE_WHITELIST", "BLACKLISTED_DIRECTORIES",
    "WHITELISTED_DIRECTORIES", "FORCED_DIRECTORY", "MAX_DEPTH_DEFAULT",
    "MAX_FILES_DEFAULT", "MIN_FILES", "HIDDEN_PREFIX"
}

class Files(metaclass=Constants.protect_class_meta(_FILES_PROTECTED_ATTRS, "FILES_CONFIG_LOCKED")):
    START_DEPTH = 0
    EMPTY_SIZE = 0

    HIDDEN_PREFIX = '.'
    CWD = os.getcwd()
    PATH_SEP = os.sep
    USE_WHITELIST = False
    BLACKLISTED_DIRECTORIES = []
    WHITELISTED_DIRECTORIES = []
    FORCED_DIRECTORY = None
    MAX_DEPTH_DEFAULT = 10
    MAX_FILES_DEFAULT = 100
    MIN_FILES = 1

    @classmethod
    def load_config(cls, config:dict):
        cls._check_config_lock()
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Files" in config.keys():
            config = config["Files"]
            cls.CWD = config.get("CWD", cls.CWD)
            cls.PATH_SEP = config.get("PATH_SEP", cls.PATH_SEP)
            cls.HIDDEN_PREFIX = config.get("HIDDEN_PREFIX", cls.HIDDEN_PREFIX)
            cls.FORCED_DIRECTORY = config.get("FORCED_DIRECTORY", cls.FORCED_DIRECTORY)
            cls.BLACKLISTED_DIRECTORIES = config.get("BLACKLISTED_DIRECTORIES", cls.BLACKLISTED_DIRECTORIES)
            cls.WHITELISTED_DIRECTORIES = config.get("WHITELISTED_DIRECTORIES", cls.WHITELISTED_DIRECTORIES)
            cls.MAX_DEPTH_DEFAULT = config.get("MAX_DEPTH_DEFAULT", cls.MAX_DEPTH_DEFAULT)
            cls.MAX_FILES_DEFAULT = config.get("MAX_FILES_DEFAULT", cls.MAX_FILES_DEFAULT)
            cls.MIN_FILES = config.get("MIN_FILES", cls.MIN_FILES)
            if cls.FORCED_DIRECTORY is not None:
                cls.FORCED_DIRECTORY = cls._normalize_path(cls.FORCED_DIRECTORY, is_file=False)
                cls.USE_WHITELIST = True
                cls.WHITELISTED_DIRECTORIES.append(cls.FORCED_DIRECTORY)
            else:
                cls.USE_WHITELIST = config.get("USE_WHITELIST", cls.USE_WHITELIST)

    @classmethod
    def lock_config(cls, permanent: bool = True):
        cls._check_config_lock()
        cls.BLACKLISTED_DIRECTORIES = tuple(cls.BLACKLISTED_DIRECTORIES)
        cls.WHITELISTED_DIRECTORIES = tuple(cls.WHITELISTED_DIRECTORIES)
        Constants.define("FILES_CONFIG_LOCKED", True)

    @classmethod
    def describe(cls, path, recursive:bool=False, max_depth:int=None, max_files:int=None, include_hidden:bool=False, verbose:bool=False):
        target = cls._normalize_path(path, is_file=False)
        depth_limit = max_depth if max_depth is not None else cls.MAX_DEPTH_DEFAULT
        file_limit = max_files if max_files is not None else cls.MAX_FILES_DEFAULT
        if file_limit < cls.MIN_FILES:
            raise ValueError("max_files must be positive")
        counter = cls.START_DEPTH
        allow_hidden = include_hidden
        recursive_scan = recursive

        def hidden(name):
            return name.startswith(cls.HIDDEN_PREFIX)

        def build_entry(current_path):
            name = os.path.basename(current_path) or current_path
            entry = {"name": name}
            is_dir = os.path.isdir(current_path)
            if is_dir:
                entry["children"] = []
            if verbose:
                try:
                    size = os.path.getsize(current_path)
                except OSError:
                    size = cls.EMPTY_SIZE
                entry.update({
                    "path": current_path,
                    "type": "directory" if is_dir else "file",
                    "size": size
                })
            return entry, is_dir

        root_entry, root_is_dir = build_entry(target)
        counter += 1
        if not root_is_dir:
            return root_entry
        queue = deque()
        queue.append((target, cls.START_DEPTH, root_entry))
        while queue and counter < file_limit:
            current_path, depth, node = queue.popleft()
            if depth >= depth_limit:
                continue
            traverse_children = recursive_scan or depth == cls.START_DEPTH
            if "children" not in node or not traverse_children:
                continue
            try:
                entries = sorted(os.listdir(current_path))
            except OSError:
                node["children"] = []
                continue
            for child in entries:
                if counter >= file_limit:
                    break
                if not allow_hidden and hidden(child):
                    continue
                child_path = os.path.join(current_path, child)
                is_dir = os.path.isdir(child_path)
                if is_dir and cls._is_blocked(child_path):
                    continue
                child_entry, child_is_dir = build_entry(child_path)
                node["children"].append(child_entry)
                counter += 1
                if child_is_dir and (recursive_scan or depth + 1 == cls.START_DEPTH) and counter < file_limit:
                    queue.append((child_path, depth + 1, child_entry))
        return root_entry

    ### GENERAL UTIL START
    @classmethod
    def use_whitelist(cls, use_whitelist:bool=True) -> bool:
        cls._check_config_lock()
        cls.USE_WHITELIST = use_whitelist
        return cls.USE_WHITELIST

    @classmethod
    def update_blacklist(cls, blacklist: list, append: bool=True) -> list:
        cls._check_config_lock()
        entries = blacklist.copy()
        if append:
            cls.BLACKLISTED_DIRECTORIES.extend(entries)
        else:
            cls.BLACKLISTED_DIRECTORIES = entries
        return cls.BLACKLISTED_DIRECTORIES

    @classmethod
    def update_whitelist(cls, blacklist: list, append: bool=True) -> list:
        cls._check_config_lock()
        entries = blacklist.copy()
        if append:
            cls.WHITELISTED_DIRECTORIES.extend(entries)
        else:
            cls.WHITELISTED_DIRECTORIES = entries
        return cls.WHITELISTED_DIRECTORIES
    ### GENERAL UTIL END

    ### SIMPLE FILE ACTIONS START
    @staticmethod
    def exists(file_path):
        return os.path.isfile(file_path)

    @classmethod
    def read(cls,file_path):
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def write(cls, file_path, data:str=""):
        file_path = cls._normalize_path(file_path, is_file=True, must_exist=False)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data)

    @classmethod
    def create(cls, file_path, data:str=""):
        file_path = cls._normalize_path(file_path, is_file=True, must_exist=False)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data)

    @classmethod
    def mkdir(cls, file_path):
        os.makedirs(file_path, exist_ok=True)

    @classmethod
    def append(cls,file_path, data:str=""):
        file_path = cls._normalize_path(file_path, is_file=True, must_exist=False)
        f = open(file_path, "a")
        f.write(data)

    @classmethod
    def rename(cls, file_path, new_name: str) -> str:
        file_path = cls._normalize_path(file_path, is_file=True)
        directory = os.path.dirname(file_path)
        new_path = os.path.join(directory, new_name)
        os.rename(file_path, new_path)
        return new_path

    @classmethod
    def move_to(cls, file_path, destination: str) -> str:
        file_path = cls._normalize_path(file_path, is_file=True)
        if os.path.isdir(destination):
            new_path = os.path.join(destination, os.path.basename(file_path))
        else:
            new_path = destination
        shutil.move(file_path, new_path)
        return new_path

    @classmethod
    def copy(cls, file_path, destination: str) -> str:
        file_path = cls._normalize_path(file_path, is_file=True)
        if os.path.isdir(destination):
            new_path = os.path.join(destination, os.path.basename(file_path))
        else:
            new_path = destination
        shutil.copy2(file_path, new_path)
        return new_path

    @classmethod
    def copy_directory(cls, source_path, destination: str) -> str:
        source_path = cls._normalize_path(source_path, is_file=False)
        shutil.copytree(source_path, destination)
        return destination

    @classmethod
    def delete(cls, file_path):
        file_path = cls._normalize_path(file_path, is_file=True)
        os.remove(file_path)

    @classmethod
    def delete_directory(cls, directory_path, recursive: bool = False):
        directory_path = cls._normalize_path(directory_path, is_file=False)
        if recursive:
            shutil.rmtree(directory_path)
        else:
            os.rmdir(directory_path)

    @classmethod
    def file_details(cls, file_path) -> dict:
        file_path = cls._normalize_path(file_path, is_file=True)
        stat_info = os.stat(file_path)
        with open(file_path, "r") as f:
            line_count = sum(1 for _ in f)
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat_info.st_size,
            "line_count": line_count,
            "created": stat_info.st_ctime,
            "modified": stat_info.st_mtime,
            "accessed": stat_info.st_atime,
            "extension": os.path.splitext(file_path)[1],
            "is_hidden": os.path.basename(file_path).startswith(cls.HIDDEN_PREFIX)
        }
    ### SIMPLE FILE ACTIONS END

    ### LINE-BASED EDITING START
    @classmethod
    def read_lines(cls, file_path, line_start: int = None, line_end: int = None) -> list:
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            lines = f.readlines()

        start_idx = (line_start - 1) if line_start is not None else 0
        end_idx = line_end if line_end is not None else len(lines)

        if start_idx < 0:
            raise ValueError("line_start must be positive")
        if end_idx > len(lines):
            end_idx = len(lines)
        if start_idx > end_idx:
            raise ValueError("line_start cannot be greater than line_end")

        return lines[start_idx:end_idx]

    @classmethod
    def get_line(cls, file_path, line_number: int) -> str:
        lines = cls.read_lines(file_path, line_number, line_number)
        return lines[0] if lines else ""

    @classmethod
    def head(cls, file_path, lines: int = 10) -> list:
        return cls.read_lines(file_path, 1, lines)

    @classmethod
    def tail(cls, file_path, lines: int = 10) -> list:
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            all_lines = f.readlines()
        if lines >= len(all_lines):
            return all_lines
        return all_lines[-lines:]

    @classmethod
    def line_count(cls, file_path) -> int:
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            return sum(1 for _ in f)

    @classmethod
    def insert_at_line(cls, file_path, line_number: int, insert_value: str):
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            lines = f.readlines()

        if line_number < 1:
            raise ValueError("line_number must be positive")

        insert_idx = line_number - 1
        if insert_idx > len(lines):
            insert_idx = len(lines)

        if not insert_value.endswith('\n'):
            insert_value += '\n'

        lines.insert(insert_idx, insert_value)

        with open(file_path, "w") as f:
            f.writelines(lines)

    @classmethod
    def remove_lines(cls, file_path, line_start: int, line_end: int = None):
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            lines = f.readlines()

        if line_start < 1:
            raise ValueError("line_start must be positive")

        if line_end is None:
            line_end = line_start

        if line_end < line_start:
            raise ValueError("line_end cannot be less than line_start")

        start_idx = line_start - 1
        end_idx = line_end

        if start_idx >= len(lines):
            return  # Nothing to remove

        del lines[start_idx:end_idx]

        with open(file_path, "w") as f:
            f.writelines(lines)

    @classmethod
    def replace_line(cls, file_path, line_number: int, new_value: str):
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            lines = f.readlines()

        if line_number < 1:
            raise ValueError("line_number must be positive")
        if line_number > len(lines):
            raise IndexError(f"Line {line_number} does not exist in file")

        if not new_value.endswith('\n'):
            new_value += '\n'

        lines[line_number - 1] = new_value

        with open(file_path, "w") as f:
            f.writelines(lines)

    @classmethod
    def replace_lines(cls, file_path, line_start: int, line_end: int, new_content: str):
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            lines = f.readlines()

        if line_start < 1:
            raise ValueError("line_start must be positive")
        if line_end < line_start:
            raise ValueError("line_end cannot be less than line_start")
        if line_start > len(lines):
            raise IndexError(f"Line {line_start} does not exist in file")

        start_idx = line_start - 1
        end_idx = min(line_end, len(lines))

        if not new_content.endswith('\n'):
            new_content += '\n'

        new_lines = new_content.splitlines(keepends=True)

        lines[start_idx:end_idx] = new_lines

        with open(file_path, "w") as f:
            f.writelines(lines)

    @classmethod
    def append_line(cls, file_path, line_value: str):
        file_path = cls._normalize_path(file_path, is_file=True)

        with open(file_path, "a") as f:
            if not line_value.startswith('\n'):
                f.write('\n')
            f.write(line_value)
            if not line_value.endswith('\n'):
                f.write('\n')

    @classmethod
    def prepend_line(cls, file_path, line_value: str):
        cls.insert_at_line(file_path, 1, line_value)

    @classmethod
    def find_line(cls, file_path, search_text: str, start_line: int = 1) -> int:
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines[start_line - 1:], start=start_line):
            if search_text in line:
                return i
        return -1

    @classmethod
    def find_all_lines(cls, file_path, search_text: str) -> list:
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            lines = f.readlines()

        return [i + 1 for i, line in enumerate(lines) if search_text in line]
    ### LINE-BASED EDITING END

    ### SEARCH-BASED EDITING START
    @classmethod
    def search(cls, file_path, pattern: str, is_regex: bool = False) -> list:
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            content = f.read()

        results = []
        lines = content.splitlines(keepends=True)

        if is_regex:
            compiled = re.compile(pattern)
            for i, line in enumerate(lines):
                matches = list(compiled.finditer(line))
                if matches:
                    results.append({
                        "line_number": i + 1,
                        "line": line.rstrip('\n'),
                        "matches": [{"start": m.start(), "end": m.end(), "text": m.group()} for m in matches]
                    })
        else:
            for i, line in enumerate(lines):
                if pattern in line:
                    results.append({
                        "line_number": i + 1,
                        "line": line.rstrip('\n'),
                        "matches": [{"start": line.find(pattern), "end": line.find(pattern) + len(pattern), "text": pattern}]
                    })

        return results

    @classmethod
    def search_replace(cls, file_path, pattern: str, replacement: str, is_regex: bool = False, count: int = 0) -> int:
        file_path = cls._normalize_path(file_path, is_file=True)
        with open(file_path, "r") as f:
            content = f.read()

        if is_regex:
            new_content, replacements = re.subn(pattern, replacement, content, count=count)
        else:
            if count == 0:
                new_content = content.replace(pattern, replacement)
                replacements = content.count(pattern)
            else:
                new_content = content.replace(pattern, replacement, count)
                replacements = min(content.count(pattern), count)

        with open(file_path, "w") as f:
            f.write(new_content)

        return replacements

    @classmethod
    def search_directory(cls, path, pattern: str, is_regex: bool = False, max_depth: int = None, max_files: int = None, include_hidden: bool = False, file_pattern: str = None) -> list:
        target = cls._normalize_path(path, is_file=False)
        depth_limit = max_depth if max_depth is not None else cls.MAX_DEPTH_DEFAULT
        file_limit = max_files if max_files is not None else cls.MAX_FILES_DEFAULT

        if file_limit < cls.MIN_FILES:
            raise ValueError("max_files must be positive")

        results = []
        files_checked = cls.START_DEPTH

        file_regex = re.compile(file_pattern) if file_pattern else None

        queue = deque()
        queue.append((target, cls.START_DEPTH))

        while queue and files_checked < file_limit:
            current_path, depth = queue.popleft()

            if depth > depth_limit:
                continue

            try:
                entries = sorted(os.listdir(current_path))
            except OSError:
                continue

            for entry in entries:
                if files_checked >= file_limit:
                    break

                if not include_hidden and entry.startswith(cls.HIDDEN_PREFIX):
                    continue

                entry_path = os.path.join(current_path, entry)

                if os.path.isdir(entry_path):
                    if not cls._is_blocked(entry_path):
                        queue.append((entry_path, depth + 1))
                elif os.path.isfile(entry_path):
                    if file_regex and not file_regex.search(entry):
                        continue

                    files_checked += 1
                    try:
                        matches = cls.search(entry_path, pattern, is_regex)
                        if matches:
                            results.append({
                                "file": entry_path,
                                "matches": matches
                            })
                    except (OSError, UnicodeDecodeError):
                        continue

        return results

    @classmethod
    def replace_in_directory(cls, path, pattern: str, replacement: str, is_regex: bool = False, max_depth: int = None, max_files: int = None, include_hidden: bool = False, file_pattern: str = None) -> dict:
        target = cls._normalize_path(path, is_file=False)
        depth_limit = max_depth if max_depth is not None else cls.MAX_DEPTH_DEFAULT
        file_limit = max_files if max_files is not None else cls.MAX_FILES_DEFAULT

        if file_limit < cls.MIN_FILES:
            raise ValueError("max_files must be positive")

        results = {
            "files_modified": 0,
            "total_replacements": 0,
            "files": []
        }
        files_checked = cls.START_DEPTH

        file_regex = re.compile(file_pattern) if file_pattern else None

        queue = deque()
        queue.append((target, cls.START_DEPTH))

        while queue and files_checked < file_limit:
            current_path, depth = queue.popleft()

            if depth > depth_limit:
                continue

            try:
                entries = sorted(os.listdir(current_path))
            except OSError:
                continue

            for entry in entries:
                if files_checked >= file_limit:
                    break

                if not include_hidden and entry.startswith(cls.HIDDEN_PREFIX):
                    continue

                entry_path = os.path.join(current_path, entry)

                if os.path.isdir(entry_path):
                    if not cls._is_blocked(entry_path):
                        queue.append((entry_path, depth + 1))
                elif os.path.isfile(entry_path):
                    if file_regex and not file_regex.search(entry):
                        continue

                    files_checked += 1
                    try:
                        replacements = cls.search_replace(entry_path, pattern, replacement, is_regex)
                        if replacements > 0:
                            results["files_modified"] += 1
                            results["total_replacements"] += replacements
                            results["files"].append({
                                "file": entry_path,
                                "replacements": replacements
                            })
                    except (OSError, UnicodeDecodeError):
                        continue

        return results

    @classmethod
    def find_files(cls, path, file_pattern: str, is_regex: bool = True, max_depth: int = None, max_files: int = None, include_hidden: bool = False) -> list:
        target = cls._normalize_path(path, is_file=False)
        depth_limit = max_depth if max_depth is not None else cls.MAX_DEPTH_DEFAULT
        file_limit = max_files if max_files is not None else cls.MAX_FILES_DEFAULT

        if file_limit < cls.MIN_FILES:
            raise ValueError("max_files must be positive")

        results = []
        files_checked = cls.START_DEPTH

        if is_regex:
            file_regex_pattern = re.compile(file_pattern)
        else:
            file_regex_pattern = None

        queue = deque()
        queue.append((target, cls.START_DEPTH))

        while queue and files_checked < file_limit:
            current_path, depth = queue.popleft()

            if depth > depth_limit:
                continue

            try:
                entries = sorted(os.listdir(current_path))
            except OSError:
                continue

            for entry in entries:
                if files_checked >= file_limit:
                    break

                if not include_hidden and entry.startswith(cls.HIDDEN_PREFIX):
                    continue

                entry_path = os.path.join(current_path, entry)

                if os.path.isdir(entry_path):
                    if not cls._is_blocked(entry_path):
                        queue.append((entry_path, depth + 1))
                else:
                    files_checked += 1
                    if is_regex:
                        if file_regex_pattern.search(entry):
                            results.append(entry_path)
                    else:
                        if file_pattern in entry:
                            results.append(entry_path)

        return results

    @classmethod
    def grep(cls, path, pattern: str, is_regex: bool = False, max_depth: int = None, max_files: int = None, include_hidden: bool = False, file_pattern: str = None, context_lines: int = 0) -> list:
        target = cls._normalize_path(path, is_file=False)
        depth_limit = max_depth if max_depth is not None else cls.MAX_DEPTH_DEFAULT
        file_limit = max_files if max_files is not None else cls.MAX_FILES_DEFAULT

        if file_limit < cls.MIN_FILES:
            raise ValueError("max_files must be positive")

        results = []
        files_checked = cls.START_DEPTH

        file_regex = re.compile(file_pattern) if file_pattern else None
        search_regex = re.compile(pattern) if is_regex else None

        queue = deque()
        queue.append((target, cls.START_DEPTH))

        while queue and files_checked < file_limit:
            current_path, depth = queue.popleft()

            if depth > depth_limit:
                continue

            try:
                entries = sorted(os.listdir(current_path))
            except OSError:
                continue

            for entry in entries:
                if files_checked >= file_limit:
                    break

                if not include_hidden and entry.startswith(cls.HIDDEN_PREFIX):
                    continue

                entry_path = os.path.join(current_path, entry)

                if os.path.isdir(entry_path):
                    if not cls._is_blocked(entry_path):
                        queue.append((entry_path, depth + 1))
                elif os.path.isfile(entry_path):
                    if file_regex and not file_regex.search(entry):
                        continue

                    files_checked += 1
                    try:
                        with open(entry_path, "r") as f:
                            lines = f.readlines()

                        file_matches = []
                        for i, line in enumerate(lines):
                            match_found = False
                            if is_regex:
                                match_found = search_regex.search(line) is not None
                            else:
                                match_found = pattern in line

                            if match_found:
                                match_entry = {
                                    "line_number": i + 1,
                                    "line": line.rstrip('\n')
                                }

                                if context_lines > 0:
                                    start = max(0, i - context_lines)
                                    end = min(len(lines), i + context_lines + 1)
                                    match_entry["context_before"] = [l.rstrip('\n') for l in lines[start:i]]
                                    match_entry["context_after"] = [l.rstrip('\n') for l in lines[i + 1:end]]

                                file_matches.append(match_entry)

                        if file_matches:
                            results.append({
                                "file": entry_path,
                                "matches": file_matches
                            })
                    except (OSError, UnicodeDecodeError):
                        continue

        return results
    ### SEARCH-BASED EDITING END

    ### PIPELINE SEARCH START
    @classmethod
    def pipeline_search(cls, path, pattern: str, is_regex: bool = False, max_depth: int = None, max_files: int = None, include_hidden: bool = False, file_pattern: str = None) -> "_Files_SearchPipeline":
        results = cls.grep(path, pattern, is_regex, max_depth, max_files, include_hidden, file_pattern)
        return _Files_SearchPipeline(results, pattern, is_regex)
    ### PIPELINE SEARCH END


    ### PRIVATE UTILITIES START
    @classmethod
    def _check_config_lock(cls):
        if Constants.get("FILES_CONFIG_LOCKED", False):
            raise PermissionError("Config is locked and cannot be modified")

    @classmethod
    def _normalize_path(cls, path, is_file:bool=False, must_exist:bool=True) -> str:
        if not os.path.isabs(path):
            path = os.path.join(cls.CWD, path)

        if cls._is_blocked(path):
            raise PermissionError(f"Access to directory blocked: {path}")
        if is_file:
            return cls._ensure_file(path, must_exist=must_exist)
        else:
            return cls._ensure_directory(path)

    @classmethod
    def _ensure_file(cls, file_path, must_exist:bool=True) -> str:
        if must_exist and not cls.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return os.path.abspath(file_path)

    @classmethod
    def _ensure_directory(cls, directory) -> str:
        if os.path.isdir(directory):
            return directory
        elif cls.exists(directory):
            directory = os.path.dirname(directory)
            return os.path.abspath(directory)
        else:
            raise NotADirectoryError(f"Directory not found: {directory}")

    @classmethod
    def _is_blocked(cls, directory_path) -> bool:
        absolute = os.path.abspath(directory_path)

        def normalize(paths):
            normalized = []
            for value in paths:
                candidate = value if os.path.isabs(value) else os.path.join(cls.CWD, value)
                normalized.append(os.path.abspath(candidate))
            return normalized

        if cls.USE_WHITELIST:
            if not cls.WHITELISTED_DIRECTORIES:
                return True
            return absolute not in normalize(cls.WHITELISTED_DIRECTORIES)
        return absolute in normalize(cls.BLACKLISTED_DIRECTORIES)
    ### PRIVATE UTILITIES END


class _Files_SearchPipeline:
    def __init__(self, results: list, pattern: str, is_regex: bool):
        self._results = results
        self._pattern = pattern
        self._is_regex = is_regex
        self._replacement = None
        self._preview_data = None

    def filter_files(self, file_pattern: str, is_regex: bool = True) -> "_Files_SearchPipeline":
        if is_regex:
            compiled = re.compile(file_pattern)
            self._results = [r for r in self._results if compiled.search(r["file"])]
        else:
            self._results = [r for r in self._results if file_pattern in r["file"]]
        return self

    def filter_lines(self, line_pattern: str, is_regex: bool = False) -> "_Files_SearchPipeline":
        if is_regex:
            compiled = re.compile(line_pattern)
            for result in self._results:
                result["matches"] = [m for m in result["matches"] if compiled.search(m["line"])]
            self._results = [r for r in self._results if r["matches"]]
        else:
            for result in self._results:
                result["matches"] = [m for m in result["matches"] if line_pattern in m["line"]]
            self._results = [r for r in self._results if r["matches"]]
        return self

    def filter_by_line_range(self, min_line: int = None, max_line: int = None) -> "_Files_SearchPipeline":
        for result in self._results:
            filtered_matches = []
            for match in result["matches"]:
                line_num = match["line_number"]
                if min_line is not None and line_num < min_line:
                    continue
                if max_line is not None and line_num > max_line:
                    continue
                filtered_matches.append(match)
            result["matches"] = filtered_matches
        self._results = [r for r in self._results if r["matches"]]
        return self

    def exclude_files(self, file_pattern: str, is_regex: bool = True) -> "_Files_SearchPipeline":
        if is_regex:
            compiled = re.compile(file_pattern)
            self._results = [r for r in self._results if not compiled.search(r["file"])]
        else:
            self._results = [r for r in self._results if file_pattern not in r["file"]]
        return self

    def exclude_lines(self, line_pattern: str, is_regex: bool = False) -> "_Files_SearchPipeline":
        if is_regex:
            compiled = re.compile(line_pattern)
            for result in self._results:
                result["matches"] = [m for m in result["matches"] if not compiled.search(m["line"])]
            self._results = [r for r in self._results if r["matches"]]
        else:
            for result in self._results:
                result["matches"] = [m for m in result["matches"] if line_pattern not in m["line"]]
            self._results = [r for r in self._results if r["matches"]]
        return self

    def replace(self, replacement: str) -> "_Files_SearchPipeline":
        self._replacement = replacement
        self._preview_data = []

        for result in self._results:
            file_preview = {
                "file": result["file"],
                "changes": []
            }
            for match in result["matches"]:
                original_line = match["line"]
                if self._is_regex:
                    new_line = re.sub(self._pattern, replacement, original_line)
                else:
                    new_line = original_line.replace(self._pattern, replacement)

                file_preview["changes"].append({
                    "line_number": match["line_number"],
                    "original": original_line,
                    "modified": new_line
                })
            self._preview_data.append(file_preview)

        return self

    def preview(self) -> list:
        if self._preview_data is not None:
            return self._preview_data
        return self._results

    def apply(self) -> dict:
        if self._replacement is None:
            raise ValueError("No replacement set. Call replace() before apply()")

        applied = {
            "files_modified": 0,
            "total_changes": 0,
            "files": []
        }

        for file_preview in self._preview_data:
            file_path = file_preview["file"]
            changes = file_preview["changes"]

            if not changes:
                continue

            with open(file_path, "r") as f:
                lines = f.readlines()

            for change in changes:
                line_idx = change["line_number"] - 1
                if line_idx < len(lines):
                    original_ending = ""
                    if lines[line_idx].endswith('\n'):
                        original_ending = '\n'
                    lines[line_idx] = change["modified"] + original_ending

            with open(file_path, "w") as f:
                f.writelines(lines)

            applied["files_modified"] += 1
            applied["total_changes"] += len(changes)
            applied["files"].append({
                "file": file_path,
                "changes": len(changes)
            })

        return applied

    def get_results(self) -> list:
        return self._results

    def count(self) -> dict:
        total_files = len(self._results)
        total_matches = sum(len(r["matches"]) for r in self._results)
        return {
            "files": total_files,
            "matches": total_matches
        }
