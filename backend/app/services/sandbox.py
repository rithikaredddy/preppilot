"""Run student code in short-lived subprocesses on this machine.

This runner is for local development and demos. Each run gets a private
temporary directory, an environment with no secrets, CPU/file-size/process
limits, and (for Python) a guard that blocks networking, shell access, child
processes and file access outside the temporary directory. It is defence in
depth, not an isolation boundary: production deployments should set
JUDGE0_URL, and the app refuses local execution in production unless
ALLOW_LOCAL_CODE_RUNNER is set explicitly.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - Windows has no resource module
    resource = None

COMPILE_TIMEOUT_SECONDS = 20
MAX_OUTPUT_BYTES = 1024 * 1024

WRAPPER = """
import builtins
import io
import os
import socket
import sys

_ROOT = os.path.realpath(os.environ["SANDBOX_ROOT"])
_ENTRY = os.path.join(_ROOT, "main.py")


def _deny(message):
    def blocked(*args, **kwargs):
        raise PermissionError(message)
    return blocked


class _BlockedSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        raise PermissionError("Network access is disabled in the coding sandbox.")


socket.socket = _BlockedSocket
socket.create_connection = _deny("Network access is disabled in the coding sandbox.")
socket.socketpair = _deny("Network access is disabled in the coding sandbox.")


def _inside(path):
    try:
        target = os.path.realpath(os.fspath(path))
    except TypeError:
        return False
    return target == _ROOT or target.startswith(_ROOT + os.sep)


_READ_ONLY_ROOTS = tuple(
    {os.path.realpath(path) + os.sep for path in (sys.prefix, sys.base_prefix, sys.exec_prefix)}
)


def _allowed(file, mode="r"):
    # File descriptors 0-2 keep open(0).read(), a common competitive-programming idiom.
    if isinstance(file, int):
        return file in (0, 1, 2)
    if _inside(file):
        return True
    # The import system reads the standard library through the same functions.
    writing = isinstance(mode, int) or any(flag in str(mode) for flag in "wax+")
    if writing:
        return False
    try:
        target = os.path.realpath(os.fspath(file))
    except TypeError:
        return False
    return target.startswith(_READ_ONLY_ROOTS)


def _mode(args, kwargs, default="r"):
    if "mode" in kwargs:
        return kwargs["mode"]
    if "flags" in kwargs:
        return kwargs["flags"]
    return args[0] if args else default


def _guard_open(original):
    def opener(file, *args, **kwargs):
        if not _allowed(file, _mode(args, kwargs)):
            raise PermissionError("Files outside the sandbox folder are not available.")
        return original(file, *args, **kwargs)
    return opener


import _io

_real_open = builtins.open
_guarded_open = _guard_open(_real_open)
builtins.open = _guarded_open
io.open = _guarded_open
_io.open = _guarded_open


class _GuardedFileIO(_io.FileIO):
    def __init__(self, file, *args, **kwargs):
        if not _allowed(file, _mode(args, kwargs)):
            raise PermissionError("Files outside the sandbox folder are not available.")
        super().__init__(file, *args, **kwargs)


io.FileIO = _GuardedFileIO
_io.FileIO = _GuardedFileIO
_real_os_open = os.open


def _guarded_os_open(path, flags, *args, **kwargs):
    writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)
    if not _allowed(path, "w" if writing else "r"):
        raise PermissionError("Files outside the sandbox folder are not available.")
    return _real_os_open(path, flags, *args, **kwargs)


os.open = _guarded_os_open

_SHELL = "Shell, child processes and file-system changes are disabled in the coding sandbox."
_BLOCKED_OS = (
    "system", "popen", "fork", "forkpty", "kill", "killpg", "execv", "execve", "execl",
    "execle", "execlp", "execlpe", "execvp", "execvpe", "spawnl", "spawnle", "spawnlp",
    "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe", "posix_spawn", "posix_spawnp",
    "remove", "unlink", "rmdir", "removedirs", "rename", "replace", "chmod", "chown",
    "symlink", "link", "chdir",
)
import posix

for _name in _BLOCKED_OS:
    for _target in (os, posix):
        if hasattr(_target, _name):
            setattr(_target, _name, _deny(_SHELL))
posix.open = os.open


def _guard_listing(original):
    def lister(path=".", *args, **kwargs):
        if not isinstance(path, int) and not _allowed(path, "r"):
            raise PermissionError("Folders outside the sandbox folder are not available.")
        return original(path, *args, **kwargs)
    return lister


for _name in ("listdir", "scandir"):
    _guarded = _guard_listing(getattr(posix, _name))
    setattr(posix, _name, _guarded)
    setattr(os, _name, _guarded)

for _module in ("subprocess", "_posixsubprocess", "multiprocessing", "pty", "ctypes", "_ctypes"):
    sys.modules[_module] = None

with _real_open(_ENTRY, encoding="utf-8") as _handle:
    _source = _handle.read()
