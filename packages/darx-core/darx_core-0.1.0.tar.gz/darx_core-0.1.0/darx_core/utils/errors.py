"""
Base error classes for DARX services

This module provides consistent error handling across all DARX services.
"""
from typing import Optional, Dict, Any


class DARXError(Exception):
    """
    Base exception for all DARX errors.

    All DARX services should raise exceptions that inherit from this base class.
    This allows for consistent error handling and logging across services.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (e.g., 'MISSING_CLIENT_SLUG')
        details: Additional error details as a dictionary
        http_status: HTTP status code for API responses
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 400
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON responses."""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ProvisioningError(DARXError):
    """
    Errors related to client provisioning.

    Examples:
        - Failed to create GitHub repository
        - Failed to create Vercel project
        - Failed to create Builder.io space
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'PROVISIONING_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=500)


class IntegrationError(DARXError):
    """
    Errors related to external API integrations.

    Examples:
        - GitHub API error
        - Vercel API error
        - Builder.io API error
        - Slack API error
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'INTEGRATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=502)


class ValidationError(DARXError):
    """
    Errors related to input validation.

    Examples:
        - Missing required parameter
        - Invalid parameter value
        - Invalid format
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'VALIDATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=400)


class AuthenticationError(DARXError):
    """
    Errors related to authentication.

    Examples:
        - Invalid JWT token
        - Missing authentication header
        - Expired token
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'AUTHENTICATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=401)


class AuthorizationError(DARXError):
    """
    Errors related to authorization.

    Examples:
        - User lacks required permission
        - Resource access denied
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'AUTHORIZATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=403)


class NotFoundError(DARXError):
    """
    Errors when a resource is not found.

    Examples:
        - Client not found
        - Site not found
        - Record not found in database
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'NOT_FOUND',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=404)


class ConflictError(DARXError):
    """
    Errors when an operation conflicts with existing state.

    Examples:
        - Client already exists
        - Duplicate resource
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'CONFLICT',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=409)


class RateLimitError(DARXError):
    """
    Errors when rate limits are exceeded.

    Examples:
        - Too many requests to external API
        - Vercel API rate limit exceeded
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'RATE_LIMIT_EXCEEDED',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=429)


class TimeoutError(DARXError):
    """
    Errors when operations timeout.

    Examples:
        - API request timeout
        - Database query timeout
    """

    def __init__(
        self,
        message: str,
        error_code: str = 'TIMEOUT',
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details, http_status=504)


# Example usage
if __name__ == "__main__":
    # Example 1: Provisioning error
    try:
        raise ProvisioningError(
            message="Failed to create GitHub repository",
            error_code="GITHUB_CREATE_FAILED",
            details={
                'client_slug': 'acme-corp',
                'repository_name': 'acme-corp-site',
                'api_error': 'Repository name already exists'
            }
        )
    except DARXError as e:
        print(f"Error: {e}")
        print(f"Dict: {e.to_dict()}")
        print(f"HTTP Status: {e.http_status}")

    # Example 2: Validation error
    try:
        raise ValidationError(
            message="Missing required parameter",
            error_code="MISSING_CLIENT_SLUG",
            details={'received_params': ['client_name', 'email']}
        )
    except DARXError as e:
        print(f"\nError: {e}")
        print(f"Dict: {e.to_dict()}")
