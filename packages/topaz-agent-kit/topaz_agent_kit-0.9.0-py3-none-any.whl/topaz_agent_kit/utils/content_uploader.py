"""
Content uploader utilities
Only responsible for acknowledging/validating files (CLI) and emitting
STATE_SNAPSHOT events for the file_uploader step. No ingestion here.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from topaz_agent_kit.core.exceptions import FileError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.file_type_detector import FileTypeDetector


class ContentUploader:
    """Uploads (acknowledges) files and emits STATE_SNAPSHOT for CLI uploads."""

    def __init__(self, emitter: Optional[Any] = None) -> None:
        self.logger = Logger("ContentUploader")
        self.emitter = emitter

    def _validate_file(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        is_supported, error = FileTypeDetector.validate_file_support(file_path)
        if not is_supported:
            raise FileError(error)

    def upload_only(
        self,
        file_paths: List[str],
        original_filenames: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate/acknowledge files and emit a single STATE_SNAPSHOT per file.

        Returns:
            { success, summary, results: [ {filename, file_path, file_size, status} ] }
        """
        results: List[Dict[str, Any]] = []
        for i, file_path in enumerate(file_paths):
            try:
                self._validate_file(file_path)
                file_size = os.path.getsize(file_path)
                filename = (
                    original_filenames[i]
                    if original_filenames and i < len(original_filenames)
                    else os.path.basename(file_path)
                )

                if self.emitter and hasattr(self.emitter, "step_output"):
                    self.emitter.step_output(
                        node_id="content_uploader",
                        result={
                            "filename": filename,
                            "status": "uploaded",
                            "file_size": file_size,
                            "content_type": Path(file_path).suffix.lower().lstrip(".") or "unknown",
                        },
                        status="completed",
                    )

                results.append(
                    {
                        "file_path": file_path,
                        "filename": filename,
                        "file_size": file_size,
                        "status": "uploaded",
                    }
                )
            except Exception as e:
                self.logger.error("Upload failed for {}: {}", file_path, e)
                results.append(
                    {
                        "file_path": file_path,
                        "filename": os.path.basename(file_path),
                        "file_size": 0,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        failed = [r for r in results if r.get("status") == "failed"]
        summary = f"{len(results) - len(failed)} uploaded, {len(failed)} failed"
        return {"success": len(failed) == 0, "summary": summary, "results": results}


