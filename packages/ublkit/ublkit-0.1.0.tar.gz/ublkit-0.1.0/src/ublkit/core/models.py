"""
Core data models for ublkit.

This module defines all dataclasses used throughout the package for
representing conversion results, processing summaries, and configuration.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ConversionResult:
    """
    Result of converting a single XML file.

    Used for single file processing - all data returned in memory.
    """

    success: bool
    source_file: str
    output_format: str
    processing_time_seconds: float
    error_message: str = ""
    file_size_bytes: int = 0
    ubl_document_type: str = ""
    content: Optional[Union[Dict[str, Any], List[Dict[str, str]]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "error_message": self.error_message,
            "processing_time_seconds": self.processing_time_seconds,
            "source_file": self.source_file,
            "file_size_bytes": self.file_size_bytes,
            "ubl_document_type": self.ubl_document_type,
            "output_format": self.output_format,
            "content": self.content,
        }


@dataclass
class ProcessingResult:
    """
    Result of processing a single XML file in batch mode.

    Used for batch processing - tracks file processing status.
    """

    file_path: Path
    success: bool
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0
    file_size_bytes: int = 0
    ubl_document_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": str(self.file_path),
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
            "error_message": self.error_message,
            "processing_time_seconds": self.processing_time_seconds,
            "file_size_bytes": self.file_size_bytes,
            "ubl_document_type": self.ubl_document_type,
        }


@dataclass
class ProcessingSummary:
    """
    Summary of batch processing results.

    Aggregates results from all files processed in batch mode.
    """

    total_files: int = 0
    successful: int = 0
    failed: int = 0
    results: List[ProcessingResult] = field(default_factory=list)
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    output_format: str = ""

    def add_result(self, result: ProcessingResult) -> None:
        """Add a processing result to the summary."""
        self.results.append(result)
        self.total_files += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary for JSON serialization."""
        return {
            "summary": {
                "total_files": self.total_files,
                "successful": self.successful,
                "failed": self.failed,
                "output_format": self.output_format,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "total_duration_seconds": (
                    (self.end_time - self.start_time).total_seconds()
                    if self.start_time and self.end_time
                    else None
                ),
            },
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class KeyValuePair:
    """
    Represents a single key-value pair from flattened JSON/XML.

    Used in CSV conversion to store flattened structure.
    """

    key: str
    value: str
    source_file: str
