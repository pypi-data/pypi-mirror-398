import contextlib
import io
import json
import math
import multiprocessing
import os
import runpy
import textwrap
import traceback
import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from topaz_agent_kit.utils.logger import Logger
from fastmcp import FastMCP

logger = Logger("MCP.Python")


@dataclass
class _PythonExecRequest:
    code: str
    input: Dict[str, Any]
    time_limit_s: float
    mode: str = "exec"  # exec | run_file | run_module
    target: str = ""  # file path or module name when mode != exec


def _parse_csv_env(name: str) -> list[str]:
    raw = os.environ.get(name, "") or ""
    items = [x.strip() for x in raw.split(",")]
    return [x for x in items if x]


def _validate_code_basic(code: str, max_chars: int = 20000) -> str:
    """
    Basic validation:
    - size cap
    - syntax check
    - denylisted tokens (best-effort; not a security boundary)
    """
    if not isinstance(code, str) or not code.strip():
        return "ValueError: code must be a non-empty string"
    if len(code) > max_chars:
        return f"ValueError: code too large ({len(code)} chars). Max allowed: {max_chars}"
    try:
        compile(code, "<python_execute>", "exec")
    except SyntaxError as e:
        return f"SyntaxError: {e}"

    # NOTE: This is best-effort validation for UX. Security boundary is the sandboxed builtins + allowlisted importer.
    deny_tokens = [
        "import os",
        "import sys",
        "import subprocess",
        "import socket",
        "import pathlib",
        "import shutil",
        "import pickle",
        "import marshal",
        "import importlib",
        "open(",
        "__import__(",
        "eval(",
        # Prevent nested exec-in-exec patterns (outer exec is controlled by us)
        "exec(",
    ]
    lowered = code.lower()
    for tok in deny_tokens:
        if tok in lowered:
            return f"ValueError: disallowed token detected: {tok}"
    return ""


def _safe_worker(req: _PythonExecRequest, out_q: multiprocessing.Queue) -> None:
    """
    Run user code in a child process with a restricted environment.

    Contract:
    - Input is available as `input` (dict)
    - User code should set `output` (JSON-serializable) to return structured results
    - Print statements are captured and returned as stdout
    """
    started_at = time.time()
    stdout_buf = io.StringIO()

    allowed_imports = {"math", "statistics", "json", "datetime", "time"}

    def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
        # Block relative imports and any dotted/module traversal patterns by default.
        if level != 0:
            raise ImportError("relative imports are not allowed")
        if not isinstance(name, str):
            raise ImportError("invalid import")
        top = name.split(".", 1)[0]
        if top not in allowed_imports:
            raise ImportError(f"import of '{top}' is not allowed")
        if top == "math":
            return math
        if top == "statistics":
            return statistics
        if top == "json":
            return json
        if top == "datetime":
            import datetime as _datetime  # stdlib

            return _datetime
        if top == "time":
            import time as _time  # stdlib

            return _time
        raise ImportError("import not allowed")

    # Minimal, deterministic safe builtins.
    safe_builtins = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "max": max,
        "min": min,
        "range": range,
        "round": round,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "print": print,
        "__import__": _safe_import,
    }

    # Ensure `input` is always a dict for user code.
    # Some callers (LLM-authored tool calls) may accidentally pass a list; we normalize it
    # so that `input.get(...)` works reliably.
    input_obj: Any = req.input
    if not isinstance(input_obj, dict):
        input_obj = {"_raw": input_obj}

    # Restricted global namespace: no os/sys/subprocess/network/fs.
    globals_dict: Dict[str, Any] = {
        "__builtins__": safe_builtins,
        # Whitelisted deterministic stdlib helpers
        "math": math,
        "statistics": statistics,
        "json": json,
        # Inputs/outputs
        "input": input_obj,
        "output": None,
    }

    try:
        with contextlib.redirect_stdout(stdout_buf):
            if req.mode == "exec":
                # Use the same namespace for globals+locals so that definitions (functions/vars)
                # are visible throughout the execution (prevents NameError for locally-defined helpers).
                exec(req.code, globals_dict, globals_dict)  # noqa: S102 (intentional controlled exec)
            elif req.mode == "run_file":
                # Run an allowlisted file path as __main__.
                # Note: executed code still runs under the restricted globals/builtins above.
                runpy.run_path(req.target, run_name="__main__", init_globals=globals_dict)
            elif req.mode == "run_module":
                # Run an allowlisted module as __main__.
                # Note: executed code still runs under the restricted globals/builtins above.
                runpy.run_module(req.target, run_name="__main__", init_globals=globals_dict)
            else:
                raise ValueError(f"Unknown execution mode: {req.mode}")
        elapsed = time.time() - started_at
        out_q.put(
            {
                "ok": True,
                "output": globals_dict.get("output", None),
                "stdout": stdout_buf.getvalue(),
                "elapsed_s": elapsed,
                "error": "",
            }
        )
    except Exception as e:
        elapsed = time.time() - started_at
        out_q.put(
            {
                "ok": False,
                "output": None,
                "stdout": stdout_buf.getvalue(),
                "elapsed_s": elapsed,
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }
        )


