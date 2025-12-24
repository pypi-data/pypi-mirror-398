"""
Error Handler
-------------
Custom exception hook for clean, user-friendly error messages.
"""

import sys
from typing import Type

from .exceptions import ShadaiError


def _format_shadai_error(exc: ShadaiError) -> str:
    """Format ShadaiError into clean, user-friendly message.

    Args:
        exc: ShadaiError instance

    Returns:
        Formatted error message
    """
    lines = []

    # Error header with code
    if hasattr(exc, "error_code") and exc.error_code:
        lines.append(f"\n❌ Error [{exc.error_code}]:")
    else:
        lines.append("\n❌ Error:")

    # Main error message
    if hasattr(exc, "message"):
        lines.append(f"   {exc.message}")
    else:
        lines.append(f"   {str(exc)}")

    # Suggestion if available
    if hasattr(exc, "suggestion") and exc.suggestion:
        lines.append("\n💡 Suggestion:")
        lines.append(f"   {exc.suggestion}")

    # Context if available and useful
    if hasattr(exc, "context") and exc.context:
        # Only show context for certain error types
        show_context = False
        if hasattr(exc, "error_type") and exc.error_type in [
            "validation_error",
            "resource_error",
        ]:
            show_context = True

        if show_context and exc.context:
            lines.append("\n📋 Details:")
            for key, value in exc.context.items():
                if key not in ["config_key", "reason"]:  # These are already in message
                    lines.append(f"   {key}: {value}")

    lines.append("")  # Empty line at the end
    return "\n".join(lines)


def shadai_excepthook(
    exc_type: Type[BaseException], exc_value: BaseException, exc_traceback
) -> None:
    """Custom exception hook for ShadaiError exceptions.

    Displays clean, user-friendly error messages without verbose tracebacks.
    Falls back to default behavior for non-ShadaiError exceptions.

    Args:
        exc_type: Exception class
        exc_value: Exception instance
        exc_traceback: Traceback object
    """
    # Handle ShadaiError with clean formatting
    if isinstance(exc_value, ShadaiError):
        error_message = _format_shadai_error(exc_value)
        print(error_message, file=sys.stderr)
        sys.exit(1)

    # For other exceptions, use default handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def install_exception_handler() -> None:
    """Install custom exception handler for clean error messages."""
    sys.excepthook = shadai_excepthook
