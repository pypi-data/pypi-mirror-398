"""
Utility decorators for ublkit.

Provides decorators for logging function execution and memory management.
"""

from __future__ import annotations

import datetime
import gc
from functools import wraps
from typing import Any, Callable, TypeVar

from py_logex import logger

F = TypeVar("F", bound=Callable[..., Any])


def log_execution(func: F) -> F:
    """
    Decorator to log function entry, exit, and execution time.

    Logs:
    - Function entry with full qualified name
    - Execution time on successful completion
    - Error details if function raises an exception

    Example:
        @log_execution
        def process_file(path: str) -> dict:
            return {"data": "..."}
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        class_name = args[0].__class__.__name__ if args else ""
        full_name = f"{class_name}.{func_name}" if class_name else func_name

        logger.debug(f"Entering: {full_name}")
        start_time = datetime.datetime.now()

        try:
            result = func(*args, **kwargs)
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            logger.debug(f"Exiting: {full_name} (took {elapsed:.4f}s)")
            return result
        except Exception as e:
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            logger.error(
                f"Failed: {full_name} (took {elapsed:.4f}s) - {type(e).__name__}: {e}"
            )
            raise

    return wrapper  # type: ignore


def memory_cleanup(func: F) -> F:
    """
    Decorator to perform garbage collection after function execution.

    Ensures memory is freed after function completes, useful for
    processing large files or batch operations.

    Example:
        @memory_cleanup
        def process_large_batch(files: list) -> dict:
            # Process many files
            return {"results": "..."}
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            gc.collect()

    return wrapper  # type: ignore
