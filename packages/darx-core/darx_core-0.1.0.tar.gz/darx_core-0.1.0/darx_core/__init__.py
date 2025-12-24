"""
DARX Core - Shared utilities for DARX microservices

This package provides common patterns and utilities used across all DARX services.
"""

__version__ = '0.1.0'
__author__ = 'Digital ArchiteX'

# Export commonly used functions
from darx_core.clients.supabase import get_supabase_client
from darx_core.clients.slack import get_slack_client, post_to_slack, upload_file_to_slack
from darx_core.clients.storage import (
    get_storage_client,
    upload_to_gcs,
    download_from_gcs,
    list_blobs,
    delete_blob
)
from darx_core.utils.logging import setup_logging, get_logger
from darx_core.utils.retry import retry_with_backoff, retry_async_with_backoff
from darx_core.utils.errors import (
    DARXError,
    ProvisioningError,
    IntegrationError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    TimeoutError
)
from darx_core.utils.idempotency import idempotent, generate_idempotency_key

__all__ = [
    # Version
    '__version__',
    # Clients
    'get_supabase_client',
    'get_slack_client',
    'post_to_slack',
    'upload_file_to_slack',
    'get_storage_client',
    'upload_to_gcs',
    'download_from_gcs',
    'list_blobs',
    'delete_blob',
    # Logging
    'setup_logging',
    'get_logger',
    # Retry
    'retry_with_backoff',
    'retry_async_with_backoff',
    # Errors
    'DARXError',
    'ProvisioningError',
    'IntegrationError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'RateLimitError',
    'TimeoutError',
    # Idempotency
    'idempotent',
    'generate_idempotency_key',
]
