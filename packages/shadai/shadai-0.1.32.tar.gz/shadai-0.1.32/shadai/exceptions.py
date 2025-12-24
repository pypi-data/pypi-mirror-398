"""
ShadAI Client Exceptions
------------------------
Exception classes matching the backend error structure for proper error handling.

All exceptions inherit from ShadaiError and provide:
- Structured error messages
- Machine-readable error codes
- Contextual information
- Retry flags
"""

from typing import Any, Dict, Optional

# ============================================================================
# Base Exceptions
# ============================================================================


class ShadaiError(Exception):
    """Base exception for all Shadai client errors.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        error_type: Error category (validation_error, resource_error, etc.)
        context: Additional error context
        is_retriable: Whether the operation can be retried
        suggestion: Optional suggestion for user action
    """

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        error_type: str = "unknown_error",
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = False,
        suggestion: Optional[str] = None,
    ) -> None:
        """Initialize Shadai error.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            error_type: Error category
            context: Additional context for debugging
            is_retriable: Whether operation can be retried
            suggestion: Optional suggestion for user
        """
        self.message = message
        self.error_code = error_code
        self.error_type = error_type
        self.context = context or {}
        self.is_retriable = is_retriable
        self.suggestion = suggestion
        super().__init__(message)


# ============================================================================
# Connection & Communication Errors
# ============================================================================


class ConnectionError(ShadaiError):
    """Raised when connection to server fails."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="CONNECTION_ERROR",
            error_type="system_error",
            is_retriable=True,
        )


# ============================================================================
# Authentication Errors
# ============================================================================


class AuthenticationError(ShadaiError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            error_type="authentication_error",
            is_retriable=False,
        )


class InvalidAPIKeyError(AuthenticationError):
    """Raised when API key is invalid."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid API key provided",
        )
        self.error_code = "INVALID_API_KEY"


class MissingAccountSetupError(AuthenticationError):
    """Raised when account setup is missing."""

    def __init__(self) -> None:
        super().__init__(
            message="account_setup_uuid is required but was not provided. "
            "Ensure you are using a valid API key with an associated AccountSetup.",
        )
        self.error_code = "MISSING_ACCOUNT_SETUP"


# ============================================================================
# Resource Errors
# ============================================================================


class ResourceError(ShadaiError):
    """Base class for resource-related errors."""

    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource doesn't exist."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        message = message or f"{resource_type} '{resource_id}' not found"
        context = context or {}
        context.update({"resource_type": resource_type, "resource_id": resource_id})
        super().__init__(
            message=message,
            error_code=f"{resource_type.upper()}_NOT_FOUND",
            error_type="resource_error",
            context=context,
            is_retriable=False,
        )


class SessionNotFoundError(ResourceNotFoundError):
    """Raised when a session doesn't exist."""

    def __init__(self, session_uuid: str, account_uuid: Optional[str] = None) -> None:
        context = {"session_uuid": session_uuid}
        if account_uuid:
            context["account_uuid"] = account_uuid
        super().__init__(
            resource_type="Session",
            resource_id=session_uuid,
            message=f"Session '{session_uuid}' not found for this account",
            context=context,
        )


class FileNotFoundError(ResourceNotFoundError):
    """Raised when a file doesn't exist."""

    def __init__(self, file_uuid: str) -> None:
        super().__init__(
            resource_type="File",
            resource_id=file_uuid,
        )


class AccountNotFoundError(ResourceNotFoundError):
    """Raised when an account doesn't exist."""

    def __init__(self, account_uuid: str) -> None:
        super().__init__(
            resource_type="Account",
            resource_id=account_uuid,
        )


