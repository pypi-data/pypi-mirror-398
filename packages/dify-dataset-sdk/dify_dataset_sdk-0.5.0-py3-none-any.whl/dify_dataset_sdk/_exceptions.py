"""Exception classes for Dify Dataset SDK."""

from typing import Optional


class DifyError(Exception):
    """Base exception class for Dify SDK.

    All Dify SDK exceptions inherit from this base class to provide
    a common interface for error handling.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
        """
        super().__init__(message)
        self.message = message


class DifyAPIError(DifyError):
    """API error from Dify service.

    Raised when the Dify API returns an error response. Contains both
    HTTP status code and Dify-specific error code when available.

    Attributes:
        status_code: HTTP status code from the response
        error_code: Dify-specific error code
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize the API error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Dify-specific error code
        """
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code

    def __str__(self) -> str:
        """Return a formatted error string."""
        if self.status_code and self.error_code:
            return f"{self.message} (HTTP {self.status_code}, Error: {self.error_code})"
        elif self.status_code:
            return f"{self.message} (HTTP {self.status_code})"
        elif self.error_code:
            return f"{self.message} (Error: {self.error_code})"
        else:
            return self.message


class DifyAuthenticationError(DifyAPIError):
    """Authentication error.

    Raised when API key is invalid or authentication fails.
    Usually corresponds to HTTP 401 status code.
    """

    pass


class DifyValidationError(DifyAPIError):
    """Validation error.

    Raised when request parameters are invalid or malformed.
    Usually corresponds to HTTP 400 or 422 status codes.
    """

    pass


class DifyNotFoundError(DifyAPIError):
    """Resource not found error.

    Raised when the requested resource (dataset, document, etc.)
    does not exist. Corresponds to HTTP 404 status code.
    """

    pass


class DifyConflictError(DifyAPIError):
    """Conflict error.

    Raised when there's a conflict with the current resource state,
    such as duplicate names. Corresponds to HTTP 409 status code.
    """

    pass


class DifyServerError(DifyAPIError):
    """Server error.

    Raised when the Dify server encounters an internal error.
    Corresponds to HTTP 5xx status codes.
    """

    pass


class DifyConnectionError(DifyError):
    """Connection error.

    Raised when unable to establish connection to the Dify API,
    including network timeouts and DNS resolution failures.
    """

    pass


class DifyTimeoutError(DifyError):
    """Timeout error.

    Raised when a request exceeds the configured timeout duration.
    """

    pass


# Error code mappings
ERROR_CODE_MAPPING = {
    "no_file_uploaded": "Please upload your file",
    "too_many_files": "Only one file upload is allowed",
    "file_too_large": "File size exceeds limit",
    "unsupported_file_type": "Unsupported file type",
    "high_quality_dataset_only": 'Current operation only supports "high quality" datasets',
    "dataset_not_initialized": "Dataset is still initializing or indexing. Please wait",
    "archived_document_immutable": "Archived documents cannot be edited",
    "dataset_name_duplicate": "Dataset name already exists, please modify your dataset name",
    "invalid_action": "Invalid operation",
    "document_already_finished": "Document has been processed. Please refresh the page or view document details",
    "document_indexing": "Document is being processed and cannot be edited",
    "invalid_metadata": "Metadata content is incorrect. Please check and validate",
}