class PythonMCPTools:
    """
    Python deterministic execution toolkit.

    Tools:
    - python_execute: Run bounded python code with a restricted environment.

    Note: We intentionally keep the surface area small; all file/network access is disallowed
    by construction (no such modules are available in the sandboxed exec globals).
    """

    def __init__(self) -> None:
        self.logger = logger

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool(
            name="python_validate",
            description=(
                "Validate Python code without executing it. Performs syntax check, size limits, "
                "and denylisted token checks. Returns ok/error."
            ),
        )
        async def python_validate(
            code: str,
            max_chars: int = 20000,
        ) -> Dict[str, Any]:
            err = _validate_code_basic(code, max_chars=max_chars)
            return {"ok": err == "", "error": err}

        @mcp.tool(
            name="python_execute",
            description=(
                "Execute bounded Python code for deterministic computation. "
                "Input is provided as JSON and available as `input` in code. "
                "Set `output` (JSON-serializable) to return structured results. "
                "Stdout is captured. File/network access is not available."
            ),
        )
        async def python_execute(
            code: str,
            input: Optional[Dict[str, Any]] = None,
            time_limit_s: float = 10.0,
        ) -> Dict[str, Any]:
            """
            Execute python in a child process with a strict time limit.

            Args:
                code: Python source code to execute.
                input: JSON object available in code as `input` (dict).
                time_limit_s: Maximum wall time in seconds before termination.

            Returns:
                Dict with keys: ok, output, stdout, elapsed_s, error
            """
            # Normalize indentation to avoid common LLM formatting issues (e.g. top-level unexpected indent).
            # This keeps execution deterministic and prevents minor formatting from failing the pipeline.
            original_code = code
            code = textwrap.dedent(code or "").lstrip("\n")

            basic_err = _validate_code_basic(code)
            if basic_err:
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": 0.0,
                    "error": basic_err,
                }
            # Clamp rather than error: we want deterministic pipeline behavior even if an agent
            # accidentally requests an unsafe timeout (e.g., 10s).
            if time_limit_s is None:
                time_limit_s = 60.0
            try:
                time_limit_s = float(time_limit_s)
            except Exception:
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": 0.0, "error": "ValueError: time_limit_s must be a number"}

            if time_limit_s <= 0:
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": 0.0, "error": "ValueError: time_limit_s must be > 0"}
            if time_limit_s > 60:
                time_limit_s = 60.0
            if time_limit_s < 30:
                time_limit_s = 60.0

            payload = _PythonExecRequest(
                code=code,
                input=input or {},
                time_limit_s=time_limit_s,
                mode="exec",
                target="",
            )

            out_q: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
            proc = multiprocessing.Process(target=_safe_worker, args=(payload, out_q))
            start = time.time()

            self.logger.input(
                "python_execute INPUT: time_limit_s={}, code_len={}, input_keys={}",
                time_limit_s,
                len(code),
                list((input or {}).keys()),
            )
            # NOTE: This can be very verbose, but it is intentionally always-on for debugging.
            if isinstance(original_code, str) and original_code != code:
                self.logger.warning(
                    "python_execute: code was normalized (dedent/lstrip). original_len={}, normalized_len={}",
                    len(original_code),
                    len(code),
                )
            self.logger.input("python_execute CODE BEGIN\n{}\npython_execute CODE END", code)

            proc.start()
            proc.join(timeout=payload.time_limit_s)

            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)
                elapsed = time.time() - start
                self.logger.error("python_execute TIMEOUT after {}s", round(elapsed, 3))
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": elapsed,
                    "error": f"TimeoutError: python_execute exceeded {payload.time_limit_s}s",
                }

            elapsed = time.time() - start
            try:
                result = out_q.get_nowait()
            except Exception:
                self.logger.error("python_execute failed: no result returned from worker")
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": elapsed,
                    "error": "RuntimeError: python_execute failed: no result returned",
                }

            # Ensure a stable shape
            result.setdefault("elapsed_s", elapsed)
            result.setdefault("stdout", "")
            result.setdefault("output", None)
            result.setdefault("ok", False)
            result.setdefault("error", "")

            if result["ok"]:
                self.logger.success(
                    "python_execute OK in {}s (stdout_len={})",
                    round(result["elapsed_s"], 3),
                    len(result.get("stdout", "")),
                )
            else:
                self.logger.error(
                    "python_execute ERROR in {}s: {}",
                    round(result["elapsed_s"], 3),
                    result.get("error", ""),
                )

            return result

        @mcp.tool(
            name="python_run_file",
            description=(
                "Run an allowlisted Python file relative to the project root (MCP server cwd). "
                "Uses the same restricted execution environment as python_execute. "
                "Enable allowlist via TOPAZ_PYTHON_ALLOWED_FILES (comma-separated relative paths)."
            ),
        )
        async def python_run_file(
            file_path: str,
            input: Optional[Dict[str, Any]] = None,
            time_limit_s: float = 10.0,
        ) -> Dict[str, Any]:
            allowed = _parse_csv_env("TOPAZ_PYTHON_ALLOWED_FILES")
            if not allowed:
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": 0.0,
                    "error": "PermissionError: python_run_file is disabled. Set TOPAZ_PYTHON_ALLOWED_FILES to enable allowlisted files.",
                }

            if not isinstance(file_path, str) or not file_path.strip():
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": 0.0, "error": "ValueError: file_path must be a non-empty string"}

            # Resolve relative to current working directory (project root for serve mcp -p).
            cwd = os.path.abspath(os.getcwd())
            candidate_rel = file_path.strip().lstrip("/\\")
            candidate_abs = os.path.abspath(os.path.join(cwd, candidate_rel))

            # Must be in allowlist and within project root.
            if candidate_rel not in allowed:
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": 0.0,
                    "error": f"PermissionError: file not allowlisted: {candidate_rel}",
                }
            if not candidate_abs.startswith(cwd + os.sep):
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": 0.0,
                    "error": "PermissionError: file_path must be within project root",
                }
            if not os.path.isfile(candidate_abs):
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": 0.0,
                    "error": f"FileNotFoundError: file does not exist: {candidate_rel}",
                }
            if time_limit_s <= 0 or time_limit_s > 60:
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": 0.0, "error": "ValueError: time_limit_s must be between 0 and 60 seconds"}

            payload = _PythonExecRequest(
                code="",
                input=input or {},
                time_limit_s=float(time_limit_s),
                mode="run_file",
                target=candidate_abs,
            )
            out_q: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
            proc = multiprocessing.Process(target=_safe_worker, args=(payload, out_q))
            start = time.time()

            self.logger.input(
                "python_run_file INPUT: time_limit_s={}, file={}, input_keys={}",
                time_limit_s,
                candidate_rel,
                list((input or {}).keys()),
            )

            proc.start()
            proc.join(timeout=payload.time_limit_s)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)
                elapsed = time.time() - start
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": elapsed, "error": f"TimeoutError: python_run_file exceeded {payload.time_limit_s}s"}

            elapsed = time.time() - start
            try:
                result = out_q.get_nowait()
            except Exception:
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": elapsed, "error": "RuntimeError: python_run_file failed: no result returned"}
            result.setdefault("elapsed_s", elapsed)
            return result

        @mcp.tool(
            name="python_run_module",
            description=(
                "Run an allowlisted Python module as __main__. Uses the same restricted execution environment "
                "as python_execute. Enable allowlist via TOPAZ_PYTHON_ALLOWED_MODULES (comma-separated module names)."
            ),
        )
        async def python_run_module(
            module: str,
            input: Optional[Dict[str, Any]] = None,
            time_limit_s: float = 10.0,
        ) -> Dict[str, Any]:
            allowed = _parse_csv_env("TOPAZ_PYTHON_ALLOWED_MODULES")
            if not allowed:
                return {
                    "ok": False,
                    "output": None,
                    "stdout": "",
                    "elapsed_s": 0.0,
                    "error": "PermissionError: python_run_module is disabled. Set TOPAZ_PYTHON_ALLOWED_MODULES to enable allowlisted modules.",
                }

            if not isinstance(module, str) or not module.strip():
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": 0.0, "error": "ValueError: module must be a non-empty string"}
            module = module.strip()
            if module not in allowed:
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": 0.0, "error": f"PermissionError: module not allowlisted: {module}"}
            if time_limit_s <= 0 or time_limit_s > 60:
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": 0.0, "error": "ValueError: time_limit_s must be between 0 and 60 seconds"}

            payload = _PythonExecRequest(
                code="",
                input=input or {},
                time_limit_s=float(time_limit_s),
                mode="run_module",
                target=module,
            )
            out_q: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
            proc = multiprocessing.Process(target=_safe_worker, args=(payload, out_q))
            start = time.time()

            self.logger.input(
                "python_run_module INPUT: time_limit_s={}, module={}, input_keys={}",
                time_limit_s,
                module,
                list((input or {}).keys()),
            )

            proc.start()
            proc.join(timeout=payload.time_limit_s)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)
                elapsed = time.time() - start
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": elapsed, "error": f"TimeoutError: python_run_module exceeded {payload.time_limit_s}s"}

            elapsed = time.time() - start
            try:
                result = out_q.get_nowait()
            except Exception:
                return {"ok": False, "output": None, "stdout": "", "elapsed_s": elapsed, "error": "RuntimeError: python_run_module failed: no result returned"}
            result.setdefault("elapsed_s", elapsed)
            return result