class ResourceAlreadyExistsError(ResourceError):
    """Raised when trying to create a resource that already exists."""

    def __init__(
        self,
        resource_type: str,
        identifier: str,
        message: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        message = message or f"{resource_type} '{identifier}' already exists"
        context = {"resource_type": resource_type, "identifier": identifier}
        super().__init__(
            message=message,
            error_code=f"{resource_type.upper()}_ALREADY_EXISTS",
            error_type="resource_error",
            context=context,
            is_retriable=False,
            suggestion=suggestion,
        )


class SessionAlreadyExistsError(ResourceAlreadyExistsError):
    """Raised when a session with the same name already exists."""

    def __init__(self, session_name: str, account_uuid: Optional[str] = None) -> None:
        context = {"session_name": session_name}
        if account_uuid:
            context["account_uuid"] = account_uuid

        super().__init__(
            resource_type="Session",
            identifier=session_name,
            message=f"A session with the name '{session_name}' already exists. "
            "Please choose a different name.",
            suggestion="Use session_get_or_create to retrieve existing session or create new one",
        )
        self.context.update(context)


# ============================================================================
# Validation Errors
# ============================================================================


class ValidationError(ShadaiError):
    """Base class for validation errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            error_type="validation_error",
            context=context,
            is_retriable=False,
        )


class InvalidFileTypeError(ValidationError):
    """Raised when file type is not supported."""

    def __init__(self, file_extension: str, allowed_extensions: list) -> None:
        super().__init__(
            message=f'File type "{file_extension}" not allowed. '
            f"Allowed types: {', '.join(allowed_extensions)}",
            error_code="INVALID_FILE_TYPE",
            context={
                "file_extension": file_extension,
                "allowed_extensions": allowed_extensions,
            },
        )


class InvalidParameterError(ValidationError):
    """Raised when a parameter value is invalid."""

    def __init__(self, parameter_name: str, parameter_value: Any, reason: str) -> None:
        super().__init__(
            message=f"Invalid value for parameter '{parameter_name}': {reason}",
            error_code="INVALID_PARAMETER",
            context={
                "parameter_name": parameter_name,
                "parameter_value": parameter_value,
                "reason": reason,
            },
        )


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing."""

    def __init__(self, parameter_name: str) -> None:
        super().__init__(
            message=f"Required parameter '{parameter_name}' is missing",
            error_code="MISSING_PARAMETER",
            context={"parameter_name": parameter_name},
        )


class InvalidBase64Error(ValidationError):
    """Raised when base64 string is invalid."""

    def __init__(self, field_name: str) -> None:
        super().__init__(
            message=f"Invalid base64 string in field '{field_name}'",
            error_code="INVALID_BASE64",
            context={"field_name": field_name},
        )


class BatchSizeLimitExceededError(ValidationError):
    """Raised when batch size exceeds limit."""

    def __init__(
        self,
        current_size: int,
        max_size: int,
        size_unit: str = "MB",
    ) -> None:
        super().__init__(
            message=f"Batch size ({current_size} {size_unit}) exceeds maximum "
            f"allowed size ({max_size} {size_unit})",
            error_code="BATCH_SIZE_LIMIT_EXCEEDED",
            context={
                "current_size": current_size,
                "max_size": max_size,
                "size_unit": size_unit,
            },
        )


# ============================================================================
# Authorization & Limit Errors
# ============================================================================


class AuthorizationError(ShadaiError):
    """Base class for authorization errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "AUTHORIZATION_ERROR",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            error_type="authorization_error",
            context=context,
            is_retriable=False,
        )


class PlanLimitExceededError(AuthorizationError):
    """Raised when plan limit is exceeded."""

    def __init__(
        self,
        limit_type: str,
        current_value: int,
        max_allowed: int,
        plan_name: str,
        message: Optional[str] = None,
    ) -> None:
        message = message or (
            f"Plan limit exceeded: {limit_type}. Your '{plan_name}' plan allows "
            f"{max_allowed}, but you have reached {current_value}. "
            "Please upgrade your plan to continue."
        )
        super().__init__(
            message=message,
            error_code="PLAN_LIMIT_EXCEEDED",
            context={
                "limit_type": limit_type,
                "current_value": current_value,
                "max_allowed": max_allowed,
                "plan_name": plan_name,
            },
        )


class KnowledgePointsLimitExceededError(PlanLimitExceededError):
    """Raised when knowledge points limit is exceeded."""

    def __init__(
        self,
        current_value: int,
        max_allowed: int,
        plan_name: str,
        points_needed: int,
    ) -> None:
        super().__init__(
            limit_type="Monthly Knowledge Points",
            current_value=current_value,
            max_allowed=max_allowed,
            plan_name=plan_name,
            message=f"Knowledge points limit exceeded. Your '{plan_name}' plan includes "
            f"{max_allowed:,} knowledge points per month. You have used {current_value} "
            f"({max_allowed - current_value} remaining), but this operation requires "
            f"{points_needed} points. Please upgrade your plan or wait until next "
            "month to continue.",
        )
        self.context["points_needed"] = points_needed


class FileSizeLimitExceededError(PlanLimitExceededError):
    """Raised when file size exceeds plan limit."""

    def __init__(
        self,
        filename: str,
        file_size_bytes: int,
        max_size_bytes: int,
        plan_name: str,
    ) -> None:
        file_size_mb = file_size_bytes / (1024 * 1024)
        max_size_mb = max_size_bytes / (1024 * 1024)

        super().__init__(
            limit_type="File Size",
            current_value=file_size_bytes,
            max_allowed=max_size_bytes,
            plan_name=plan_name,
            message=f"File '{filename}' exceeds plan limit. Your '{plan_name}' plan "
            f"allows files up to {max_size_mb:.2f} MB, but this file is "
            f"{file_size_mb:.2f} MB. Please upgrade your plan to upload larger files.",
        )
        self.context["filename"] = filename


# ============================================================================
# External Service Errors
# ============================================================================


class ExternalServiceError(ShadaiError):
    """Base class for external service errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = True,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            error_type="external_service_error",
            context=context,
            is_retriable=is_retriable,
        )


