"""
Idempotency utilities for safe operation retries

This module provides decorators and functions to make operations idempotent using
database-backed idempotency keys. This prevents duplicate resource creation when
operations are retried (e.g., due to Pub/Sub redelivery).
"""
import hashlib
import json
import logging
from typing import TypeVar, Callable, Any, Dict, Optional
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


def generate_idempotency_key(operation: str, params: Dict[str, Any]) -> str:
    """
    Generate a deterministic idempotency key from operation name and parameters.

    Args:
        operation: Name of the operation (e.g., 'create_github_repo')
        params: Parameters that uniquely identify this operation

    Returns:
        SHA256 hash as hex string

    Example:
        >>> generate_idempotency_key('create_github_repo', {'client_slug': 'acme-corp'})
        'a3f7b2c...'
    """
    # Create deterministic JSON string (sorted keys)
    key_data = {
        'operation': operation,
        'params': params
    }
    key_string = json.dumps(key_data, sort_keys=True)

    # Hash to fixed-length key
    return hashlib.sha256(key_string.encode()).hexdigest()


def idempotent(
    key_fn: Callable[..., Dict[str, Any]],
    ttl_hours: int = 24,
    db_client_fn: Optional[Callable[[], Any]] = None
):
    """
    Decorator to make operations idempotent using database-backed keys.

    Args:
        key_fn: Function that extracts idempotency key params from function args
        ttl_hours: How long to keep idempotency keys (hours)
        db_client_fn: Function to get database client (default: get_supabase_client)

    Returns:
        Decorated function

    Example:
        >>> @idempotent(
        ...     key_fn=lambda client_slug, *args, **kwargs: {'operation': 'create_github_repo', 'client_slug': client_slug}
        ... )
        ... def create_github_repo(client_slug: str):
        ...     # This function can be safely retried
        ...     return github_api.create_repo(client_slug)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Get database client
            if db_client_fn:
                db = db_client_fn()
            else:
                # Default to Supabase client
                from darx_core.clients.supabase import get_supabase_client
                db = get_supabase_client()

            if not db:
                logger.warning(
                    "Database client not available - executing without idempotency protection",
                    extra={'function': func.__name__}
                )
                return func(*args, **kwargs)

            # Generate idempotency key
            key_params = key_fn(*args, **kwargs)
            idempotency_key = generate_idempotency_key(func.__name__, key_params)

            # Check if operation already completed
            try:
                existing = db.table('idempotency_keys').select('*').eq('key', idempotency_key).execute()

                if existing.data and len(existing.data) > 0:
                    # Operation already completed
                    cached_result = existing.data[0]['result']
                    logger.info(
                        "Idempotent operation skipped - using cached result",
                        extra={
                            'function': func.__name__,
                            'idempotency_key': idempotency_key,
                            'key_params': key_params
                        }
                    )
                    return cached_result

            except Exception as e:
                logger.error(
                    "Failed to check idempotency key - executing without protection",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'idempotency_key': idempotency_key
                    }
                )
                # Continue without idempotency protection
                return func(*args, **kwargs)

            # Execute operation
            logger.info(
                "Executing idempotent operation",
                extra={
                    'function': func.__name__,
                    'idempotency_key': idempotency_key,
                    'key_params': key_params
                }
            )
            result = func(*args, **kwargs)

            # Store result in database
            try:
                expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
                db.table('idempotency_keys').insert({
                    'key': idempotency_key,
                    'result': result,
                    'created_at': datetime.utcnow().isoformat(),
                    'expires_at': expires_at.isoformat()
                }).execute()

                logger.info(
                    "Idempotency key stored",
                    extra={
                        'function': func.__name__,
                        'idempotency_key': idempotency_key,
                        'ttl_hours': ttl_hours
                    }
                )

            except Exception as e:
                logger.error(
                    "Failed to store idempotency key - result not cached",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'idempotency_key': idempotency_key
                    }
                )
                # Continue anyway - operation succeeded

            return result

        return wrapper
    return decorator


def cleanup_expired_keys(db_client: Any, batch_size: int = 100) -> int:
    """
    Clean up expired idempotency keys from database.

    This should be run periodically (e.g., daily via cron job) to remove old keys.

    Args:
        db_client: Database client (e.g., Supabase client)
        batch_size: Number of keys to delete per batch

    Returns:
        Number of keys deleted

    Example:
        >>> from darx_core.clients.supabase import get_supabase_client
        >>> db = get_supabase_client()
        >>> deleted = cleanup_expired_keys(db)
        >>> print(f"Deleted {deleted} expired keys")
    """
    try:
        # Find expired keys
        now = datetime.utcnow().isoformat()
        expired = db.table('idempotency_keys').select('key').lt('expires_at', now).limit(batch_size).execute()

        if not expired.data or len(expired.data) == 0:
            logger.info("No expired idempotency keys to clean up")
            return 0

        # Delete expired keys
        keys_to_delete = [row['key'] for row in expired.data]
        db.table('idempotency_keys').delete().in_('key', keys_to_delete).execute()

        logger.info(
            "Cleaned up expired idempotency keys",
            extra={'deleted_count': len(keys_to_delete)}
        )
        return len(keys_to_delete)

    except Exception as e:
        logger.error("Failed to clean up expired idempotency keys", exc_info=True)
        return 0


# Example usage
if __name__ == "__main__":
    # Example: Idempotent function
    @idempotent(
        key_fn=lambda client_slug, *args, **kwargs: {
            'operation': 'create_github_repo',
            'client_slug': client_slug
        },
        ttl_hours=24
    )
    def create_github_repo(client_slug: str) -> Dict[str, str]:
        """Create GitHub repository (safe to retry)."""
        print(f"Creating GitHub repo for {client_slug}")
        return {
            'repo_url': f'https://github.com/org/{client_slug}',
            'created_at': datetime.utcnow().isoformat()
        }

    # First call - executes
    result1 = create_github_repo('acme-corp')
    print(f"Result 1: {result1}")

    # Second call - uses cached result (won't create duplicate)
    result2 = create_github_repo('acme-corp')
    print(f"Result 2 (cached): {result2}")

    # Different params - executes again
    result3 = create_github_repo('different-corp')
    print(f"Result 3: {result3}")
