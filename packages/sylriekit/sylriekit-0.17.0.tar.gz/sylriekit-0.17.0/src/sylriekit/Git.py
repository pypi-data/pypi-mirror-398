import subprocess
from typing import List, Optional

class Git:
    GIT_EXECUTABLE = "git"

    REPO_PATH = "."
    DEFAULT_TIMEOUT = 60

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config["api_key"]
        env_variables = config["env"]
        if "Git" in config.keys():
            tool_config = config["Git"]
            cls.REPO_PATH = tool_config.get("REPO_PATH", cls.REPO_PATH)
            cls.DEFAULT_TIMEOUT = tool_config.get("DEFAULT_TIMEOUT", cls.DEFAULT_TIMEOUT)

    @classmethod
    def init(cls) -> str:
        return cls._run_command(["init"])

    @classmethod
    def status(cls) -> str:
        return cls._run_command(["status"])

    @classmethod
    def add(cls, files: List[str]) -> str:
        return cls._run_command(["add"] + files)

    @classmethod
    def commit(cls, message: str) -> str:
        return cls._run_command(["commit", "-m", message])

    @classmethod
    def push(cls, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> str:
        args = ["push", remote]
        if branch:
            args.append(branch)
        if force:
            args.append("--force")
        return cls._run_command(args)

    @classmethod
    def pull(cls, remote: str = "origin", branch: Optional[str] = None) -> str:
        args = ["pull", remote]
        if branch:
            args.append(branch)
        return cls._run_command(args)

    @classmethod
    def create_branch(cls, branch_name: str) -> str:
        return cls._run_command(["branch", branch_name])

    @classmethod
    def delete_branch(cls, branch_name: str, force: bool = False) -> str:
        arg = "-D" if force else "-d"
        return cls._run_command(["branch", arg, branch_name])

    @classmethod
    def checkout(cls, branch_name: str, create_new: bool = False) -> str:
        args = ["checkout"]
        if create_new:
            args.append("-b")
        args.append(branch_name)
        return cls._run_command(args)

    @classmethod
    def list_branches(cls) -> str:
        return cls._run_command(["branch", "--list"])

    @classmethod
    def rollback(cls, count: int = 1, hard: bool = True) -> str:
        args = ["reset"]
        if hard:
            args.append("--hard")
        else:
            args.append("--soft")
        args.append(f"HEAD~{count}")
        return cls._run_command(args)

    @classmethod
    def log(cls, limit: int = 10) -> str:
        return cls._run_command(["log", "-n", str(limit), "--oneline"])

    ### PRIVATE UTILITIES START
    @classmethod
    def _run_command(cls, args: List[str]) -> str:
        try:
            command = [cls.GIT_EXECUTABLE] + args
            result = subprocess.run(
                command,
                cwd=cls.REPO_PATH,
                capture_output=True,
                text=True,
                timeout=cls.DEFAULT_TIMEOUT
            )
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            return result.stdout.strip()
        except Exception as e:
            return f"Exception: {str(e)}"
    ### PRIVATE UTILITIES END