class LLMProviderError(ExternalServiceError):
    """Raised when LLM provider returns an error."""

    def __init__(
        self,
        provider_name: str,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        message = f"LLM provider '{provider_name}' error"
        if error_message:
            message += f": {error_message}"

        context = {"provider_name": provider_name}
        if status_code:
            context["status_code"] = status_code

        super().__init__(
            message=message,
            error_code="LLM_PROVIDER_ERROR",
            context=context,
            is_retriable=True,
        )


class VectorStoreError(ExternalServiceError):
    """Raised when vector store operation fails."""

    def __init__(self, operation: str, error_details: Optional[str] = None) -> None:
        message = f"Vector store operation '{operation}' failed"
        if error_details:
            message += f": {error_details}"

        super().__init__(
            message=message,
            error_code="VECTOR_STORE_ERROR",
            context={"operation": operation},
        )


class S3StorageError(ExternalServiceError):
    """Raised when S3 storage operation fails."""

    def __init__(self, operation: str, error_details: Optional[str] = None) -> None:
        message = f"S3 storage operation '{operation}' failed"
        if error_details:
            message += f": {error_details}"

        super().__init__(
            message=message,
            error_code="S3_STORAGE_ERROR",
            context={"operation": operation},
        )


# ============================================================================
# Processing Errors
# ============================================================================


class ProcessingError(ShadaiError):
    """Base class for processing errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = False,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            error_type="system_error",
            context=context,
            is_retriable=is_retriable,
        )


class FileParsingError(ProcessingError):
    """Raised when file parsing fails."""

    def __init__(self, file_uuid: str, error_details: str) -> None:
        super().__init__(
            message=f"Failed to parse file '{file_uuid}': {error_details}",
            error_code="FILE_PARSING_ERROR",
            context={"file_uuid": file_uuid, "error_details": error_details},
        )


class ChunkIngestionError(ProcessingError):
    """Raised when chunk ingestion fails."""

    def __init__(self, file_uuid: str, error_details: str) -> None:
        super().__init__(
            message=f"Failed to ingest chunks for file '{file_uuid}': {error_details}",
            error_code="CHUNK_INGESTION_ERROR",
            context={"file_uuid": file_uuid, "error_details": error_details},
        )


# ============================================================================
# System Errors
# ============================================================================


class SystemError(ShadaiError):
    """Base class for system errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "SYSTEM_ERROR",
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = False,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            error_type="system_error",
            context=context,
            is_retriable=is_retriable,
        )


class ConfigurationError(SystemError):
    """Raised when system configuration is invalid or missing."""

    def __init__(self, config_key: str, reason: str) -> None:
        super().__init__(
            message=f"Invalid configuration for '{config_key}': {reason}",
            error_code="CONFIGURATION_ERROR",
            context={"config_key": config_key, "reason": reason},
        )


class DatabaseError(SystemError):
    """Raised when database operation fails."""

    def __init__(self, operation: str, error_details: Optional[str] = None) -> None:
        message = f"Database operation '{operation}' failed"
        if error_details:
            message += f": {error_details}"

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            context={"operation": operation},
            is_retriable=True,
        )


class TimeoutError(SystemError):
    """Raised when operation times out."""

    def __init__(self, operation: str, timeout_seconds: int) -> None:
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout_seconds} seconds",
            error_code="TIMEOUT_ERROR",
            context={"operation": operation, "timeout_seconds": timeout_seconds},
            is_retriable=True,
        )


