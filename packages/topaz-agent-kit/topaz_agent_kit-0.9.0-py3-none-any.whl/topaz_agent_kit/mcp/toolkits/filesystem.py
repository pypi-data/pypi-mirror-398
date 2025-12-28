"""
Filesystem MCP Toolkit - Basic file and directory operations.

Provides tools for listing directories, moving files, and creating directories.
Intended for agents like File Mover that need controlled access to the local
project filesystem.
"""

import os
import shutil
from typing import Dict, Any, List

from fastmcp import FastMCP

from topaz_agent_kit.utils.logger import Logger


class FilesystemMCPTools:
    """MCP toolkit for basic filesystem operations."""

    def __init__(self, **_: Any) -> None:
        self._logger = Logger("MCP.Filesystem")

    def _validate_path(self, path: str) -> None:
        if not path:
            raise ValueError("path parameter is required")

    def register(self, mcp: FastMCP) -> None:
        """Register filesystem tools with MCP server."""

        @mcp.tool(name="fs_listdir")
        def fs_listdir(path: str) -> Dict[str, Any]:
            """
            List files and directories at the given path.

            Args:
                path: Directory path to list.

            Returns:
                Dict with:
                  - path: the input path
                  - entries: list of {name, is_dir}
            """
            self._logger.input("fs_listdir INPUT: path={}", path)
            self._validate_path(path)

            try:
                entries: List[Dict[str, Any]] = []
                for name in os.listdir(path):
                    full_path = os.path.join(path, name)
                    entries.append(
                        {
                            "name": name,
                            "is_dir": os.path.isdir(full_path),
                        }
                    )
                result = {"path": path, "entries": entries}
                self._logger.output(
                    "fs_listdir OUTPUT: {} entries for path={}", len(entries), path
                )
                return result
            except Exception as exc:
                self._logger.error("fs_listdir failed for {}: {}", path, exc)
                raise

        @mcp.tool(name="fs_makedirs")
        def fs_makedirs(path: str, exist_ok: bool = True) -> Dict[str, Any]:
            """
            Create a directory (and parents) if it does not exist.

            Args:
                path: Directory path to create.
                exist_ok: If True, do not error when directory already exists.

            Returns:
                Dict with:
                  - path: directory path
                  - created: bool indicating if directory was newly created
            """
            self._logger.input("fs_makedirs INPUT: path={}, exist_ok={}", path, exist_ok)
            self._validate_path(path)

            try:
                created = False
                if not os.path.isdir(path):
                    os.makedirs(path, exist_ok=exist_ok)
                    created = True
                result = {"path": path, "created": created}
                self._logger.output(
                    "fs_makedirs OUTPUT: path={} created={}", path, created
                )
                return result
            except Exception as exc:
                self._logger.error("fs_makedirs failed for {}: {}", path, exc)
                raise

        @mcp.tool(name="fs_move_file")
        def fs_move_file(src: str, dest: str, create_dirs: bool = True) -> Dict[str, Any]:
            """
            Move a file from src to dest.

            Args:
                src: Source file path.
                dest: Destination file path (including filename).
                create_dirs: If True, create parent directories for dest if needed.

            Returns:
                Dict with:
                  - src: original path
                  - dest: new path
                  - status: "success" or "failed"
                  - error: error message if any, else empty string
            """
            self._logger.input(
                "fs_move_file INPUT: src={}, dest={}, create_dirs={}",
                src,
                dest,
                create_dirs,
            )
            self._validate_path(src)
            self._validate_path(dest)

            try:
                dest_dir = os.path.dirname(dest) or "."
                if create_dirs and not os.path.isdir(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)

                shutil.move(src, dest)
                result = {
                    "src": src,
                    "dest": dest,
                    "status": "success",
                    "error": "",
                }
                self._logger.output(
                    "fs_move_file OUTPUT: src={} -> dest={} status={}",
                    src,
                    dest,
                    "success",
                )
                return result
            except Exception as exc:
                self._logger.error("fs_move_file failed: {}", exc)
                return {
                    "src": src,
                    "dest": dest,
                    "status": "failed",
                    "error": str(exc),
                }

        @mcp.tool(name="fs_write_file")
        def fs_write_file(path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
            """
            Write content to a file at the given path.

            Args:
                path: File path to write to (including filename).
                content: Content to write to the file.
                create_dirs: If True, create parent directories for path if needed.

            Returns:
                Dict with:
                  - path: file path
                  - status: "success" or "failed"
                  - error: error message if any, else empty string
            """
            self._logger.input(
                "fs_write_file INPUT: path={}, content_length={}, create_dirs={}",
                path,
                len(content),
                create_dirs,
            )
            self._validate_path(path)

            try:
                file_dir = os.path.dirname(path) or "."
                if create_dirs and not os.path.isdir(file_dir):
                    os.makedirs(file_dir, exist_ok=True)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                result = {
                    "path": path,
                    "status": "success",
                    "error": "",
                }
                self._logger.output(
                    "fs_write_file OUTPUT: path={} status={}", path, "success"
                )
                return result
            except Exception as exc:
                self._logger.error("fs_write_file failed for {}: {}", path, exc)
                return {
                    "path": path,
                    "status": "failed",
                    "error": str(exc),
                }


