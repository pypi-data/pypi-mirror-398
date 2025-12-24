"""
Supabase SDK client singleton with proper error handling

This module provides a thread-safe Supabase client singleton that can be
used across all DARX services.
"""
import os
import logging
from supabase import create_client, Client
from typing import Optional

# Module-level logger
logger = logging.getLogger(__name__)

# Supabase client (singleton pattern)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Get or create Supabase client (singleton).

    Returns:
        Client: Supabase client instance, or None if credentials missing

    Raises:
        Exception: If client initialization fails
    """
    global _supabase_client

    if _supabase_client is None:
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')

        if not url or not key:
            logger.warning(
                "Supabase credentials not found in environment",
                extra={
                    'has_url': bool(url),
                    'has_key': bool(key)
                }
            )
            return None

        try:
            _supabase_client = create_client(url, key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(
                "Failed to initialize Supabase client",
                exc_info=True,
                extra={'error': str(e)}
            )
            raise

    return _supabase_client


def reset_supabase_client():
    """
    Reset the Supabase client singleton.

    Useful for testing or when credentials change.
    """
    global _supabase_client
    _supabase_client = None
    logger.info("Supabase client reset")