class ServerError(SystemError):
    """Raised when server returns an unexpected error."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        context = {}
        if status_code:
            context["status_code"] = status_code

        super().__init__(
            message=message,
            error_code="SERVER_ERROR",
            context=context,
            is_retriable=False,
        )


# ============================================================================
# Error Code to Exception Mapping
# ============================================================================


ERROR_CODE_MAP = {
    # Authentication
    "INVALID_API_KEY": InvalidAPIKeyError,
    "MISSING_ACCOUNT_SETUP": MissingAccountSetupError,
    "AUTHENTICATION_ERROR": AuthenticationError,
    # Resources
    "SESSION_NOT_FOUND": SessionNotFoundError,
    "FILE_NOT_FOUND": FileNotFoundError,
    "ACCOUNT_NOT_FOUND": AccountNotFoundError,
    "SESSION_ALREADY_EXISTS": SessionAlreadyExistsError,
    # Validation
    "INVALID_FILE_TYPE": InvalidFileTypeError,
    "INVALID_PARAMETER": InvalidParameterError,
    "MISSING_PARAMETER": MissingParameterError,
    "INVALID_BASE64": InvalidBase64Error,
    "BATCH_SIZE_LIMIT_EXCEEDED": BatchSizeLimitExceededError,
    # Authorization
    "PLAN_LIMIT_EXCEEDED": PlanLimitExceededError,
    # External Services
    "LLM_PROVIDER_ERROR": LLMProviderError,
    "VECTOR_STORE_ERROR": VectorStoreError,
    "S3_STORAGE_ERROR": S3StorageError,
    # Processing
    "FILE_PARSING_ERROR": FileParsingError,
    "CHUNK_INGESTION_ERROR": ChunkIngestionError,
    # System
    "CONFIGURATION_ERROR": ConfigurationError,
    "DATABASE_ERROR": DatabaseError,
    "TIMEOUT_ERROR": TimeoutError,
    "SERVER_ERROR": ServerError,
}


def create_exception_from_error_response(error_data: Dict[str, Any]) -> ShadaiError:
    """
    Create appropriate exception from standardized error response.

    Args:
        error_data: Error data from MCP response (error field)

    Returns:
        Appropriate ShadaiError subclass instance

    Example:
        >>> error_data = {
        ...     "code": "SESSION_NOT_FOUND",
        ...     "message": "Session not found",
        ...     "type": "resource_error",
        ...     "context": {"session_uuid": "123"},
        ...     "is_retriable": False
        ... }
        >>> exc = create_exception_from_error_response(error_data)
        >>> isinstance(exc, SessionNotFoundError)
        True
    """
    error_code = error_data.get("code", "UNKNOWN_ERROR")
    message = error_data.get("message", "An unknown error occurred")
    error_type = error_data.get("type", "unknown_error")
    context = error_data.get("context", {})
    is_retriable = error_data.get("is_retriable", False)
    suggestion = error_data.get("suggestion")

    # Try to create specific exception from code
    exception_class = ERROR_CODE_MAP.get(error_code)

    if exception_class:
        # Try to instantiate with context parameters
        try:
            if error_code == "SESSION_NOT_FOUND":
                return exception_class(
                    session_uuid=context.get("session_uuid", ""),
                    account_uuid=context.get("account_uuid"),
                )
            elif error_code == "FILE_NOT_FOUND":
                return exception_class(file_uuid=context.get("resource_id", ""))
            elif error_code == "ACCOUNT_NOT_FOUND":
                return exception_class(account_uuid=context.get("resource_id", ""))
            elif error_code == "SESSION_ALREADY_EXISTS":
                return exception_class(
                    session_name=context.get("session_name", ""),
                    account_uuid=context.get("account_uuid"),
                )
            elif error_code == "CONFIGURATION_ERROR":
                return exception_class(
                    config_key=context.get("config_key", ""),
                    reason=context.get("reason", message),
                )
            elif error_code == "PLAN_LIMIT_EXCEEDED":
                # Check if it's knowledge points specific
                if "points_needed" in context:
                    return KnowledgePointsLimitExceededError(
                        current_value=context.get("current_value", 0),
                        max_allowed=context.get("max_allowed", 0),
                        plan_name=context.get("plan_name", ""),
                        points_needed=context.get("points_needed", 0),
                    )
                # Check if it's file size specific
                elif "filename" in context:
                    return FileSizeLimitExceededError(
                        filename=context.get("filename", ""),
                        file_size_bytes=context.get("current_value", 0),
                        max_size_bytes=context.get("max_allowed", 0),
                        plan_name=context.get("plan_name", ""),
                    )
                # Generic plan limit
                return exception_class(
                    limit_type=context.get("limit_type", ""),
                    current_value=context.get("current_value", 0),
                    max_allowed=context.get("max_allowed", 0),
                    plan_name=context.get("plan_name", ""),
                )
            # For other exceptions that don't need special handling
            else:
                return exception_class()
        except (TypeError, KeyError):
            # Fall through to generic exception
            pass

    # Generic exception if we can't create specific one
    return ShadaiError(
        message=message,
        error_code=error_code,
        error_type=error_type,
        context=context,
        is_retriable=is_retriable,
        suggestion=suggestion,
    )
