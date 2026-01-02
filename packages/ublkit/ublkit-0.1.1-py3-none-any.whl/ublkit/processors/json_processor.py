"""
JSON Processing Module for ublkit.

Handles JSON output generation and writing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from py_logex import logger

from ublkit.utils.decorators import log_execution


class JSONProcessor:
    """Handles JSON output operations."""

    def __init__(
        self,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        """
        Initialize JSONProcessor.

        Args:
            indent: JSON indentation level
            ensure_ascii: Whether to escape non-ASCII characters
        """
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    @log_execution
    def write_file(
        self,
        data: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        Write dictionary to JSON file.

        Args:
            data: Dictionary to write
            output_path: Path for output JSON file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=self._indent,
                ensure_ascii=self._ensure_ascii,
            )

        logger.debug(f"Wrote JSON to: {output_path}")

    def to_json_string(
        self,
        data: Dict[str, Any],
    ) -> str:
        """
        Convert dictionary to JSON string.

        Args:
            data: Dictionary to convert

        Returns:
            JSON string
        """
        return json.dumps(
            data,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii,
        )