_code = compile(_source, "main.py", "exec")
del _handle, _source, _name, _target, _module, _guarded
sys.argv = ["main.py"]
exec(_code, {"__name__": "__main__", "__file__": "main.py", "__builtins__": builtins})
"""


def _clean_env(folder: str, extra: dict | None = None) -> dict:
    """An environment with no inherited secrets (the parent holds JWT_SECRET etc.)."""
    env = {
        "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
        "HOME": folder,
        "TMPDIR": folder,
        "LANG": "C.UTF-8",
    }
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        env["JAVA_HOME"] = java_home
    env.update(extra or {})
    return env


def _limits(cpu_seconds: int, max_processes: int | None = None):
    """Return a preexec_fn that applies resource limits inside the child process."""
    if resource is None:
        return None

    def apply() -> None:
        os.setsid()
        for name, value in (
            ("RLIMIT_CPU", (cpu_seconds, cpu_seconds + 1)),
            ("RLIMIT_FSIZE", (10 * 1024 * 1024, 10 * 1024 * 1024)),
            ("RLIMIT_CORE", (0, 0)),
        ):
            try:
                resource.setrlimit(getattr(resource, name), value)
            except (ValueError, OSError, AttributeError):
                pass
        if max_processes is not None and sys.platform.startswith("linux"):
            try:
                resource.setrlimit(resource.RLIMIT_NPROC, (max_processes, max_processes))
            except (ValueError, OSError):
                pass

    return apply


def run_python(source_code: str, stdin: str, time_limit_ms: int, memory_limit_kb: int) -> dict:
    timeout = min(max(time_limit_ms / 1000, 0.4), 5)
    with tempfile.TemporaryDirectory(prefix="code-sandbox-") as folder:
        root = Path(folder)
        (root / "main.py").write_text(source_code, encoding="utf-8")
        (root / "runner.py").write_text(WRAPPER, encoding="utf-8")
        env = _clean_env(
            folder,
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
                "PYTHONSAFEPATH": "1",
                "SANDBOX_ROOT": folder,
            },
        )
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-B", str(root / "runner.py")],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=folder,
                env=env,
                check=False,
                preexec_fn=_limits(int(timeout) + 1, max_processes=1),
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "time_limit",
                "stdout": "",
                "stderr": "Time limit exceeded.",
                "time_ms": int(timeout * 1000),
                "memory_kb": None,
            }
        stderr = (completed.stderr or "")[:4000]
        status = "accepted" if completed.returncode == 0 else "runtime_error"
        if "MemoryError" in stderr:
            status = "runtime_error"
        return {
            "status": status,
            "stdout": (completed.stdout or "")[:MAX_OUTPUT_BYTES],
            "stderr": stderr,
            "time_ms": None,
            "memory_kb": memory_limit_kb,
        }


def run_local(source_code: str, language: str, stdin: str, time_limit_ms: int, memory_limit_kb: int) -> dict:
    if language == "python":
        return run_python(source_code, stdin, time_limit_ms, memory_limit_kb)
    if language == "java":
        return _compile_and_run(
            source_code,
            "Main.java",
            ["javac", "Main.java"],
            ["java", "Main"],
            stdin,
            time_limit_ms,
            memory_limit_kb,
        )
    if language == "cpp":
        return _compile_and_run(
            source_code,
            "main.cpp",
            ["g++", "-std=c++17", "-O0", "-o", "main", "main.cpp"],
            ["./main"],
            stdin,
            time_limit_ms,
            memory_limit_kb,
        )
    return {
        "status": "error",
        "stdout": "",
        "stderr": "Choose Python, Java, or C++.",
        "time_ms": None,
        "memory_kb": None,
    }


def _compile_and_run(source, filename, compile_cmd, run_cmd, stdin, time_limit_ms, memory_limit_kb) -> dict:
    # The run limit applies to the program only. Compiling (and JVM start-up for
    # Java) gets its own budget so a correct solution is not marked time_limit.
    timeout = min(max(time_limit_ms / 1000, 1), 8)
    if compile_cmd[0] == "javac":
        timeout += 2
    with tempfile.TemporaryDirectory(prefix="code-sandbox-") as folder:
        (Path(folder) / filename).write_text(source, encoding="utf-8")
        env = _clean_env(folder)
        try:
            compiled = subprocess.run(
                compile_cmd,
                cwd=folder,
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT_SECONDS,
                env=env,
                check=False,
            )
        except FileNotFoundError:
            return _missing_compiler(compile_cmd[0])
        except subprocess.TimeoutExpired:
            return {
                "status": "compilation_error",
                "stdout": "",
                "stderr": "Compilation took too long.",
                "time_ms": None,
                "memory_kb": memory_limit_kb,
            }
        if compiled.returncode != 0:
            return {
                "status": "compilation_error",
                "stdout": "",
                "stderr": ((compiled.stderr or compiled.stdout) or "Compilation failed.")[:4000],
                "time_ms": None,
                "memory_kb": memory_limit_kb,
            }
        try:
            completed = subprocess.run(
                run_cmd,
                cwd=folder,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
                preexec_fn=_limits(int(timeout) + 1),
            )
        except subprocess.TimeoutExpired:
            return _timed_out(timeout, memory_limit_kb)
        stderr = (completed.stderr or "")[:4000]
        status = "accepted" if completed.returncode == 0 else "runtime_error"
        return {
            "status": status,
            "stdout": (completed.stdout or "")[:MAX_OUTPUT_BYTES],
            "stderr": stderr,
            "time_ms": None,
            "memory_kb": memory_limit_kb,
        }


def _missing_compiler(command: str) -> dict:
    return {
        "status": "compilation_error",
        "stdout": "",
        "stderr": f"{command} is not installed on this computer.",
        "time_ms": None,
        "memory_kb": None,
    }


def _timed_out(timeout: float, memory_limit_kb: int) -> dict:
    return {
        "status": "time_limit",
        "stdout": "",
        "stderr": "Time limit exceeded.",
        "time_ms": int(timeout * 1000),
        "memory_kb": memory_limit_kb,
    }
